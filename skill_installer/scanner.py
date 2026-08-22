"""Scan a source directory for skills and their dependency edges."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_FRONTMATTER_KV = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)$")
_SKILL_TOKEN = re.compile(r"/([a-zA-Z][a-zA-Z0-9-]{2,60})")
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


@dataclass
class Skill:
    name: str
    bucket: str
    dir: Path
    description: str = ""
    requires_skill: set[str] = field(default_factory=set)
    requires_file: set[Path] = field(default_factory=set)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a SKILL.md into (frontmatter dict, body). Frontmatter is a
    minimal '---' delimited key: value block - not full YAML."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text, body = parts[1], parts[2]
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        m = _FRONTMATTER_KV.match(line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm, body


def scan_source(source: Path) -> dict[str, Skill]:
    """Scan every SKILL.md under `source` and return name -> Skill.

    Bucket is the SKILL.md's grandparent-relative path under a `skills/`
    directory if one exists directly under `source`, otherwise the immediate
    parent directory name.
    """
    source = source.resolve()
    skills_root = source / "skills" if (source / "skills").is_dir() else source

    found: dict[str, Skill] = {}
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        skill_dir = skill_md.parent.resolve()
        name = skill_dir.name
        bucket = str(skill_dir.parent.relative_to(skills_root)).replace("\\", "/")
        text = skill_md.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        found[name] = Skill(
            name=name,
            bucket=bucket if bucket != "." else "",
            dir=skill_dir,
            description=fm.get("description", ""),
        )

    known_names = set(found)
    for skill in found.values():
        text = (skill.dir / "SKILL.md").read_text(encoding="utf-8")
        _, body = _parse_frontmatter(text)

        for token in _SKILL_TOKEN.findall(body):
            if token in known_names and token != skill.name:
                skill.requires_skill.add(token)

        for link in _MD_LINK.findall(body):
            if link.startswith(("http://", "https://")):
                continue
            candidate = (skill.dir / link).resolve()
            if candidate.is_file():
                skill.requires_file.add(candidate)

    return found
