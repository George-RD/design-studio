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
    def __init__(
        self,
        *,
        extra_file_role: str | None = None,
        invalid_bundle: bool = False,
        blocked_role: str | None = None,
    ):
        self.calls = []
        self.packets = {}
        self.extra_file_role = extra_file_role
        self.invalid_bundle = invalid_bundle
        self.blocked_role = blocked_role
        self.assignment_present_at_explore = False

    def __call__(self, invocation):
        if invocation.role == self.blocked_role:
            raise RuntimeError("fake blocked role must be replaced by test wrapper")
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
            content = (
                "<!doctype html><main>invalid</main>"
                if self.invalid_bundle
                else self.local_index()
            )
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
        return "\n\n".join(
            f"## {heading}\nSpecific {heading.lower()} contract." for heading in headings
        )

    @staticmethod
    def local_index() -> str:
        return """<!doctype html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; connect-src 'none'; form-action 'none'; frame-src 'none'; object-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; media-src 'self' data:">
</head>
<body><main>Generated</main></body>
</html>"""


class FakeMechanicalRunner:
    def __init__(self, lane_module, *, fail: bool = False):
        self.lane = lane_module
        self.fail = fail
        self.calls = []

    def __call__(self, invocation):
        self.calls.append(invocation)
        if self.fail:
            raise self.lane.ContractError("synthetic mechanical failure")
        self.assert_site(invocation.site_dir)
        return {
            "status": "passed",
            "provider": invocation.provider,
            "coverage": {"source": "complete", "browser": "pending"},
            "version": "3.5.0" if invocation.provider == "impeccable" else "1.5.0-fallback",
            "revision": (
                invocation.impeccable_revision
                if invocation.provider == "impeccable"
                else invocation.design_revision
            ),
            "findings": {"total": 0, "primary": 0, "advisory": 0},
        }

    @staticmethod
    def assert_site(site_dir: Path) -> None:
        if not (site_dir / "index.html").is_file():
            raise AssertionError("mechanical runner did not receive the staged site")


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
        tool_sources = {
            "design-studio-current": "George-RD/design-studio@design-sha",
            "design-studio-impeccable": (
                "George-RD/design-studio@design-sha + "
                "pbakaus/impeccable@impeccable-sha"
            ),
            "impeccable-alone": "pbakaus/impeccable@impeccable-sha",
        }
        (run / "run.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "runId": f"m0-fixture-a-{lane}",
                    "status": "running",
                    "fixture": {"id": "fixture-a", "version": 1},
                    "lane": {"id": lane},
                    "tool": {
                        "name": lane,
                        "version": "test",
                        "source": tool_sources[lane],
                    },
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
            impeccable / "cli/bin/cli.js": "#!/usr/bin/env node\n",
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
        mechanical = FakeMechanicalRunner(self.lane)
        report = self.lane.run_generation(
            repo_root=repo,
            impeccable_root=impeccable,
            run_dir=run,
            design_revision="design-sha",
            impeccable_revision="impeccable-sha",
            role_runner=fake,
            mechanical_runner=mechanical,
        )
        return report, run, mechanical

    def test_design_studio_lane_runs_generation_and_fallback_preflight(self) -> None:
        fake = FakeRoleRunner()
        report, run, mechanical = self.run_generation("design-studio-current", fake)
        self.assertEqual(["explore", "direct", "builder"], fake.calls)
        self.assertTrue(fake.assignment_present_at_explore)
        self.assertEqual("generated", report["status"])
        self.assertEqual("fallback", report["mechanical"]["provider"])
        self.assertEqual(1, len(mechanical.calls))
        self.assertEqual("fallback", mechanical.calls[0].provider)
        self.assertFalse(mechanical.calls[0].output_dir_existed)
        self.assertTrue((run / "output" / "index.html").is_file())
        self.assertEqual(
            report,
            json.loads(
                (run / "evidence" / "generation-report.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        self.assertNotIn("baselineSource", fake.packets["explore"])
        self.assertNotIn("baselineSource", fake.packets["direct"])
        self.assertIn("baselineSource", fake.packets["builder"])
        self.assertIn("designDescription", fake.packets["builder"])

    def test_enabled_lane_invokes_pinned_impeccable_without_prompt_leakage(self) -> None:
        fake = FakeRoleRunner()
        report, _, mechanical = self.run_generation("design-studio-impeccable", fake)
        self.assertEqual(["explore", "direct", "builder"], fake.calls)
        self.assertEqual("impeccable", report["mechanical"]["provider"])
        self.assertEqual(1, len(mechanical.calls))
        invocation = mechanical.calls[0]
        self.assertEqual("impeccable", invocation.provider)
        self.assertEqual("impeccable-sha", invocation.impeccable_revision)
        self.assertEqual("3.5.0", json.loads((invocation.impeccable_root / "package.json").read_text())["version"])
        builder_packet = json.dumps(fake.packets["builder"])
        self.assertNotIn("IMPECCABLE_CORE", builder_packet)
        self.assertEqual("impeccable", fake.packets["builder"]["mechanicalProvider"])

    def test_standalone_impeccable_lane_is_one_isolated_role(self) -> None:
        fake = FakeRoleRunner()
        report, run, mechanical = self.run_generation("impeccable-alone", fake)
        self.assertEqual(["impeccable"], fake.calls)
        serialized = json.dumps(fake.packets["impeccable"])
        self.assertIn("IMPECCABLE_CORE", serialized)
        self.assertNotIn("DIRECTOR_GUIDANCE", serialized)
        self.assertEqual("generated", report["status"])
        self.assertEqual([], mechanical.calls)
        self.assertIsNone(report["mechanical"])
        self.assertTrue((run / "output" / "index.html").is_file())

    def test_generation_fails_closed_on_role_bundle_and_mechanical_failures(self) -> None:
        cases = (
            (FakeRoleRunner(extra_file_role="builder"), FakeMechanicalRunner(self.lane), "builder"),
            (FakeRoleRunner(invalid_bundle=True), FakeMechanicalRunner(self.lane), "validate-bundle"),
            (FakeRoleRunner(), FakeMechanicalRunner(self.lane, fail=True), "mechanical-preflight"),
        )
        for role_runner, mechanical_runner, expected_step in cases:
            with self.subTest(step=expected_step):
                temporary, repo, impeccable, run = self.make_run()
                self.addCleanup(temporary.cleanup)
                with self.assertRaises(self.lane.ContractError):
                    self.lane.run_generation(
                        repo_root=repo,
                        impeccable_root=impeccable,
                        run_dir=run,
                        design_revision="design-sha",
                        impeccable_revision="impeccable-sha",
                        role_runner=role_runner,
                        mechanical_runner=mechanical_runner,
                    )
                report = json.loads(
                    (run / "evidence" / "generation-report.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("failed", report["status"])
                self.assertEqual(expected_step, report["error"]["step"])
                self.assertEqual([], list((run / "output").iterdir()))

    def test_blocked_role_preserves_report_and_classification(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)

        def blocked(_invocation):
            raise self.lane.CapabilityBlocked("synthetic policy block")

        with self.assertRaises(self.lane.CapabilityBlocked):
            self.lane.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                design_revision="design-sha",
                impeccable_revision="impeccable-sha",
                role_runner=blocked,
                mechanical_runner=FakeMechanicalRunner(self.lane),
            )
        report = json.loads(
            (run / "evidence" / "generation-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked", report["status"])
        self.assertEqual("capability-blocked", report["error"]["kind"])
        self.assertEqual([], list((run / "output").iterdir()))

    def test_blocked_classification_survives_cleanup_failure(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)

        def blocked(_invocation):
            raise self.lane.CapabilityBlocked("synthetic policy block")

        with mock.patch.object(
            self.lane,
            "_reset_output",
            side_effect=self.lane.ContractError("synthetic cleanup failure"),
        ):
            with self.assertRaises(self.lane.CapabilityBlocked):
                self.lane.run_generation(
                    repo_root=repo,
                    impeccable_root=impeccable,
                    run_dir=run,
                    design_revision="design-sha",
                    impeccable_revision="impeccable-sha",
                    role_runner=blocked,
                    mechanical_runner=FakeMechanicalRunner(self.lane),
                )
        report = json.loads(
            (run / "evidence" / "generation-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked", report["status"])
        self.assertEqual("capability-blocked", report["error"]["kind"])
        self.assertIn("cleanup failed", report["error"]["message"])

    def test_missing_token_is_recorded_as_blocked_generation(self) -> None:
        temporary, repo, impeccable, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        runner = self.lane.CopilotRoleRunner(
            token="",
            command_runner=lambda *_args, **_kwargs: self.fail("CLI must not run"),
        )
        with self.assertRaises(self.lane.CapabilityBlocked):
            self.lane.run_generation(
                repo_root=repo,
                impeccable_root=impeccable,
                run_dir=run,
                design_revision="design-sha",
                impeccable_revision="impeccable-sha",
                role_runner=runner,
                mechanical_runner=FakeMechanicalRunner(self.lane),
            )
        report = json.loads(
            (run / "evidence" / "generation-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked", report["status"])
        self.assertIn("GITHUB_TOKEN", report["error"]["message"])

    def adapter_invocation(self, run: Path, output_name: str = "directions.json"):
        workspace = run / "evidence" / f"adapter-{output_name}-workspace"
        evidence = run / "evidence" / f"adapter-{output_name}-evidence"
        workspace.mkdir()
        (workspace / "packet.json").write_text("{}", encoding="utf-8")
        invocation = self.lane.RoleInvocation(
            role="explore",
            run_dir=run,
            workspace=workspace,
            evidence_dir=evidence,
            output_name=output_name,
            prompt=f"Read packet.json and create {output_name}.",
        )
        return workspace, evidence, invocation

    def successful_events(self, output_name: str, model: str = "fake-model"):
        return [
            {"type": "assistant.turn_start", "data": {"turnId": "t1", "model": model}},
            {"type": "tool.execution_start", "data": {"toolCallId": "r1", "toolName": "view", "turnId": "t1", "arguments": {"path": "packet.json"}}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "r1", "toolName": "view", "turnId": "t1", "success": True}},
            {"type": "tool.execution_start", "data": {"toolCallId": "w1", "toolName": "create", "turnId": "t1", "arguments": {"path": output_name}}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "w1", "toolName": "create", "turnId": "t1", "success": True}},
            {"type": "assistant.turn_end", "data": {"turnId": "t1"}},
        ]

    def test_live_adapter_uses_trusted_workspace_timeout_and_exact_file_tools(self) -> None:
        temporary, _, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        workspace, evidence, invocation = self.adapter_invocation(run)
        observed = {}

        def command_runner(command, *, cwd, env, **kwargs):
            observed.update({"command": command, "cwd": cwd, "env": env, **kwargs})
            (cwd / "directions.json").write_text(
                json.dumps({"directions": []}), encoding="utf-8"
            )
            return self.lane.capability.CommandOutcome(
                exit_code=0,
                stdout="\n".join(
                    json.dumps(event)
                    for event in self.successful_events("directions.json")
                )
                + "\n",
                stderr="",
            )

        adapter = self.lane.CopilotRoleRunner(
            token="secret-token",
            copilot_bin="copilot",
            copilot_version="1.0.74",
            model="auto",
            command_runner=command_runner,
        )
        with mock.patch.dict(
            os.environ,
            {"AWS_SECRET_ACCESS_KEY": "must-not-leak"},
            clear=False,
        ):
            result = adapter(invocation)
        command_text = " ".join(observed["command"])
        self.assertIn("--available-tools=view,create", command_text)
        self.assertIn("--allow-tool=read,write", command_text)
        self.assertIn("--deny-tool=shell,url,memory", command_text)
        self.assertNotIn("secret-token", command_text)
        self.assertEqual("secret-token", observed["env"]["GITHUB_TOKEN"])
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", observed["env"])
        self.assertEqual(self.lane.capability.COMMAND_TIMEOUT_SECONDS, observed["timeout_seconds"])
        self.assertEqual(workspace.resolve(), observed["cwd"])
        self.assertEqual("fake-model", result["resolvedModel"])
        self.assertEqual(["packet.json"], result["toolReceipt"]["read"])
        self.assertEqual(["directions.json"], result["toolReceipt"]["written"])
        for path in evidence.rglob("*"):
            if path.is_file():
                self.assertNotIn("secret-token", path.read_text(encoding="utf-8"))

    def test_live_adapter_rejects_explicit_model_fallback(self) -> None:
        temporary, _, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        workspace, _, invocation = self.adapter_invocation(run, "directions.json")

        def command_runner(_command, *, cwd, env, timeout_seconds):
            del env, timeout_seconds
            (cwd / "directions.json").write_text(
                json.dumps({"directions": []}), encoding="utf-8"
            )
            return self.lane.capability.CommandOutcome(
                exit_code=0,
                stdout="\n".join(
                    json.dumps(event)
                    for event in self.successful_events(
                        "directions.json", model="fallback-model"
                    )
                )
                + "\n",
                stderr="",
            )

        adapter = self.lane.CopilotRoleRunner(
            token="secret-token",
            model="requested-model",
            command_runner=command_runner,
        )
        with self.assertRaisesRegex(self.lane.ContractError, "requested-model"):
            adapter(invocation)
        self.assertTrue((workspace / "directions.json").is_file())

    def test_live_adapter_redacts_token_from_cli_failure_and_reportable_error(self) -> None:
        temporary, _, _, run = self.make_run()
        self.addCleanup(temporary.cleanup)
        _, evidence, invocation = self.adapter_invocation(run, "directions.json")

        def command_runner(_command, *, cwd, env, timeout_seconds):
            del cwd, env, timeout_seconds
            return self.lane.capability.CommandOutcome(
                exit_code=1,
                stdout="",
                stderr="request failed with secret-token",
            )

        adapter = self.lane.CopilotRoleRunner(
            token="secret-token",
            command_runner=command_runner,
        )
        with self.assertRaises(self.lane.ContractError) as raised:
            adapter(invocation)
        self.assertNotIn("secret-token", str(raised.exception))
        for path in evidence.rglob("*"):
            if path.is_file():
                self.assertNotIn("secret-token", path.read_text(encoding="utf-8"))

    def test_pinned_impeccable_source_runner_records_findings_and_exact_command(self) -> None:
        temporary, _, impeccable, run = self.make_run("design-studio-impeccable")
        self.addCleanup(temporary.cleanup)
        site = run / "evidence" / "staged-site"
        site.mkdir()
        (site / "index.html").write_text(FakeRoleRunner.local_index(), encoding="utf-8")
        evidence = run / "evidence" / "mechanical-live"
        observed = {}

        def command_runner(command, *, cwd, env, **kwargs):
            observed.update({"command": command, "cwd": cwd, "env": env, **kwargs})
            findings = [
                {"antipattern": "nested-cards", "severity": "primary"},
                {"antipattern": "em-dash", "severity": "advisory", "advisory": True},
            ]
            return self.lane.capability.CommandOutcome(
                exit_code=2,
                stdout=json.dumps(findings),
                stderr="",
            )

        runner = self.lane.ComparisonMechanicalRunner(
            node_bin="node",
            command_runner=command_runner,
        )
        invocation = self.lane.MechanicalInvocation(
            provider="impeccable",
            run_dir=run,
            site_dir=site,
            output_dir_existed=False,
            evidence_dir=evidence,
            impeccable_root=impeccable,
            design_revision="design-sha",
            impeccable_revision="impeccable-sha",
        )
        result = runner(invocation)
        self.assertEqual("passed", result["status"])
        self.assertEqual("impeccable", result["provider"])
        self.assertEqual("3.5.0", result["version"])
        self.assertEqual("impeccable-sha", result["revision"])
        self.assertEqual({"total": 2, "primary": 1, "advisory": 1}, result["findings"])
        self.assertEqual(
            [
                "node",
                str((impeccable / "cli/bin/cli.js").resolve()),
                "detect",
                "--json",
                str(site.resolve()),
            ],
            observed["command"],
        )
        self.assertNotIn("npx", observed["command"])
        self.assertEqual(site.resolve(), observed["cwd"])
        self.assertEqual(
            self.lane.capability.COMMAND_TIMEOUT_SECONDS,
            observed["timeout_seconds"],
        )
        self.assertEqual(
            json.loads((evidence / "findings.json").read_text(encoding="utf-8")),
            json.loads(observed["command"] and json.dumps([
                {"antipattern": "nested-cards", "severity": "primary"},
                {"antipattern": "em-dash", "severity": "advisory", "advisory": True},
            ])),
        )


if __name__ == "__main__":
    unittest.main()
