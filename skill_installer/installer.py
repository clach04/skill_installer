"""Diff-and-copy logic for installing resolved skills into a target dir."""

from __future__ import annotations

import difflib
import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DirDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


def _hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    if not root.is_dir():
        return hashes
    for path in root.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(root)).replace("\\", "/")
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def diff_dirs(source_dir: Path, target_dir: Path) -> DirDiff:
    src_hashes = _hash_tree(source_dir)
    dst_hashes = _hash_tree(target_dir)
    diff = DirDiff()
    for rel, h in src_hashes.items():
        if rel not in dst_hashes:
            diff.added.append(rel)
        elif dst_hashes[rel] != h:
            diff.changed.append(rel)
    for rel in dst_hashes:
        if rel not in src_hashes:
            diff.removed.append(rel)
    diff.added.sort()
    diff.removed.sort()
    diff.changed.sort()
    return diff


def render_diff(diff: DirDiff, source_dir: Path, target_dir: Path) -> str:
    lines: list[str] = []
    for rel in diff.added:
        lines.append(f"  + {rel}")
    for rel in diff.removed:
        lines.append(f"  - {rel}")
    for rel in diff.changed:
        lines.append(f"  ~ {rel}")
        src_path = source_dir / rel
        dst_path = target_dir / rel
        try:
            src_text = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
            dst_text = dst_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            lines.append("    (binary file changed)")
            continue
        udiff = difflib.unified_diff(dst_text, src_text, lineterm="", n=2)
        lines.extend(f"    {line}" for line in udiff)
    return "\n".join(lines)


def copy_skill_dir(source_dir: Path, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


def copy_extra_file(source_root: Path, file_path: Path, target_root: Path) -> Path:
    rel = file_path.relative_to(source_root)
    dest = target_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, dest)
    return dest
