from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_copilot_cli_agent_capability_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_copilot_cli_trusted_workspace", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotCliTrustedWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_config_trusts_only_the_role_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "copilot-home" / "director"
            workspace = root / "workspaces" / "director"
            workspace.mkdir(parents=True)

            config_path = self.module.write_trusted_workspace_config(home, workspace)
            config = json.loads(config_path.read_text())

        self.assertEqual([str(workspace.resolve())], config["trustedFolders"])
        self.assertEqual({"trustedFolders"}, set(config))

    def test_existing_unrelated_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "copilot-home" / "builder"
            workspace = root / "workspaces" / "builder"
            home.mkdir(parents=True)
            workspace.mkdir(parents=True)
            (home / "config.json").write_text(
                json.dumps({"trustedFolders": ["/unexpected"]}) + "\n"
            )

            with self.assertRaisesRegex(self.module.core.ContractError, "already exists"):
                self.module.write_trusted_workspace_config(home, workspace)


if __name__ == "__main__":
    unittest.main()
