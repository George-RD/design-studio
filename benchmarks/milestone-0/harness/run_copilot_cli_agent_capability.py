from pathlib import Path

_CORE_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "run_copilot_cli_agent_capability.py"
)
globals()["__file__"] = str(_CORE_PATH)
exec(
    compile(_CORE_PATH.read_bytes(), str(_CORE_PATH), "exec"),
    globals(),
    globals(),
)
