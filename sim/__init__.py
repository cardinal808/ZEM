"""ZEPHYR simulator.

Uses the real core (``custom_components/zephyr/core``), loaded as the
stand-alone package ``zephyr_core`` so Home Assistant is not needed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "zephyr" / "core"


def _load_core() -> None:
    if "zephyr_core" in sys.modules:
        return
    spec = importlib.util.spec_from_file_location("zephyr_core", CORE_DIR / "__init__.py", submodule_search_locations=[str(CORE_DIR)])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["zephyr_core"] = module
    spec.loader.exec_module(module)


_load_core()
