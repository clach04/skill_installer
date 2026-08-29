"""Post-install compatibility checks for cross-agent skill portability.

Some skills (notably Claude Code-style ones) assume features that not every
agent implements. The installer never rewrites skill content; it only detects
and warns, so the same installed files work everywhere.
"""

from __future__ import annotations

from pathlib import Path

# Claude-ism: body assumes the agent exposes a "Skill tool" for invoking other
# skills. Read-based agents (e.g. Kon) have no such tool and need an AGENTS.md
# directive telling the model to read the referenced SKILL.md instead.
SKILL_TOOL_MARKER = "skill tool"

# Claude-ism: frontmatter meaning "never auto-invoke; user-invoked only".
# Harmlessly ignored by agents that don't parse it, but silently *not honored*
# there either - worth a softer note.
MODEL_INVOCATION_MARKER = "disable-model-invocation"

AGENTS_MD_SNIPPET = """\
Some skills instruct the agent to "Call the Skill tool" for a named skill.
This agent has no Skill tool: instead, read that skill's SKILL.md (resolve the
name against ~/.agents/skills/ or the project's .agents/skills/) and follow it,
including any files it references relative to its directory.
"""


def _iter_skill_files(target_root: Path, names: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in names:
        skill_dir = target_root / name
        if not skill_dir.is_dir():
            continue
        files.extend(p for p in skill_dir.rglob("*") if p.is_file())
    return files


def check_installed(target_root: Path, names: list[str]) -> bool:
    """Scan installed skills for cross-agent compatibility markers.

    Prints warnings for anything found. Returns True if any warning was
    emitted (so callers can adjust their exit summary if desired).
    """
    skill_tool_hits: dict[str, list[str]] = {}
    invocation_hits: list[str] = []

    for path in _iter_skill_files(target_root, names):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(target_root)
        if SKILL_TOOL_MARKER in text.lower():
            skill_tool_hits.setdefault(str(rel), []).append(path.name)
        if MODEL_INVOCATION_MARKER in text:
            invocation_hits.append(str(rel))

    warned = False

    if skill_tool_hits:
        warned = True
        print()
        print(
            f"warning: {len(skill_tool_hits)} installed file(s) reference a "
            f'"Skill tool", which some agents do not have (e.g. Kon loads '
            f"skills by reading SKILL.md files directly)."
        )
        for rel in sorted(skill_tool_hits):
            print(f"  - {rel}")
        print("If your agent has no Skill tool, add this to your global AGENTS.md:")
        print()
        for line in AGENTS_MD_SNIPPET.rstrip("\n").split("\n"):
            print(f"  {line}")

    if invocation_hits:
        warned = True
        print()
        print(
            f"note: {len(invocation_hits)} installed file(s) use the "
            f"'disable-model-invocation' frontmatter flag (user-invoked only). "
            f"Agents that don't parse it will ignore the flag and may "
            f"auto-invoke these skills:"
        )
        for rel in sorted(set(invocation_hits)):
            print(f"  - {rel}")

    return warned
