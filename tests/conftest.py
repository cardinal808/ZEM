"""Test setup.

The core is loaded as the stand-alone package ``zem_core`` straight from
``custom_components/zem/core``, so the core tests do not need Home Assistant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "custom_components" / "zem" / "core"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


sys.path.insert(0, str(ROOT))
import sim  # noqa: E402,F401  (loads the core as zem_core)


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES / f"report_{name}.json").open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


@pytest.fixture
def report_raw() -> Any:
    return load_fixture
