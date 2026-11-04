"""Check fixture mounts without importing the remote tensor runtime."""

import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from gemma4_lab.assets import sha256
from gemma4_lab.remote_evaluation import configure_workspace_imports, fixture_identity


class FixtureIdentityTests(unittest.TestCase):
    def test_checkout_import_wins_over_a_host_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            site_packages = root / "venv/lib/python3.12/site-packages"
            host = root / "host"
            for path in (workspace / "src", site_packages, host):
                path.mkdir(parents=True)
            (workspace / "src/probe_package.py").write_text("value = 'checkout'\n")
            (host / "probe_package.py").write_text("value = 'host'\n")
            manager = types.SimpleNamespace(
                start=lambda: "task",
                sandboxes={"task": {"workspace": workspace, "venv": root / "venv"}},
            )
            configure_workspace_imports(manager)
            manager.start()
            result = subprocess.check_output(
                [
                    sys.executable,
                    "-S",
                    "-c",
                    "import sys, site; "
                    f"sys.path.insert(0, {str(host)!r}); "
                    f"site.addsitedir({str(site_packages)!r}); "
                    "import probe_package; print(probe_package.value)",
                ],
                text=True,
            )
            self.assertEqual(result.strip(), "checkout")

    def test_rejects_answer_files_and_same_size_fixture_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "snapshot.tgz"
            fixture.write_bytes(b"abc")
            manifest = {
                "files": [{"name": fixture.name, "size_bytes": 3, "sha256": sha256(fixture)}]
            }
            self.assertEqual(len(fixture_identity(root, manifest)), 64)
            answers = root / "tasks.jsonl"
            answers.write_text("evaluation-only data")
            with self.assertRaisesRegex(ValueError, "unexpected"):
                fixture_identity(root, manifest)
            answers.unlink()
            fixture.write_bytes(b"xyz")
            with self.assertRaisesRegex(ValueError, "checksum"):
                fixture_identity(root, manifest)
