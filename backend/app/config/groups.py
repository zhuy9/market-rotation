from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_GROUPS_PATH = Path(__file__).parent / "groups.yaml"


def load_groups(path: Path = DEFAULT_GROUPS_PATH) -> dict[str, list[str]]:
    """Defensive/cyclical sector membership, kept in config per PRD section 24."""
    return yaml.safe_load(path.read_text())
