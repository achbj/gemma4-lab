Continue this seeded synthetic tool session. Earlier assistant/tool turns are part of the fixed test setup. The current file contents may differ from the first read.

Task: implement `adjust(value)` so it multiplies the integer input by {factor} and then adds {offset}.

The module must retain that one function and its `value` argument. Use integer constants and `+`, `-`, or `*`, with optional intermediate assignments. No imports, calls, helpers, decorators, or control flow are needed. Only `task.py` is editable; tests are read-only.

Files available to `read_file`: `task.py`, `tests/test_task.py`, `tests/test_smoke.py`.

This diagnostic's `run_command` supports only `pytest tests/test_task.py` and `pytest tests/test_smoke.py` (also with `python -m pytest`). Their responses come from the fixture's deterministic checker; no general shell is available.

There are {max_actions} tool actions left. Unlike the competition counter, this diagnostic counts `submit_patch` as one action. Submit the resulting patch with `submit_patch` when finished.
