"""Guardrails for skill packaging compliance.

Enforces:
  - canonical SKILL.md exists with only agentskills.io-compliant frontmatter
  - multi-host symlinks point at the canonical path
  - plugin manifests (.claude-plugin, .codex-plugin) agree on name + version
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).parent.parent
CANONICAL = REPO / "skills" / "vibe-sci"
SKILL_MD = CANONICAL / "SKILL.md"

# Per https://agentskills.io/specification — only these frontmatter keys are
# first-class. Everything else must sit inside `metadata:`.
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

HOST_SYMLINK_DIRS = [
    ".claude/skills",
    ".agents/skills",
    ".gemini/skills",
    ".opencode/skills",
]


def _parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    _, fm, _ = text.split("---\n", 2)
    return yaml.safe_load(fm) or {}


def test_canonical_skill_md_exists() -> None:
    assert SKILL_MD.is_file(), f"canonical SKILL.md missing at {SKILL_MD}"


def test_frontmatter_has_required_keys() -> None:
    fm = _parse_frontmatter(SKILL_MD)
    assert fm.get("name") == "vibe-sci"
    assert isinstance(fm.get("description"), str) and len(fm["description"]) <= 1024


def test_frontmatter_has_no_unknown_keys() -> None:
    fm = _parse_frontmatter(SKILL_MD)
    extra = set(fm) - ALLOWED_FRONTMATTER
    assert not extra, (
        f"non-standard frontmatter keys {sorted(extra)} — put them under `metadata:` "
        f"per agentskills.io spec"
    )


@pytest.mark.parametrize("host_dir", HOST_SYMLINK_DIRS)
def test_host_symlink_points_at_canonical(host_dir: str) -> None:
    link = REPO / host_dir / "vibe-sci"
    assert link.is_symlink(), f"{link} must be a symlink"
    resolved = link.resolve()
    assert resolved == CANONICAL.resolve(), (
        f"{link} → {resolved}, expected {CANONICAL.resolve()}"
    )


def test_plugin_manifests_agree_on_name_and_version() -> None:
    claude = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((REPO / ".codex-plugin" / "plugin.json").read_text())
    assert claude["name"] == codex["name"] == "vibe-sci"
    assert claude["version"] == codex["version"]


def test_claude_plugin_references_canonical_skill_path() -> None:
    claude = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
    assert "./skills/vibe-sci" in claude.get("skills", []), (
        ".claude-plugin/plugin.json must list `./skills/vibe-sci` in its skills array "
        "so npx skills groups the skill under this plugin"
    )
