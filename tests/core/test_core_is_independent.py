"""The core must not depend on Home Assistant (ARCHITECTUUR §1)."""

from __future__ import annotations

import ast

from conftest import CORE_DIR


def test_no_home_assistant_imports() -> None:
    offenders: list[str] = []
    for path in CORE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            offenders += [f"{path.name}: {n}" for n in names if n.split(".")[0] == "homeassistant"]
    assert offenders == []
