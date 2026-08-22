"""Resolve a selection of skills into the full transitive install set."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .scanner import Skill


@dataclass
class Resolution:
    skills: dict[str, Skill] = field(default_factory=dict)
    # requires_file targets that fall outside their referencing skill's own
    # directory, and so aren't already covered by copying that skill's dir.
    extra_files: set[Path] = field(default_factory=set)
    log: list[str] = field(default_factory=list)


def resolve(selected: list[str], catalog: dict[str, Skill]) -> Resolution:
    result = Resolution()
    stack = list(selected)

    for name in selected:
        if name not in catalog:
            raise KeyError(f"unknown skill: {name}")

    while stack:
        name = stack.pop()
        if name in result.skills:
            continue
        skill = catalog[name]
        result.skills[name] = skill
        result.log.append(f"selected {name} ({skill.bucket or 'root'})")

        for dep_name in sorted(skill.requires_skill):
            if dep_name not in catalog:
                result.log.append(
                    f"  {name} references /{dep_name}, but no such skill exists - ignoring"
                )
                continue
            if dep_name not in result.skills:
                result.log.append(f"  {name} requires skill '{dep_name}' -> pulling in")
                stack.append(dep_name)

        for file_path in sorted(skill.requires_file):
            if skill.dir in file_path.parents:
                continue  # sibling file, already covered by copying skill.dir
            result.extra_files.add(file_path)
            result.log.append(f"  {name} requires file '{file_path}' (outside its own dir)")

    return result
