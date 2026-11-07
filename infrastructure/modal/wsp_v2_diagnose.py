"""Exploratory, post-hoc diagnostic after the failed v2 gate (not part of any gate).

Questions: (1) does the edit's key fire on evaluation decision points, and does the design-set
shift `d` generalize; (2) in an idealized dense-edit simulation, does any single-layer shift of this
form change the first tool-call choice? Reports teacher-forced log P(read_file) - log P(edit_file).
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
ALPHAS = [0.0, 1.0, 2.0, 4.0, 8.0, -1.0]
RIDGE = 1e-3
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
        "teacher_prompt": (ROOT / "submissions/edit-integrity-v1-3m/prompts/system.md").read_text(),
        "context": (ROOT / "submissions/behavior-diagnostic-v1/prompts/context.md").read_text(),
        "cases": [c for c in cases if c["role"] == "eval" and c["family"] == "prefix_corruption"],
    }

app = modal.App("gemma4-wsp-v2-diagnose")
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
def diagnose(inputs: dict) -> str:
    import traceback

    try:
        return json.dumps(_diagnose(inputs))
    except Exception:
        return json.dumps({"failed": traceback.format_exc()[-3000:]})


def _diagnose(inputs: dict) -> dict:
    import torch
    import transformers
    from safetensors import safe_open

    from gemma4_lab.behavior_diagnostics import TOOL_DEFINITIONS, SeededSession

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
    state = {"alpha": 0.0, "record": None}

    def hook(_m, args, output):
        x = args[0]
        state["record"] = (x[0, -1].float().cpu(), output[0, -1].float().cpu())
        if state["alpha"] != 0.0:
            shift = (x.float() @ a_row).unsqueeze(-1) * d_cuda * state["alpha"]
            return output + shift.to(output.dtype)
        return output

    module.register_forward_hook(hook)

    def prompt_ids(case, system):
        session = SeededSession(case)
        messages = [{"role": "system", "content": system}]
        for message in session.seed_messages(inputs["context"], 6):
            message = json.loads(json.dumps(message))
            for call in message.get("tool_calls", []):
                call["function"]["arguments"] = json.loads(call["function"]["arguments"])
            messages.append(message)
        text = tok.apply_chat_template(
            messages, tools=TOOL_DEFINITIONS, add_generation_prompt=True, tokenize=False
        )
        return tok(text, return_tensors="pt", add_special_tokens=False)["input_ids"].cuda()

    read_ids = tok("<|tool_call>call:read_file", add_special_tokens=False)["input_ids"]
    edit_ids = tok("<|tool_call>call:edit_file", add_special_tokens=False)["input_ids"]

    def logprob(ids, cont):
        full = torch.cat([ids, torch.tensor([cont], device="cuda")], dim=1)
        with torch.no_grad():
            logits = model(input_ids=full).logits[0].float().log_softmax(-1)
        start = ids.shape[1]
        return sum(float(logits[start + i - 1, t]) for i, t in enumerate(cont))

    keys, o_base, o_teacher, dots, cosines = [], [], [], [], []
    margins = {str(a): [] for a in ALPHAS}
    teacher_margin = []
    for case in inputs["cases"]:
        state["alpha"] = 0.0
        ids = prompt_ids(case, inputs["base_prompt"])
        with torch.no_grad():
            model(input_ids=ids)
        k, o = state["record"]
        keys.append(k)
        o_base.append(o)
        dots.append(float(k.cuda() @ a_row))
        cosines.append(float(torch.nn.functional.cosine_similarity(k.double(), k_star, dim=0)))
        ids_t = prompt_ids(case, inputs["teacher_prompt"])
        with torch.no_grad():
            model(input_ids=ids_t)
        o_teacher.append(state["record"][1])
        teacher_margin.append(logprob(ids_t, read_ids) - logprob(ids_t, edit_ids))
        for alpha in ALPHAS:
            state["alpha"] = alpha
            margins[str(alpha)].append(logprob(ids, read_ids) - logprob(ids, edit_ids))
    state["alpha"] = 0.0

    def stats(values):
        t = torch.tensor(values, dtype=torch.float64)
        return {"mean": float(t.mean()), "min": float(t.min()), "max": float(t.max())}

    d_eval = torch.stack(o_teacher).mean(0) - torch.stack(o_base).mean(0)
    return {
        "layer": layer,
        "cases": len(inputs["cases"]),
        "key_dot_a": stats(dots),
        "key_cosine_with_design_mean": stats(cosines),
        "key_norm": stats([float(k.norm()) for k in keys]),
        "design_key_norm": float(k_star.norm()),
        "d_design_norm": float(d.norm()),
        "d_eval_norm": float(d_eval.norm()),
        "cosine_d_eval_vs_d_design": float(
            torch.nn.functional.cosine_similarity(d_eval.double(), d, dim=0)
        ),
        "logP_read_minus_edit_base_prompt_by_alpha": {a: stats(m) for a, m in margins.items()},
        "fraction_read_preferred_by_alpha": {
            a: sum(x > 0 for x in m) / len(m) for a, m in margins.items()
        },
        "logP_read_minus_edit_teacher_prompt": stats(teacher_margin),
        "fraction_read_preferred_teacher": sum(x > 0 for x in teacher_margin) / len(teacher_margin),
    }


@app.local_entrypoint()
def main():
    result = json.loads(diagnose.remote(INPUTS))
    result["input_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    destination = (
        ROOT
        / "artifacts/wsp-v2-diagnose"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2)[:6000])
