"""Gradient-trained prompt-distillation LoRA baseline (v3 amendment 2, frozen).

Rank-8 LoRA on layer 29 `o_proj`, simulated as an additive hook on the frozen quantized model,
trained on the 24 v2 design cases only (teacher = edit-integrity prompt on the 12 prefix cases;
preservation targets = the base prompt's own continuations on 12 non-target cases). Stops at the
first 20-step checkpoint meeting the design-set rule; exports standard PEFT bf16 factors.
"""

import base64
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL_PATH = "/cache/models/e4b-v2"
LAYER = 29
RANK, LR, MAX_STEPS, EVAL_EVERY, NEW_TOKENS, MIN_READS = 8, 2e-3, 120, 20, 48, 11
SEED = 20261108
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
        "design_cases": [c for c in cases if c["role"] == "design"],
    }

app = modal.App("gemma4-wsp-v3-distill")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    gpu="A10G",
    cpu=2,
    memory=16 * 1024,
    timeout=1800,
    startup_timeout=600,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def train(inputs: dict) -> str:
    import traceback

    try:
        return json.dumps(_train(inputs))
    except Exception:
        return json.dumps({"failed": traceback.format_exc()[-3000:]})


def _train(inputs: dict) -> dict:
    import io
    import re
    import time

    import torch
    import transformers
    from safetensors.torch import save as save_bytes

    from gemma4_lab.behavior_diagnostics import TOOL_DEFINITIONS, SeededSession

    started = time.monotonic()
    model = transformers.AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, dtype=torch.bfloat16, device_map="cuda"
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    tok = transformers.AutoTokenizer.from_pretrained(MODEL_PATH)
    name = f"model.language_model.layers.{LAYER}.self_attn.o_proj"
    module = dict(model.named_modules())[name]
    torch.manual_seed(SEED)
    a = torch.empty((RANK, 4096), device="cuda", dtype=torch.float32)
    torch.nn.init.kaiming_uniform_(a, a=5**0.5)
    a.requires_grad_(True)
    b = torch.zeros((2560, RANK), device="cuda", dtype=torch.float32, requires_grad=True)
    state = {"on": False}

    def hook(_m, args, output):
        if not state["on"]:
            return output
        return output + ((args[0].float() @ a.T) @ b.T).to(output.dtype)

    module.register_forward_hook(hook)

    def ids_for(case, system):
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

    def generate(ids):
        with torch.no_grad():
            out = model.generate(input_ids=ids, max_new_tokens=NEW_TOKENS, do_sample=False)
        return out[0, ids.shape[1] :]

    def first_call(ids):
        text = tok.decode(generate(ids))
        match = re.search(r"call:([A-Za-z_]+)\{", text)
        return match.group(1) if match else None

    prefix = [c for c in inputs["design_cases"] if c["family"] == "prefix_corruption"]
    other = [c for c in inputs["design_cases"] if c["family"] != "prefix_corruption"]
    student = {c["id"]: ids_for(c, inputs["base_prompt"]) for c in prefix + other}
    state["on"] = False
    targets = {}
    for c in prefix:
        targets[c["id"]] = generate(ids_for(c, inputs["teacher_prompt"]))
    baseline = {}
    for c in other:
        targets[c["id"]] = generate(student[c["id"]])
        baseline[c["id"]] = first_call(student[c["id"]])

    optimizer = torch.optim.AdamW([a, b], lr=LR, weight_decay=0.0)
    log, chosen = [], None

    def evaluate():
        state["on"] = True
        reads = sum(first_call(student[c["id"]]) == "read_file" for c in prefix)
        same = sum(first_call(student[c["id"]]) == baseline[c["id"]] for c in other)
        state["on"] = False
        return reads, same

    for step in range(1, MAX_STEPS + 1):
        optimizer.zero_grad()
        batch = [prefix[(3 * (step - 1) + i) % len(prefix)] for i in range(3)] + [
            other[(3 * (step - 1) + i) % len(other)] for i in range(3)
        ]
        total = 0.0
        for case in batch:
            prompt, target = student[case["id"]], targets[case["id"]]
            n = target.shape[0]
            full = torch.cat([prompt, target.unsqueeze(0)], dim=1)
            state["on"] = True
            logits = model(input_ids=full, logits_to_keep=n + 1).logits[0, :n].float()
            state["on"] = False
            loss = torch.nn.functional.cross_entropy(logits, target) / len(batch)
            loss.backward()
            total += float(loss)
        if step == 1:
            log.append({"grad_norm_a": float(a.grad.norm()), "grad_norm_b": float(b.grad.norm())})
        torch.nn.utils.clip_grad_norm_([a, b], 1.0)
        optimizer.step()
        entry = {"step": step, "loss": total}
        if step % EVAL_EVERY == 0:
            reads, same = evaluate()
            entry.update(prefix_read_file=reads, nontarget_unchanged=same)
            if reads >= MIN_READS and same == len(other):
                chosen = step
        log.append(entry)
        if chosen:
            break

    result = {
        "chosen_step": chosen,
        "log": log,
        "qualified": chosen is not None,
        "total_seconds": time.monotonic() - started,
    }
    if chosen:
        factors = {
            f"base_model.model.{name}.lora_A.weight": a.detach().bfloat16().cpu().contiguous(),
            f"base_model.model.{name}.lora_B.weight": b.detach().bfloat16().cpu().contiguous(),
        }
        blob = save_bytes(factors, metadata={"format": "pt"})
        result["adapter_b64"] = base64.b64encode(blob).decode()
        result["adapter_sha256"] = hashlib.sha256(blob).hexdigest()
    del io
    return result


@app.local_entrypoint()
def main():
    result = json.loads(train.remote(INPUTS))
    destination = ROOT / "artifacts/wsp-v3-distill" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination.mkdir(parents=True, exist_ok=True)
    blob = result.pop("adapter_b64", None)
    result["input_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (destination / "train.json").write_text(json.dumps(result, indent=2) + "\n")
    if blob:
        folder = destination / "submission/adapters/wsp_read"
        folder.mkdir(parents=True)
        (folder / "adapter_model.safetensors").write_bytes(base64.b64decode(blob))
        peft = {
            "base_model_name_or_path": MODEL_PATH,
            "bias": "none",
            "fan_in_fan_out": False,
            "inference_mode": True,
            "lora_alpha": RANK,
            "lora_dropout": 0.0,
            "peft_type": "LORA",
            "r": RANK,
            "target_modules": ["o_proj"],
            "task_type": "CAUSAL_LM",
            "use_dora": False,
            "use_rslora": False,
        }
        (folder / "adapter_config.json").write_text(json.dumps(peft, indent=2) + "\n")
        (destination / "prepare.json").write_text(
            json.dumps({"kind": "distilled adapter holder", "train_report": "train.json"}) + "\n"
        )
    print(json.dumps({**result, "log": result.get("log", [])[-8:]}, indent=2)[:3500])
    print(str(destination))
