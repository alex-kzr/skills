"""Fixture-based tests for the deterministic project setup generator.

Written before ``setup_project.py`` per the test-driven-development skill. Each
negative case snapshots the target tree first and asserts it is untouched after
the expected :class:`setup_project.SetupError`.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import setup_project
from setup_project import SetupError, run_setup


def _valid_input() -> dict:
    """A confirmed, fully specified input object (Graphify enabled)."""
    return {
        "anchors": {
            "project_root": ".",
            "agents_root": ".agents",
            "core_root": "feature-pipeline-skill",
        },
        "task_routing": [
            {"task_type": "tooling", "working_root": "tools"},
            {"task_type": "docs", "working_root": "docs"},
        ],
        "technology_stacks": [
            {
                "stack": "python",
                "checks": [
                    {
                        "name": "unit",
                        "argv": ["uv", "run", "python", "-m", "unittest"],
                        "cwd": "feature-pipeline-skill",
                    },
                    {"name": "lint", "argv": ["ruff", "check", "."], "cwd": "."},
                ],
            }
        ],
        "run_state_path": "tools/feature-pipeline/state",
        "roles": [
            {"role": "executor", "min_grants": ["read", "write"]},
            {"role": "task_verifier", "min_grants": ["read"]},
        ],
        "graphify": {
            "enabled": True,
            "wrapper_source": None,  # filled in by the test with a real fixture dir
            "wrapper_destination": "tools/graphify/config/wrapper",
        },
    }


def _snapshot(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root)).replace(os.sep, "/")] = path.read_bytes()
    return out


class GeneratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name) / "target-repo"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "feature-pipeline-skill" / "pipeline_core").mkdir(parents=True)
        (self.project / "feature-pipeline-skill" / "pipeline_core" / "profiles.py").write_text(
            "# portable core, must not be touched\n", encoding="utf-8"
        )
        (self.project / ".agents").mkdir()
        # An approved wrapper source outside the project.
        self.wrapper_src = Path(self._tmp.name) / "approved-wrapper"
        self.wrapper_src.mkdir()
        (self.wrapper_src / "build_graph.sh").write_text(
            "#!/bin/sh\nexec graphify build tools/graphify \"$@\"\n", encoding="utf-8"
        )

    def _input(self, **overrides) -> dict:
        data = _valid_input()
        data["graphify"]["wrapper_source"] = str(self.wrapper_src)
        for key, value in overrides.items():
            data[key] = value
        return data

    def _run(self, data: dict, *, confirmed: bool = True, report: str = "setup-report.json"):
        return run_setup(
            data,
            project_root=self.project,
            report_path=report,
            confirmed=confirmed,
        )

    # -- fresh generation --------------------------------------------------

    def test_fresh_generation_creates_full_layout(self) -> None:
        report = self._run(self._input())

        cfg = self.project / "tools" / "feature-pipeline" / "config"
        for name in ("pipeline.profile.json", "integrations.json", "checks.json"):
            self.assertTrue((cfg / name).is_file(), name)
        self.assertTrue((self.project / "tools" / "feature-pipeline" / "README.md").is_file())
        self.assertTrue((self.project / "tools" / "graphify" / ".graphifyignore").is_file())
        self.assertTrue(
            (self.project / "tools" / "graphify" / "config" / "wrapper" / "build_graph.sh").is_file()
        )
        self.assertTrue((self.project / "setup-report.json").is_file())

        profile = json.loads((cfg / "pipeline.profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["schema_version"], 1)
        self.assertEqual(
            [r["task_type"] for r in profile["task_routing"]], ["tooling", "docs"]
        )
        self.assertNotIn("checks", profile)  # split into checks.json, never both

        integrations = json.loads((cfg / "integrations.json").read_text(encoding="utf-8"))
        self.assertEqual(report["graphify_enabled"], True)
        self.assertEqual(integrations["graphify"]["workspace"], "tools/graphify")
        self.assertEqual(integrations["graphify"]["diff_policy"], "tracked-empty")

    def test_gitignore_line_added_once_and_preserves_content(self) -> None:
        gitignore = self.project / ".gitignore"
        gitignore.write_text("*.pyc\n/node_modules/\n\n# custom\n.env\n", encoding="utf-8")

        self._run(self._input())
        text = gitignore.read_text(encoding="utf-8")

        self.assertIn("*.pyc\n", text)
        self.assertIn("/node_modules/\n", text)
        self.assertIn("# custom\n", text)
        self.assertIn(".env\n", text)
        self.assertEqual(text.count("/tools/graphify/graphify-out/"), 1)

    def test_graphify_policy_contract(self) -> None:
        self._run(self._input())
        integrations = json.loads(
            (self.project / "tools/feature-pipeline/config/integrations.json").read_text("utf-8")
        )
        block = integrations["graphify"]
        self.assertEqual(
            block["expected_outputs"],
            [
                "tools/graphify/graphify-out/graph.json",
                "tools/graphify/graphify-out/GRAPH_REPORT.md",
                "tools/graphify/graphify-out/manifest.json",
                "tools/graphify/graphify-out/.graphify_labels.json",
                "tools/graphify/graphify-out/.graphify_root",
            ],
        )
        self.assertEqual(
            block["forbidden"],
            [
                "graphify claude install",
                "graphify codex install",
                "graphify antigravity install",
            ],
        )
        self.assertEqual(block["diff_policy"], "tracked-empty")
        joined = json.dumps(integrations)
        self.assertNotIn("graph.html", joined)
        self.assertNotIn('"tools/graphify"\n', joined)  # never ignore the whole tree

    # -- idempotency -----------------------------------------------------

    def test_idempotent_rerun_is_byte_identical(self) -> None:
        self.project.joinpath(".gitignore").write_text("*.log\n", encoding="utf-8")
        self._run(self._input())
        tracked = _snapshot(self.project / "tools")
        gitignore_first = (self.project / ".gitignore").read_bytes()

        self._run(self._input())

        self.assertEqual(_snapshot(self.project / "tools"), tracked)
        self.assertEqual((self.project / ".gitignore").read_bytes(), gitignore_first)
        self.assertEqual(
            (self.project / ".gitignore").read_text("utf-8").count("/tools/graphify/graphify-out/"),
            1,
        )

    # -- fail-closed cases (no writes) ---------------------------------

    def _assert_no_writes(
        self, data: dict, message: str, *, confirmed: bool = True
    ) -> SetupError:
        before = _snapshot(self.project)
        with self.assertRaises(SetupError, msg=message) as ctx:
            self._run(data, confirmed=confirmed)
        self.assertEqual(_snapshot(self.project), before, message)
        return ctx.exception

    def test_missing_confirmation_fails_closed(self) -> None:
        self._assert_no_writes(self._input(), "unconfirmed input", confirmed=False)

    def test_unknown_top_level_key_fails_closed(self) -> None:
        data = self._input()
        data["surprise"] = 1
        self._assert_no_writes(data, "unknown key")

    def test_missing_required_key_fails_closed(self) -> None:
        data = self._input()
        del data["run_state_path"]
        self._assert_no_writes(data, "missing run_state_path")

    def test_absolute_generated_path_fails_closed(self) -> None:
        data = self._input()
        data["run_state_path"] = "/var/run/pipeline"
        self._assert_no_writes(data, "absolute path")

    def test_parent_escape_path_fails_closed(self) -> None:
        data = self._input()
        data["task_routing"][0]["working_root"] = "../outside"
        self._assert_no_writes(data, "parent escape")

    def test_backslash_path_fails_closed(self) -> None:
        data = self._input()
        data["run_state_path"] = "tools\\feature-pipeline\\state"
        self._assert_no_writes(data, "backslash separator")

    def test_shell_form_check_command_fails_closed(self) -> None:
        data = self._input()
        data["technology_stacks"][0]["checks"][0]["argv"] = ["ruff check . && pytest"]
        self._assert_no_writes(data, "shell operator in argv")

    def test_string_check_command_fails_closed(self) -> None:
        data = self._input()
        data["technology_stacks"][0]["checks"][0]["argv"] = "ruff check ."
        self._assert_no_writes(data, "argv must be a list")

    def test_unapproved_task_type_fails_closed(self) -> None:
        data = self._input()
        data["task_routing"][0]["task_type"] = "deployment"
        self._assert_no_writes(data, "unapproved task type")

    def test_graphify_enabled_without_wrapper_source_fails_closed(self) -> None:
        data = self._input()
        data["graphify"]["wrapper_source"] = None
        self._assert_no_writes(data, "missing wrapper source")

    def test_unresolved_wrapper_source_fails_closed(self) -> None:
        data = self._input()
        data["graphify"]["wrapper_source"] = str(self.wrapper_src / "does-not-exist")
        self._assert_no_writes(data, "wrapper source does not resolve")

    def test_report_path_outside_project_fails_closed(self) -> None:
        before = _snapshot(self.project)
        with self.assertRaises(SetupError):
            self._run(self._input(), report="../escape-report.json")
        self.assertEqual(_snapshot(self.project), before)

    # -- Graphify disabled ---------------------------------------------

    def test_graphify_disabled_writes_no_graphify_tree(self) -> None:
        data = self._input(graphify={"enabled": False})
        self._run(data)

        self.assertFalse((self.project / "tools" / "graphify").exists())
        self.assertFalse((self.project / ".gitignore").exists())
        integrations = json.loads(
            (self.project / "tools/feature-pipeline/config/integrations.json").read_text("utf-8")
        )
        self.assertNotIn("graphify", integrations)

    # -- portable-core / no-shell-out guarantees (AC-5) ---------------

    def test_portable_core_is_untouched(self) -> None:
        core = self.project / "feature-pipeline-skill"
        before = _snapshot(core)
        self._run(self._input())
        self.assertEqual(_snapshot(core), before)

    def test_written_files_stay_within_tools_and_gitignore(self) -> None:
        report = self._run(self._input())
        for rel in report["written_files"]:
            self.assertTrue(
                rel == ".gitignore" or rel.startswith("tools/"),
                rel,
            )

    def test_generator_module_never_shells_out(self) -> None:
        source = Path(setup_project.__file__).read_text(encoding="utf-8")
        for banned in (
            "import subprocess",
            "subprocess.",
            "os.system",
            "os.popen",
            "os.exec",
            "os.spawn",
            "pty.",
            "__import__(",
        ):
            self.assertNotIn(banned, source, banned)

    def test_report_records_no_forbidden_commands(self) -> None:
        report = self._run(self._input())
        for command in report.get("commands", []):
            joined = " ".join(command["argv"])
            self.assertNotIn("install", joined)
            self.assertNotIn("commit", joined)
            self.assertNotIn("push", joined)


if __name__ == "__main__":
    unittest.main()
