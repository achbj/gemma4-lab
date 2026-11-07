"""Design-set strength selection for weight-space study v3 (pre-registered rule).

Dense Transformers simulation of the frozen v2 construction at all positions, greedy 48-token
continuations, on the v2 *design* cases only. Evaluation-case prompts are never loaded.
Rule: smallest alpha in the frozen grid with greedy first tool call `read_file` in >= 11 of the
12 design prefix cases and an unchanged first tool-call name in all 12 non-target design cases.
"""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL_PATH = "/cache/models/e4b-v2"
CAPTURE = "/cache/wsp-v2/capture-v1.safetensors"
GRID = [2.0, 3.0, 4.0, 6.0, 8.0]
MIN_PREFIX_READS = 11
RIDGE = 1e-3
NEW_TOKENS = 48
image = None
INPUTS = {}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.modal_runtime import build_runtime_image

    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")
    cases = json.loads((ROOT / "configs/wsp-v2-cases.json").read_text())["cases"]
    INPUTS = {
        "base_prompt": (ROOT / "submissions/wsp-base-v1/prompts/system.md").read_text(),
        "context": (ROOT / "submissions/behavior-diagnostic-v1/prompts/context.md").read_text(),
        "design_cases": [c for c in cases if c["role"] == "design"],
    }

app = modal.App("gemma4-wsp-v3-select")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    gpu="A10G",
    cpu=2,
    memory=16 * 1024,
    timeout=900,
    startup_timeout=600,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def select(inputs: dict) -> str:
    import traceback

    try:
        return json.dumps(_select(inputs))
    except Exception:
        return json.dumps({"failed": traceback.format_exc()[-3000:]})


def _select(inputs: dict) -> dict:
    import re
    import time

    import torch
    import transformers
    from safetensors import safe_open

    from gemma4_lab.behavior_diagnostics import TOOL_DEFINITIONS, SeededSession

    started = time.monotonic()
    model = transformers.AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, dtype=torch.bfloat16, device_map="cuda"
    ).eval()
    tok = transformers.AutoTokenizer.from_pretrained(MODEL_PATH)
    with safe_open(CAPTURE, framework="pt") as handle:
        layer = int(handle.metadata()["layer"])
        k_star = handle.get_tensor(f"layer{layer}.k_star").double()
        d = handle.get_tensor(f"layer{layer}.d").double()
        c = handle.get_tensor("covariance").double()
    ridge = RIDGE * float(c.diag().mean())
    v = torch.linalg.solve(c + ridge * torch.eye(c.shape[0], dtype=torch.float64), k_star)
    a_row = (v / float(k_star @ v)).float().cuda()
    d_cuda = d.float().cuda()
    module = dict(model.named_modules())[f"model.language_model.layers.{layer}.self_attn.o_proj"]
    state = {"alpha": 0.0}

    def hook(_m, args, output):
        if state["alpha"] == 0.0:
            return output
        shift = (args[0].float() @ a_row).unsqueeze(-1) * d_cuda * state["alpha"]
        return output + shift.to(output.dtype)

    module.register_forward_hook(hook)

    def ids_for(case):
        session = SeededSession(case)
        messages = [{"role": "system", "content": inputs["base_prompt"]}]
        for message in session.seed_messages(inputs["context"], 6):
            message = json.loads(json.dumps(message))
            for call in message.get("tool_calls", []):
                call["function"]["arguments"] = json.loads(call["function"]["arguments"])
            messages.append(message)
        text = tok.apply_chat_template(
            messages, tools=TOOL_DEFINITIONS, add_generation_prompt=True, tokenize=False
        )
        return tok(text, return_tensors="pt", add_special_tokens=False)["input_ids"].cuda()

    def first_call(ids):
        with torch.no_grad():
            out = model.generate(input_ids=ids, max_new_tokens=NEW_TOKENS, do_sample=False)
        text = tok.decode(out[0, ids.shape[1] :])
        match = re.search(r"call:([A-Za-z_]+)\{", text)
        return (match.group(1) if match else None), text[:160]

    prefix = [c for c in inputs["design_cases"] if c["family"] == "prefix_corruption"]
    other = [c for c in inputs["design_cases"] if c["family"] != "prefix_corruption"]
    cache = {c["id"]: ids_for(c) for c in prefix + other}
    results = {}
    for alpha in [0.0, *GRID]:
        state["alpha"] = alpha
        record = {"prefix": {}, "nontarget": {}}
        for case in prefix:
            record["prefix"][case["id"]] = first_call(cache[case["id"]])
        for case in other:
            record["nontarget"][case["id"]] = first_call(cache[case["id"]])
        results[str(alpha)] = record
    state["alpha"] = 0.0
    baseline = {k: v[0] for k, v in results["0.0"]["nontarget"].items()}
    summary = {}
    for alpha in GRID:
        record = results[str(alpha)]
        reads = sum(v[0] == "read_file" for v in record["prefix"].values())
        unchanged = sum(v[0] == baseline[k] for k, v in record["nontarget"].items())
        summary[str(alpha)] = {
            "prefix_read_file": reads,
            "nontarget_unchanged": unchanged,
            "qualifies": reads >= MIN_PREFIX_READS and unchanged == len(other),
        }
    chosen = next((a for a in GRID if summary[str(a)]["qualifies"]), None)
    return {
        "layer": layer,
        "grid": GRID,
        "rule": f"smallest alpha with >= {MIN_PREFIX_READS}/12 read_file and 12/12 unchanged",
        "baseline_prefix_read_file": sum(
            v[0] == "read_file" for v in results["0.0"]["prefix"].values()
        ),
        "summary": summary,
        "chosen_alpha": chosen,
        "results": results,
        "total_seconds": time.monotonic() - started,
    }


@app.local_entrypoint()
def main():
    result = json.loads(select.remote(INPUTS))
    result["input_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    destination = (
        ROOT / "artifacts/wsp-v3-select" / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result.get(k)
                for k in (
                    "failed",
                    "baseline_prefix_read_file",
                    "summary",
                    "chosen_alpha",
                    "total_seconds",
                )
            },
            indent=2,
        )
    )
