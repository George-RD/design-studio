from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import time
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_with_deadline.py"


def load_deadline_runner():
    spec = importlib.util.spec_from_file_location(
        "run_with_deadline_test", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load deadline runner from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CopilotComparisonDeadlineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.deadline = load_deadline_runner()

    def test_child_exit_code_is_preserved(self) -> None:
        exit_code = self.deadline.run_with_deadline(
            [sys.executable, "-c", "raise SystemExit(7)"],
            timeout_seconds=5,
        )
        self.assertEqual(7, exit_code)

    def test_elapsed_deadline_returns_terminal_timeout_code(self) -> None:
        started = time.monotonic()
        exit_code = self.deadline.run_with_deadline(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout_seconds=0.1,
            kill_grace_seconds=0.1,
        )
        elapsed = time.monotonic() - started

        self.assertEqual(124, exit_code)
        self.assertLess(elapsed, 2)

    def test_invalid_deadline_is_rejected_before_launch(self) -> None:
        for value in (True, 0, -1, "5"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "positive number"):
                    self.deadline.run_with_deadline(
                        [sys.executable, "-c", "raise SystemExit(0)"],
                        timeout_seconds=value,
                    )


if __name__ == "__main__":
    unittest.main()
