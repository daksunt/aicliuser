import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "delegate-cli" / "scripts"


def load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_executable(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class DelegateCliScriptTests(unittest.TestCase):
    def test_discover_cli_reports_path_version_help_and_invocations(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            make_executable(
                bin_dir / "agent",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "if '--version' in sys.argv:\n"
                "    print('agent 1.2.3')\n"
                "elif '--help' in sys.argv:\n"
                "    print('Usage: agent [--print] [--prompt TEXT]')\n"
                "else:\n"
                "    print('ran')\n",
            )
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                discover_cli = load_script("discover_cli.py")
                report = discover_cli.discover("agent")
            finally:
                os.environ["PATH"] = old_path

        self.assertEqual(report["name"], "agent")
        self.assertTrue(report["found"])
        self.assertEqual(report["path"], str(bin_dir / "agent"))
        self.assertEqual(report["version"]["exit_code"], 0)
        self.assertIn("agent 1.2.3", report["version"]["stdout"])
        self.assertIn("Usage: agent", report["help"]["stdout"])
        self.assertTrue(report["inferred_capabilities"]["accepts_prompt_flag"])
        self.assertTrue(report["inferred_capabilities"]["supports_print_mode"])

    def test_discover_cli_reports_missing_command(self):
        discover_cli = load_script("discover_cli.py")

        report = discover_cli.discover("definitely-not-a-real-cli-name")

        self.assertEqual(
            report,
            {
                "name": "definitely-not-a-real-cli-name",
                "found": False,
                "path": None,
                "version": None,
                "help": None,
                "inferred_capabilities": {},
            },
        )

    def test_scan_candidates_reports_found_and_missing_clis(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            make_executable(
                bin_dir / "alpha",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "if '--version' in sys.argv:\n"
                "    print('alpha 0.1')\n"
                "elif '--help' in sys.argv:\n"
                "    print('Usage: alpha exec --prompt TEXT')\n",
            )
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                discover_cli = load_script("discover_cli.py")
                report = discover_cli.scan_candidates(["alpha", "missing-cli"], timeout_seconds=2)
            finally:
                os.environ["PATH"] = old_path

        self.assertEqual([item["name"] for item in report["candidates"]], ["alpha", "missing-cli"])
        self.assertEqual([item["name"] for item in report["found"]], ["alpha"])
        self.assertEqual([item["name"] for item in report["missing"]], ["missing-cli"])
        self.assertEqual(report["selection_guidance"], "Present discovered CLI options and require the user to select which CLI(s) to use before delegating, unless the request already names the CLI.")

    def test_default_candidates_include_cursor_agent_executable(self):
        discover_cli = load_script("discover_cli.py")

        self.assertIn("agent", discover_cli.DEFAULT_CANDIDATES)

    def test_run_delegation_captures_transcript_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            transcript = tmp_path / "transcript.json"
            runner = load_script("run_delegation.py")

            result = runner.run_delegation(
                [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)"],
                cwd=tmp_path,
                transcript_path=transcript,
                timeout_seconds=5,
            )

            saved = json.loads(transcript.read_text(encoding="utf-8"))

        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(result["timed_out"])
        self.assertEqual(result["stdout"], "out\n")
        self.assertEqual(result["stderr"], "err\n")
        self.assertEqual(saved["command"][0], sys.executable)
        self.assertEqual(saved["cwd"], str(tmp_path))
        self.assertEqual(saved["exit_code"], 0)

    def test_run_delegation_records_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            transcript = tmp_path / "timeout.json"
            runner = load_script("run_delegation.py")

            result = runner.run_delegation(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=tmp_path,
                transcript_path=transcript,
                timeout_seconds=0.1,
            )

            saved = json.loads(transcript.read_text(encoding="utf-8"))

        self.assertIsNone(result["exit_code"])
        self.assertTrue(result["timed_out"])
        self.assertIn("timed out", result["stderr"].lower())
        self.assertTrue(saved["timed_out"])

    def test_snapshot_status_captures_branch_status_and_diff_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
            tracked = tmp_path / "tracked.txt"
            tracked.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
            tracked.write_text("after\n", encoding="utf-8")
            (tmp_path / "new.txt").write_text("new\n", encoding="utf-8")

            snapshot_status = load_script("snapshot_status.py")
            snapshot = snapshot_status.snapshot(tmp_path)

        self.assertTrue(snapshot["is_git_repo"])
        self.assertIn(snapshot["branch"], {"main", "master"})
        self.assertIn(" M tracked.txt", snapshot["status_short"])
        self.assertIn("?? new.txt", snapshot["status_short"])
        self.assertIn("tracked.txt", snapshot["diff_stat"])


if __name__ == "__main__":
    unittest.main()
