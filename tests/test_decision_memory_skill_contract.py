import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src/decisionmemory/mcp_server.py"
SKILL = ROOT / "decisionmemory-plugin/skills/decision-memory/SKILL.md"
PLUGIN = ROOT / "decisionmemory-plugin/.claude-plugin/plugin.json"
PYPROJECT = ROOT / "pyproject.toml"


def _registered_tools() -> dict[str, list[str]]:
    tree = ast.parse(SERVER.read_text())
    tools = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "mcp"
            and dec.func.attr == "tool"
            for dec in node.decorator_list
        ):
            continue
        tools[node.name] = [arg.arg for arg in node.args.args]
    return tools


def test_skill_matches_package_version_and_registered_tools():
    skill = SKILL.read_text()
    plugin = json.loads(PLUGIN.read_text())
    package_version = re.search(
        r'^version = "([^"]+)"$', PYPROJECT.read_text(), re.MULTILINE
    ).group(1)
    tools = _registered_tools()

    assert plugin["version"] == package_version
    assert f"Protocol v{package_version}" in skill
    assert f"registers **{len(tools)} MCP tools**" in skill
    for name, parameters in tools.items():
        assert f"`{name}`" in skill
        signature_row = next(
            line
            for line in skill.splitlines()
            if line.startswith(f"| `{name}` | `(")
        )
        for parameter in parameters:
            assert parameter in signature_row


def test_skill_describes_actual_owm_and_remember_decision_contract():
    skill = SKILL.read_text()
    skill_lower = skill.lower()

    assert "score = Q × Sim × Rec × Conf × Aff" in skill
    assert "Power law" in skill
    assert "exponential decay" not in skill
    assert "writes to all 5 memory layers" not in skill
    assert "`remember_decision` does **not** write prospective memory" in skill
    for layer in ("episodic", "semantic", "procedural", "affective", "decision_records"):
        assert layer in skill_lower
