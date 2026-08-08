from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_copilot_comparison_lane.py"


def load_lane_runner():
    spec = importlib.util.spec_from_file_location("run_copilot_comparison_lane", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load comparison lane runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRoleRunner:
    def __init__(self, *, extra_file_role: str | None = None, invalid_bundle: bool = False):
        self.calls = []
        self.packets = {}
        self.extra_file_role = extra_file_role
        self.invalid_bundle = invalid_bundle
        self.assignment_present_at_explore = False

    def __call__(self, invocation):
        packet_path = invocation.workspace / "packet.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        self.calls.append(invocation.role)
        self.packets[invocation.role] = packet
        if invocation.role == "explore":
            self.assignment_present_at_explore = (
                invocation.run_dir / "evidence" / "direction-assignment.json"
            ).is_file()
            output = {
                "directions": [
                    {"id": f"direction-{index}", "name": name, "concept": name}
                    for index, name in enumerate(("A", "B", "C"), start=1)
                ]
            }
            (invocation.workspace / invocation.output_name).write_text(
                json.dumps(output), encoding="utf-8"
            )
        elif invocation.role == "direct":
            (invocation.workspace / invocation.output_name).write_text(
                self.design_description(), encoding="utf-8"
            )
        elif invocation.role in {"builder", "impeccable"}:
            content = "<!doctype html><main>invalid</main>" if self.invalid_bundle else self.local_index()
            (invocation.workspace / invocation.output_name).write_text(
                json.dumps({"files": [{"path": "index.html", "content": content}]}),
                encoding="utf-8",
            )
        else:
            raise AssertionError(f"unexpected role: {invocation.role}")
        if invocation.role == self.extra_file_role:
            (invocation.workspace / "unexpected.txt").write_text("escape", encoding="utf-8")
        return {
            "status": "passed",
            "resolvedModel": "fake-model",
            "toolReceipt": {
                "read": ["packet.json"],
                "written": [invocation.output_name],
            },
        }

    @staticmethod
    def design_description() -> str:
        headings = (
            "THESIS",
            "FIRST VIEWPORT",
            "VISITOR PATH",
            "VISUAL WORLD",
            "TYPOGRAPHY",
            "COLOUR",
            "SPATIAL RHYTHM",
            "MOTION",
            "INTERACTION STATES",
            "RESPONSIVE BEHAVIOUR",
            "SIGNATURE MOMENT",
            "ANTI-GOALS",
        )
        return "\n\n".join(f"## {heading}\nSpecific {heading.lower()} contract." for heading in headings)

    @staticmethod
    def local_index() -> str:
        return """<!doctype html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; object-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; media-src 'self' data:">
</head>
<body><main>Generated</main></body>
</html>"""


class CopilotComparisonLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lane = load_lane_runner()

    def make_run(self, lane: str = "design-studio-current"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        run = root / "run"
        repo = root / "repo"
        impeccable = root / "impeccable"
        for directory in (run / "input", run / "work", run / "output", run / "evidence"):
            directory.mkdir(parents=True)
        (run / "input" / "brief.md").write_text("PUBLIC_BRIEF", encoding="utf-8")
        (run / "input" / "acceptance.json").write_text(
            json.dumps({"mustDeliver": ["A usable local page"]}), encoding="utf-8"
        )
        (run / "input" / "fixture.json").write_text(
            json.dumps(
                {
                    "id": "fixture-a",
                    "version": 1,
                    "kind": "new-marketing-surface",
                    "brief": "brief.md",
                    "acceptance": "acceptance.json",
                    "outputContract": {"entrypoint": "index.html"},
                }
            ),
            encoding="utf-8",
        )
        (run / "work" / "index.html").write_text("PRIVATE_SOURCE", encoding="utf-8")
        (run / "run.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "runId": f"m0-fixture-a-{lane}",
                    "status": "running",
                    "fixture": {"id": "fixture-a", "version": 1},
                    "lane": {"id": lane},
                    "tool": {"name": lane, "version": "test", "source": "sha"},
                }
            ),
            encoding="utf-8",
        )
        for path, text in {
            repo / "skills/design-studio/agents/design-agent.md": "DIRECTOR_GUIDANCE",
            repo / "skills/design-studio/references/generation.md": "BUILDER_GUIDANCE",
            impeccable / "skill/SKILL.src.md": "IMPECCABLE_CORE",
            impeccable / "skill/reference/new-work.md": "IMPECCABLE_NEW",
            impeccable / "skill/reference/craft-floor.md": "IMPECCABLE_CRAFT",
        }.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (impeccable / "package.json").write_text(
            json.dumps({"name": "impeccable", "version": "3.5.0"}), encoding="utf-8"
        )
        return temporary, repo, impeccable, run

    def run_generation(self, lane: str, fake: FakeRoleRunner):
        temporary, repo, impeccable, run = self.make_run(lane)
        self.addCleanup(temporary.cleanup)
        report = self.lane.run_generation(
            repo_root=repo,
            impeccable_root=impeccable,
            run_dir=run,
            design_revision="design-sha",
            impeccable_revision="impeccable-sha",
            role_runner=fake,
        )
        return report, run

    def test_design_studio_lane_runs_explore_direct_builder_transaction(self) -> None:
        fake = FakeRoleRunner()
        report, run = self.run_generation("design-studio-current", fake)
        self.assertEqual(["explore", "direct", "builder"], fake.calls)
        self.assertTrue(fake.assignment_present_at_explore)
        self.assertEqual("generated", report["status"])
        self.assertEqual("fallback", report["lane"]["mechanicalProvider"])
        self.assertTrue((run / "output" / "index.html").is_file())
        self.assertEqual(
            report,
            json.loads((run / "evidence" / "generation-report.json").read_text(encoding="utf-8")),
        )
        self.assertNotIn("baselineSource", fake.packets["explore"])
        self.assertNotIn("baselineSource", fake.packets["direct"])
        self.assertIn("baselineSource", fake.packets["builder"])
        self.assertIn("designDescription", fake.packets["builder"])

    def test_enabled_lane_changes_mechanics_without_leaking_upstream_guidance(self) -> None:
        fake = FakeRoleRunner()
        report, _ = self.run_generation("design-studio-impeccable", fake)
        self.assertEqual(["explore", "direct", "builder"], fake.calls)
        self.assertEqual("impeccable", report["lane"]["mechanicalProvider"])
        builder_packet = json.dumps(fake.packets["builder"])
        self.assertNotIn("IMPECCABLE_CORE", builder_packet)
        self.assertEqual("impeccable", fake.packets["builder"]["mechanicalProvider"])

    def test_standalone_impeccable_lane_is_one_isolated_role(self) -> None:
        fake = FakeRoleRunner()
        report, run = self.run_generation("impeccable-alone", fake)
        self.assertEqual(["impeccable"], fake.calls)
        serialized = json.dumps(fake.packets["impeccable"])
        self.assertIn("IMPECCABLE_CORE", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertEqual("generated", report["status"])
        self.assertTrue((run / "output" / "index.html").is_file())

    def test_generation_fails_closed_on_extra_role_files(self) -> None:
        fake = FakeRoleRunner(extra_file_role="builder")
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(self.lane.ContractError):
            self.lane.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                design_revision="design-sha",
                impeccable_revision="impeccable-sha",
                role_runner=fake,
            )
        report = json.loads(
            (run / "evidence" / "generation-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", report["status"])
        self.assertEqual("builder", report["error"]["step"])
        self.assertEqual([], list((run / "output").iterdir()))

    def test_generation_fails_closed_on_invalid_bundle_without_partial_output(self) -> None:
        fake = FakeRoleRunner(invalid_bundle=True)
        temporary, repo, impeccable, run = self.make_run("impeccable-alone")
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(self.lane.ContractError):
            self.lane.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                design_revision="design-sha",
                impeccable_revision="impeccable-sha",
                role_runner=fake,
            )
        self.assertEqual([], list((run / "output").iterdir()))
        report = json.loads(
            (run / "evidence" / "generation-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("validate-bundle", report["error"]["step"])

    def test_live_adapter_uses_trusted_workspace_and_exact_file_tools(self) -> None:
        temporary, _, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        workspace = run / "evidence" / "adapter-workspace"
        evidence = run / "evidence" / "adapter-evidence"
        workspace.mkdir()
        (workspace / "packet.json").write_text("{}", encoding="utf-8")
        observed = {}

        def command_runner(command, *, cwd, env, timeout_seconds):
            observed.update(
                {
                    "command": command,
                    "cwd": cwd,
                    "env": env,
                    "timeout": timeout_seconds,
                }
            )
            (cwd / "directions.json").write_text(
                json.dumps({"directions": []}), encoding="utf-8"
            )
            events = [
                {"type": "assistant.turn_start", "data": {"turnId": "t1", "model": "fake-model"}},
                {"type": "tool.execution_start", "data": {"toolCallId": "r1", "toolName": "view", "turnId": "t1", "arguments": {"path": "packet.json"}}},
                {"type": "tool.execution_complete", "data": {"toolCallId": "r1", "toolName": "view", "turnId": "t1", "success": True}},
                {"type": "tool.execution_start", "data": {"toolCallId": "w1", "toolName": "create", "turnId": "t1", "arguments": {"path": "directions.json"}}},
                {"type": "tool.execution_complete", "data": {"toolCallId": "w1", "toolName": "create", "turnId": "t1", "success": True}},
                {"type": "assistant.turn_end", "data": {"turnId": "t1"}},
            ]
            return self.lane.capability.CommandOutcome(
                exit_code=0,
                stdout="\n".join(json.dumps(event) for event in events) + "\n",
                stderr="",
            )

        adapter = self.lane.CopilotRoleRunner(
            token="secret-token",
            copilot_bin="copilot",
            copilot_version="1.0.74",
            model="auto",
            command_runner=command_runner,
        )
        invocation = self.lane.RoleInvocation(
            role="explore",
            run_dir=run,
            workspace=workspace,
            evidence_dir=evidence,
            output_name="directions.json",
            prompt="Read packet.json and create directions.json.",
        )
        with mock.patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "must-not-leak"}, clear=False):
            result = adapter(invocation)
        command_text = " ".join(observed["command"])
        self.assertIn("--available-tools=view,create", command_text)
        self.assertIn("--allow-tool=read,write", command_text)
        self.assertIn("--deny-tool=shell,url,memory", command_text)
        self.assertNotIn("secret-token", command_text)
        self.assertEqual("secret-token", observed["env"]["GITHUB_TOKEN"])
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", observed["env"])
        self.assertEqual(workspace.resolve(), observed["cwd"])
        self.assertEqual("fake-model", result["resolvedModel"])
        self.assertEqual(["packet.json"], result["toolReceipt"]["read"])
        self.assertEqual(["directions.json"], result["toolReceipt"]["written"])


if __name__ == "__main__":
    unittest.main()
