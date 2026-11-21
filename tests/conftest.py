"""Test setup.

The core is loaded as the stand-alone package ``zem_core`` straight from
``custom_components/zem/core``, so the core tests do not need Home Assistant.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "custom_components" / "zem" / "core"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_core() -> None:
    if "zem_core" in sys.modules:
        return
    spec = importlib.util.spec_from_file_location("zem_core", CORE_DIR / "__init__.py", submodule_search_locations=[str(CORE_DIR)])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["zem_core"] = module
    spec.loader.exec_module(module)


_load_core()


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES / f"report_{name}.json").open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


@pytest.fixture
def report_raw() -> Any:
    return load_fixture
