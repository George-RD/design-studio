from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
STRESS_PATH = (
    ROOT
    / "benchmarks"
    / "milestone-0"
    / "harness"
    / "run_browser_capability_stress.py"
)


def load_stress_module():
    name = "browser_stress_timeout_evidence_test"
    spec = importlib.util.spec_from_file_location(name, STRESS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {STRESS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BrowserStressTimeoutEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stress = load_stress_module()

    def test_timeout_bytes_remain_json_serializable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "site"
            root.mkdir()
            output = Path(temporary) / "evidence"
            timeout = subprocess.TimeoutExpired(
                cmd=["node", "browser"],
                timeout=1,
                output=b"prefix-\xffstdout",
                stderr=b"prefix-\xfestderr",
            )
            with mock.patch.object(
                self.stress.subprocess,
                "run",
                side_effect=timeout,
            ):
                attempt = self.stress.run_attempt(
                    index=1,
                    root=root,
                    output_dir=output,
                    entrypoint="index.html",
                    width=390,
                    height=844,
                    expected_url=self.stress.DEFAULT_EXPECTED_URL,
                    timeout_seconds=1,
                )

            evidence = self.stress.build_evidence(
                attempts=[attempt],
                root=root,
                expected_url=self.stress.DEFAULT_EXPECTED_URL,
            )
            encoded = json.dumps(evidence)

        self.assertEqual("blocked", attempt["status"])
        self.assertEqual("stress-timeout", attempt["phase"])
        self.assertIsInstance(attempt["stdout"], str)
        self.assertIsInstance(attempt["stderr"], str)
        self.assertIn("stdout", encoded)
        self.assertEqual("failed", evidence["status"])


if __name__ == "__main__":
    unittest.main()
