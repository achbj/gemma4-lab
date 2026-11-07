"""Design-set activation capture for weight-space study v2 (pre-registered).

Replays each *design* case's seeded history to the first assistant turn under two
system prompts, records `self_attn.o_proj` input/output at the last token for layers
12-38, picks the layer by the frozen rule, then collects the background covariance
of that layer's input over all tokens of the non-target design cases. Evaluation-panel
cases are never loaded. No weights are modified and no adapter is built here.
"""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL_PATH = "/cache/models/e4b-v2"
OUTPUT = "/cache/wsp-v2/capture-v1.safetensors"
LAYERS = list(range(12, 39))
BASE_PROMPT = "submissions/wsp-base-v1/prompts/system.md"
TEACHER_PROMPT = "submissions/edit-integrity-v1-3m/prompts/system.md"
CONTEXT = "submissions/behavior-diagnostic-v1/prompts/context.md"
CASES = "configs/wsp-v2-cases.json"
GENERATE_TOKENS = 64
RESOURCES = {"gpu": "A10G", "timeout_seconds": 900, "startup_timeout_seconds": 600}
image = None
INPUTS = {}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.modal_runtime import build_runtime_image

    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")
    cases = json.loads((ROOT / CASES).read_text())["cases"]
    INPUTS = {
        "base_prompt": (ROOT / BASE_PROMPT).read_text(),
        "teacher_prompt": (ROOT / TEACHER_PROMPT).read_text(),
        "context": (ROOT / CONTEXT).read_text(),
        "design_cases": [c for c in cases if c["role"] == "design"],
    }

app = modal.App("gemma4-wsp-v2-capture")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    gpu=RESOURCES["gpu"],
    cpu=2,
    memory=16 * 1024,
    timeout=RESOURCES["timeout_seconds"],
    startup_timeout=RESOURCES["startup_timeout_seconds"],
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def capture(inputs: dict) -> str:
    import traceback

    try:
        return json.dumps(_capture(inputs))
    except Exception:
        return json.dumps({"failed": traceback.format_exc()[-3000:]})


def _messages(session, prompt, context):
    out = [{"role": "system", "content": prompt}]
    for message in session.seed_messages(context, 6):
        message = json.loads(json.dumps(message))
        for call in message.get("tool_calls", []):
            call["function"]["arguments"] = json.loads(call["function"]["arguments"])
        out.append(message)
    return out


def _capture(inputs: dict) -> dict:
    import time

    import torch
    import transformers
    from safetensors.torch import save_file

    from gemma4_lab.behavior_diagnostics import TOOL_DEFINITIONS, SeededSession

    started = time.monotonic()
    model = transformers.AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, dtype=torch.bfloat16, device_map="cuda"
    ).eval()
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_PATH)
    modules = {
        i: dict(model.named_modules())[f"model.language_model.layers.{i}.self_attn.o_proj"]
        for i in LAYERS
    }
    prompts = {"base": inputs["base_prompt"], "teacher": inputs["teacher_prompt"]}
    design = inputs["design_cases"]
    target = [c for c in design if c["family"] == "prefix_corruption"]
    background = [c for c in design if c["family"] != "prefix_corruption"]
    report = {"transformers": str(transformers.__version__), "gpu": torch.cuda.get_device_name(0)}

    def tokens_for(case, prompt):
        session = SeededSession(case)
        text = tokenizer.apply_chat_template(
            _messages(session, prompt, inputs["context"]),
            tools=TOOL_DEFINITIONS,
            add_generation_prompt=True,
            tokenize=False,
        )
        ids = tokenizer(text, return_tensors="pt", add_special_tokens=False)
        return text, ids["input_ids"].to("cuda")

    # Pass 1: last-token records at every candidate layer.
    store = {}
    handles = []
    for i, module in modules.items():

        def hook(_m, args, output, layer=i):
            store[layer] = (args[0][0, -1].float().cpu(), output[0, -1].float().cpu())

        handles.append(module.register_forward_hook(hook))
    records = {name: {i: [] for i in LAYERS} for name in prompts}
    rendered, behaviour = {}, []
    for case in target:
        entry = {"id": case["id"]}
        for name, prompt in prompts.items():
            text, ids = tokens_for(case, prompt)
            store.clear()
            with torch.no_grad():
                logits = model(input_ids=ids).logits[0, -1].float()
            for i in LAYERS:
                records[name][i].append(store[i])
            entry[name + "_tokens"] = int(ids.shape[1])
            entry[name + "_top1"] = tokenizer.decode([int(logits.argmax())])
            if case is target[0]:
                rendered[name] = text[-900:]
        behaviour.append(entry)
    for handle in handles:
        handle.remove()
    report["rendered_tail"] = rendered

    tensors, ratios = {}, {}
    for i in LAYERS:
        k_base = torch.stack([k for k, _ in records["base"][i]]).mean(0)
        o_base = torch.stack([o for _, o in records["base"][i]]).mean(0)
        o_teacher = torch.stack([o for _, o in records["teacher"][i]]).mean(0)
        d = o_teacher - o_base
        ratios[i] = float(d.norm() / o_base.norm())
        tensors[f"layer{i}.k_star"], tensors[f"layer{i}.d"] = k_base, d
    chosen = max(ratios, key=ratios.get)
    report["layer_ratios"] = {str(i): round(r, 5) for i, r in ratios.items()}
    report["chosen_layer"] = chosen
    # Keep only the chosen layer's vectors; other layers' ratios are in the report.
    saved = {n: v.contiguous() for n, v in tensors.items() if n.startswith(f"layer{chosen}.")}

    # Pass 2: background covariance of the chosen layer input over all tokens.
    width = saved[f"layer{chosen}.k_star"].numel()
    gram = torch.zeros((width, width), dtype=torch.float64, device="cuda")
    count = 0

    def gram_hook(_m, args):
        nonlocal gram, count
        keys = args[0][0].double()
        gram += keys.T @ keys
        count += keys.shape[0]

    handle = modules[chosen].register_forward_pre_hook(gram_hook)
    for case in background:
        _, ids = tokens_for(case, prompts["base"])
        with torch.no_grad():
            model(input_ids=ids)
    handle.remove()
    saved["covariance"] = (gram / count).float().cpu().contiguous()
    report["covariance_tokens"] = count
    report["covariance_trace_per_dim"] = float(saved["covariance"].diag().mean())

    # Replay fidelity: greedy first action under each prompt (HF vs the earlier vLLM screens).
    for case, entry in zip(target, behaviour, strict=True):
        for name, prompt in prompts.items():
            _, ids = tokens_for(case, prompt)
            with torch.no_grad():
                out = model.generate(input_ids=ids, max_new_tokens=GENERATE_TOKENS, do_sample=False)
            entry[name + "_first_action"] = tokenizer.decode(out[0, ids.shape[1] :])[:240]
    report["behaviour"] = behaviour

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    save_file(saved, OUTPUT, metadata={"format": "pt", "layer": str(chosen)})
    volume.commit()
    report["output_sha256"] = hashlib.sha256(Path(OUTPUT).read_bytes()).hexdigest()
    report["tensor_shapes"] = {n: list(v.shape) for n, v in saved.items()}
    report["total_seconds"] = time.monotonic() - started
    report["peak_gpu_memory_gib"] = torch.cuda.max_memory_allocated() / 1024**3
    return report


@app.local_entrypoint()
def main():
    result = json.loads(capture.remote(INPUTS))
    result["profile"] = "onepiecification"
    result["input_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            BASE_PROMPT,
            TEACHER_PROMPT,
            CONTEXT,
            CASES,
            "infrastructure/modal/wsp_v2_capture.py",
        )
    }
    destination = (
        ROOT / "artifacts/wsp-v2-capture" / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2)[:7000])
