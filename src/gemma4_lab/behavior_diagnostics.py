"""Synthetic tool sessions and a bounded arithmetic checker; never execute generated code."""

import ast
import difflib
import json
from dataclasses import asdict
from pathlib import PurePosixPath

VISIBLE_INPUTS = (-1, 0, 2)
CHECK_INPUTS = (-13, -7, -1, 0, 2, 11, 17)
FAMILIES = {"prefix_corruption", "failing_assertion", "passing_control", "irrelevant_pass"}


def _tool(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOL_DEFINITIONS = [
    _tool(
        "read_file",
        "Read a file, optionally selecting inclusive one-based line numbers.",
        {
            "filepath": {"type": "string"},
            "start_line": {"type": ["integer", "null"]},
            "end_line": {"type": ["integer", "null"]},
        },
        ["filepath"],
    ),
    _tool(
        "edit_file",
        "Replace matching text in task.py using the native resilient editor.",
        {
            "filepath": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"},
            "allow_multiple": {"type": "boolean", "default": False},
        },
        ["filepath", "old_string", "new_string"],
    ),
    _tool(
        "run_command",
        "Run one of the two documented fixture checks.",
        {"command": {"type": "string"}},
        ["command"],
    ),
    _tool("submit_patch", "Submit the current diff and finish.", {}, []),
]


class UnsupportedSource(ValueError):
    """The source falls outside the explicitly documented fixture grammar."""


def check_source(source: str, factor: int, offset: int, inputs=CHECK_INPUTS) -> dict:
    """Check finite integer inputs by interpreting a tiny AST, without eval/exec."""
    try:
        if len(source) > 8192:
            raise UnsupportedSource("Source exceeds 8192 characters")
        tree = ast.parse(source, filename="task.py")
        if sum(1 for _ in ast.walk(tree)) > 256:
            raise UnsupportedSource("Source exceeds 256 AST nodes")
        body = tree.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            if isinstance(body[0].value.value, str):
                body = body[1:]
        if len(body) != 1 or not isinstance(body[0], ast.FunctionDef):
            raise UnsupportedSource("Retain exactly one adjust(value) function")
        func = body[0]
        args = func.args
        if (
            func.name != "adjust"
            or len(args.args) != 1
            or args.args[0].arg != "value"
            or args.posonlyargs
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
            or args.defaults
            or args.kw_defaults
            or func.decorator_list
            or func.returns
            or args.args[0].annotation
            or func.type_comment
            or getattr(func, "type_params", [])
        ):
            raise UnsupportedSource("Retain the unannotated adjust(value) signature")
        statements = list(func.body)
        if statements and isinstance(statements[0], ast.Expr):
            expr = statements[0].value
            if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
                statements = statements[1:]
        if not statements or not isinstance(statements[-1], ast.Return):
            raise UnsupportedSource("End the function with a return expression")

        def bounded(value):
            if type(value) is not int or abs(value) > 10**12:
                raise UnsupportedSource("Only bounded integer arithmetic is supported")
            return value

        def expression(node, values):
            if isinstance(node, ast.Constant):
                return bounded(node.value)
            if isinstance(node, ast.Name) and node.id in values:
                return values[node.id]
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = expression(node.operand, values)
                return bounded(value if isinstance(node.op, ast.UAdd) else -value)
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
                left, right = expression(node.left, values), expression(node.right, values)
                if isinstance(node.op, ast.Add):
                    return bounded(left + right)
                if isinstance(node.op, ast.Sub):
                    return bounded(left - right)
                return bounded(left * right)
            raise UnsupportedSource("Use integer constants, variables, +, -, and * only")

        observed = []
        for value in inputs:
            values = {"value": value}
            for stmt in statements[:-1]:
                if (
                    not isinstance(stmt, ast.Assign)
                    or len(stmt.targets) != 1
                    or not isinstance(stmt.targets[0], ast.Name)
                    or stmt.type_comment
                ):
                    raise UnsupportedSource("Only simple intermediate assignments are supported")
                values[stmt.targets[0].id] = expression(stmt.value, values)
            observed.append(expression(statements[-1].value, values))
        expected = [factor * value + offset for value in inputs]
        return {
            "status": "correct" if observed == expected else "wrong",
            "inputs": list(inputs),
            "observed": observed,
            "expected": expected,
        }
    except SyntaxError as exc:
        return {"status": "syntax_error", "message": str(exc)}
    except (UnsupportedSource, RecursionError, ValueError) as exc:
        return {"status": "unsupported", "message": str(exc)}


def native_edit(before, old, new, allow_multiple=False):
    """Import the official implementation only inside the remote runtime."""
    from adk_eval_core.editing import apply_replacement

    return asdict(apply_replacement(before, old, new, allow_multiple=allow_multiple))


def _source(factor, offset):
    return f"def adjust(value):\n    return ({factor} * value) + ({offset})\n"


def _error(kind, message, **extra):
    return {"status": "error", "error_type": kind, "error_message": message, **extra}


def _path(filepath):
    if not isinstance(filepath, str) or ".." in PurePosixPath(filepath).parts:
        raise ValueError("Invalid fixture filepath")
    if filepath.startswith("/workspace/"):
        filepath = filepath[len("/workspace/") :]
    path = PurePosixPath(filepath).as_posix()
    if path not in {"task.py", "tests/test_task.py", "tests/test_smoke.py"}:
        raise ValueError("Only the three documented fixture files are available")
    return path


class SeededSession:
    """A deterministic seeded continuation, with separate source/workflow outcomes."""

    def __init__(self, case: dict, native_edit=native_edit):
        if case["family"] not in FAMILIES:
            raise ValueError("Unknown fixture family")
        self.case = dict(case)
        self.editor = native_edit
        self.base = _source(case["factor"], case["offset"] - 2)
        self.source = self.base
        self.revision = 0
        self.target_test_revision = None
        self.submitted = False
        self.premature_submit = False
        self.actions = []
        self.seed_turns = []
        self._seed("read_file", {"filepath": "task.py"})
        family = case["family"]
        if family != "irrelevant_pass":
            old = self.base.splitlines()[1]
            new = _source(case["factor"], case["offset"]).splitlines()[1]
            if family == "prefix_corruption":
                old = "    ret"
            if family == "failing_assertion":
                new = _source(case["factor"], case["offset"] - 1).splitlines()[1]
            self._seed("edit_file", {"filepath": "task.py", "old_string": old, "new_string": new})
        command = (
            "pytest tests/test_smoke.py"
            if family == "irrelevant_pass"
            else ("pytest tests/test_task.py")
        )
        self._seed("run_command", {"command": command})
        status = self.summary()["source_status"]
        expected = {
            "prefix_corruption": "syntax_error",
            "failing_assertion": "wrong",
            "passing_control": "correct",
            "irrelevant_pass": "wrong",
        }[family]
        if status != expected or any(t["response"]["status"] != "ok" for t in self.seed_turns[:-1]):
            raise ValueError(f"Seed precondition failed: {case['id']} / {status}")
        if family == "prefix_corruption" and self.seed_turns[1]["response"]["strategy"] != "exact":
            raise ValueError("Prefix-corruption seed must use native exact replacement")

    def _seed(self, name, args):
        self.seed_turns.append(
            {"name": name, "arguments": args, "response": self._dispatch(name, args)}
        )

    def seed_messages(self, context: str, max_actions: int) -> list[dict]:
        messages = [
            {
                "role": "user",
                "content": context.format(
                    factor=self.case["factor"], offset=self.case["offset"], max_actions=max_actions
                ),
            }
        ]
        for index, turn in enumerate(self.seed_turns):
            call_id = f"seed_{index}"
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": turn["name"],
                                "arguments": json.dumps(turn["arguments"]),
                            },
                        }
                    ],
                }
            )
            messages.append(
                {"role": "tool", "tool_call_id": call_id, "content": json.dumps(turn["response"])}
            )
        return messages

    def _files(self):
        factor, offset = self.case["factor"], self.case["offset"]
        return {
            "task.py": self.source,
            "tests/test_task.py": "from task import adjust\n\ndef test_adjust():\n"
            + "".join(f"    assert adjust({x}) == {factor * x + offset}\n" for x in VISIBLE_INPUTS),
            "tests/test_smoke.py": "import task\n\ndef test_import():\n"
            "    assert callable(task.adjust)\n",
        }

    def dispatch(self, name: str, args: dict) -> dict:
        if self.submitted:
            return _error("ProtocolError", "The patch has already been submitted")
        response = self._dispatch(name, args)
        self.actions.append({"name": name, "arguments": args, "response": response})
        return response

    def _dispatch(self, name, args):
        try:
            if not isinstance(args, dict):
                raise ValueError("Tool arguments must be a JSON object")
            if name == "read_file":
                if set(args) - {"filepath", "start_line", "end_line"}:
                    raise ValueError("Unknown read_file argument")
                path = _path(args["filepath"])
                lines = self._files()[path].splitlines(keepends=True)
                start, end = args.get("start_line"), args.get("end_line")
                start, end = 1 if start is None else start, len(lines) if end is None else end
                if type(start) is not int or type(end) is not int or not 1 <= start <= end:
                    raise ValueError("Use positive inclusive line bounds")
                return {
                    "status": "ok",
                    "filepath": path,
                    "content": "".join(lines[start - 1 : end]),
                    "start_line": start,
                    "end_line": min(end, len(lines)),
                    "total_lines": len(lines),
                    "is_truncated": False,
                }
            if name == "edit_file":
                if set(args) - {"filepath", "old_string", "new_string", "allow_multiple"}:
                    raise ValueError("Unknown edit_file argument")
                path = _path(args["filepath"])
                if path != "task.py":
                    return _error("FileEditError", "Tests are read-only")
                old, new = args["old_string"], args["new_string"]
                multiple = args.get("allow_multiple", False)
                if not isinstance(old, str) or not old or not isinstance(new, str):
                    raise ValueError("Nonempty old_string and string new_string are required")
                if len(old) + len(new) > 16384 or type(multiple) is not bool:
                    raise ValueError("Invalid edit size or allow_multiple")
                result = self.editor(self.source, old, new, allow_multiple=multiple)
                if result.get("error_message"):
                    return _error("FileEditError", result["error_message"])
                before = self.source
                self.source = result["new_content"]
                if before != self.source:
                    self.revision += 1
                diff = "".join(
                    difflib.unified_diff(
                        before.splitlines(True),
                        self.source.splitlines(True),
                        fromfile=path,
                        tofile=path,
                    )
                )
                return {
                    "status": "ok",
                    "filepath": path,
                    "occurrences": result["occurrences"],
                    "strategy": result["strategy"],
                    "diff": diff,
                    "is_truncated": False,
                }
            if name == "run_command":
                if set(args) != {"command"} or not isinstance(args["command"], str):
                    raise ValueError("Supply only a string command")
                command = args["command"].strip()
                if command.startswith("python -m "):
                    command = command[len("python -m ") :]
                if command not in {"pytest tests/test_task.py", "pytest tests/test_smoke.py"}:
                    return _error("CommandError", "Unsupported fixture command")
                check = check_source(
                    self.source, self.case["factor"], self.case["offset"], VISIBLE_INPUTS
                )
                smoke = command.endswith("test_smoke.py")
                if check["status"] == "correct" or smoke and check["status"] == "wrong":
                    if not smoke:
                        self.target_test_revision = self.revision
                    return {
                        "status": "ok",
                        "stdout": "1 passed (fixture checker)\n",
                        "stderr": "",
                        "exit_code": 0,
                    }
                exit_code = 1 if check["status"] == "wrong" else 2
                if check["status"] == "wrong":
                    index = next(
                        i
                        for i, (a, b) in enumerate(
                            zip(check["observed"], check["expected"], strict=True)
                        )
                        if a != b
                    )
                    message = (
                        f"AssertionError: adjust({VISIBLE_INPUTS[index]}) returned "
                        f"{check['observed'][index]}, expected {check['expected'][index]}"
                    )
                else:
                    message = f"{check['status']}: {check.get('message', '')}"
                return _error(
                    "CommandError",
                    "Fixture check failed",
                    details={"stdout": f"E {message}\n", "stderr": "", "exit_code": exit_code},
                )
            if name == "submit_patch":
                if args:
                    raise ValueError("submit_patch takes no arguments")
                self.submitted = True
                self.premature_submit = not self.summary()["workflow_complete"]
                patch = self.patch()
                return {
                    "status": "ok",
                    "patch_size": len(patch.encode()),
                    "files_changed": int(bool(patch)),
                }
            return _error("UnknownToolError", f"Unknown tool: {name}")
        except (KeyError, TypeError, ValueError) as exc:
            return _error("ValidationError", str(exc))

    def patch(self):
        return "".join(
            difflib.unified_diff(
                self.base.splitlines(True),
                self.source.splitlines(True),
                fromfile="a/task.py",
                tofile="b/task.py",
            )
        )

    def summary(self):
        check = check_source(self.source, self.case["factor"], self.case["offset"])
        checked = self.target_test_revision == self.revision
        return {
            "source_status": check["status"],
            "source_correct": check["status"] == "correct",
            "source_check": check,
            "submitted": self.submitted,
            "target_checked_current": checked,
            "has_diff": bool(self.patch()),
            "workflow_complete": bool(
                self.submitted and checked and self.patch() and check["status"] == "correct"
            ),
            "premature_submit": self.premature_submit,
            "revision": self.revision,
            "target_test_revision": self.target_test_revision,
            "actions": len(self.actions),
        }
