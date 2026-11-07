"""One bounded GPU feasibility check: load the approved E4B and read hidden states.

No gradient, edit, adapter or generation loop. It reports whether a plain
Transformers forward pass works on the staged checkpoint and whether the inputs
to attention output projections can be hooked. Tensor imports stay remote.
"""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL_PATH = "/cache/models/e4b-v2"
PROMPTS = [
    "The capital of France is",
    "def add(a, b):\n    return",
    "To list files in a directory, run",
]
RESOURCES = {"gpu": "A10G", "timeout_seconds": 900, "startup_timeout_seconds": 600}
image = None
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.modal_runtime import build_runtime_image

    image = build_runtime_image(ROOT)

app = modal.App("gemma4-activation-feasibility")
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
def capture(prompts: list[str]) -> str:
    """Return plain JSON text: torch's version type cannot be unpickled locally."""
    import traceback

    try:
        return json.dumps(_capture(prompts))
    except Exception:
        return json.dumps({"failed": traceback.format_exc()[-3000:]})


def _capture(prompts: list[str]) -> dict:
    import time

    import torch
    import transformers

    report = {
        "torch": str(torch.__version__),
        "transformers": str(transformers.__version__),
        "gpu": torch.cuda.get_device_name(0),
        "load_attempts": [],
    }
    started = time.monotonic()
    model = None
    for class_name in ("AutoModelForCausalLM", "AutoModelForImageTextToText"):
        try:
            cls = getattr(transformers, class_name)
            model = cls.from_pretrained(MODEL_PATH, dtype=torch.bfloat16, device_map="cuda")
            report["load_attempts"].append({"class": class_name, "ok": True})
            report["model_class"] = type(model).__name__
            break
        except Exception as exc:  # recorded, bounded to two attempts
            report["load_attempts"].append(
                {"class": class_name, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:600]}
            )
    report["load_seconds"] = time.monotonic() - started
    if model is None:
        return report
    model.eval()
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_PATH)
    report["gpu_memory_gib_after_load"] = torch.cuda.memory_allocated() / 1024**3

    o_proj = {n: m for n, m in model.named_modules() if n.endswith("self_attn.o_proj")}
    names = sorted(o_proj)
    report["o_proj_count"] = len(names)
    report["o_proj_examples"] = (
        [
            {
                "name": n,
                "type": type(o_proj[n]).__name__,
                "attrs": sorted(a for a in vars(o_proj[n]) if not a.startswith("_"))[:12],
                "weight_shape": list(
                    getattr(getattr(o_proj[n], "weight", None), "shape", []) or []
                ),
                "weight_dtype": str(getattr(getattr(o_proj[n], "weight", None), "dtype", None)),
            }
            for n in (names[0], names[len(names) // 2], names[-1])
        ]
        if names
        else []
    )

    captured = {}
    handles = []
    for n in names:

        def hook(_module, args, name=n):
            captured[name] = args[0][0, -1].float().norm().item()

        handles.append(o_proj[n].register_forward_pre_hook(hook))

    results = []
    for prompt in prompts:
        ids = tokenizer(prompt, return_tensors="pt").to("cuda")
        captured.clear()
        with torch.no_grad():
            out = model(**ids, output_hidden_states=True)
        hidden = out.hidden_states
        top = torch.topk(out.logits[0, -1].float().softmax(-1), 5)
        results.append(
            {
                "prompt": prompt,
                "tokens": int(ids["input_ids"].shape[1]),
                "hidden_state_count": len(hidden),
                "hidden_shape": list(hidden[-1].shape),
                "last_token_norm_by_layer": [
                    round(h[0, -1].float().norm().item(), 3) for h in hidden
                ],
                "finite": bool(all(torch.isfinite(h).all().item() for h in hidden)),
                "o_proj_input_norm_hooked": len(captured),
                "top5": [
                    [tokenizer.decode([int(i)]), round(float(p), 4)]
                    for p, i in zip(top.values, top.indices, strict=True)
                ],
            }
        )
    for handle in handles:
        handle.remove()
    report["results"] = results
    report["peak_gpu_memory_gib"] = torch.cuda.max_memory_allocated() / 1024**3
    report["total_seconds"] = time.monotonic() - started
    return report


@app.local_entrypoint()
def main():
    result = json.loads(capture.remote(PROMPTS))
    result["profile"] = "onepiecification"
    result["input_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    destination = (
        ROOT
        / "artifacts/activation-feasibility-v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2)[:6000])
