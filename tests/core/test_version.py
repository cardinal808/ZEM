"""The version in manifest.json matches the newest entry in the changelog."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_version_matches_changelog() -> None:
    manifest = json.loads((ROOT / "custom_components" / "zephyr" / "manifest.json").read_text())
    newest = re.search(r"^### .*?(\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(), re.MULTILINE)
    assert newest is not None
    assert manifest["version"] == newest.group(1)
