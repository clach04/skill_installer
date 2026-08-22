"""Argv-driven CLI: `list`/`ls` (default) and `install`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .installer import copy_extra_file, copy_skill_dir, diff_dirs, render_diff
from .resolver import resolve
from .scanner import scan_source


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill_installer")
    parser.add_argument("--source", type=Path, help="used when no subcommand is given (defaults to 'list')")
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", aliases=["ls"], help="list skills available in a source")
    list_p.add_argument("--source", required=True, type=Path)

    install_p = sub.add_parser("install", help="install one or more skills into a target dir")
    install_p.add_argument("names", nargs="+")
    install_p.add_argument("--source", required=True, type=Path)
    install_p.add_argument("--target", required=True, type=Path)
    install_p.add_argument("--dry-run", action="store_true")
    install_p.add_argument("-y", "--yes", action="store_true", help="skip confirm prompts")

    return parser


def _cmd_list(source: Path) -> int:
    catalog = scan_source(source)
    for name in sorted(catalog):
        skill = catalog[name]
        bucket = skill.bucket or "root"
        desc = f" - {skill.description}" if skill.description else ""
        print(f"{name} ({bucket}){desc}")
    return 0


def _cmd_install(source: Path, target: Path, names: list[str], dry_run: bool, yes: bool) -> int:
    source = source.resolve()
    catalog = scan_source(source)
    try:
        resolution = resolve(names, catalog)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for line in resolution.log:
        print(line)

    target.mkdir(parents=True, exist_ok=True)

    for name in sorted(resolution.skills):
        skill = resolution.skills[name]
        dest = target / name
        diff = diff_dirs(skill.dir, dest)

        if diff.is_empty:
            print(f"== {name} == up to date, skipping")
            continue

        print(f"== {name} ==")
        print(render_diff(diff, skill.dir, dest))

        if dry_run:
            continue

        if not yes:
            answer = input(f"Apply changes to {dest}? [y/N] ").strip().lower()
            if answer != "y":
                print(f"skipped {name}")
                continue

        copy_skill_dir(skill.dir, dest)
        print(f"installed {name} -> {dest}")

    for file_path in sorted(resolution.extra_files):
        dest = target / file_path.relative_to(source)
        print(f"== extra file: {file_path.relative_to(source)} ==")
        if dry_run:
            continue
        if not yes:
            answer = input(f"Copy {file_path} -> {dest}? [y/N] ").strip().lower()
            if answer != "y":
                print("skipped")
                continue
        copy_extra_file(source, file_path, target)
        print(f"copied -> {dest}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command = args.command or "list"

    if command in ("list", "ls"):
        source = args.source
        if source is None:
            parser.error("--source is required")
        return _cmd_list(source)
    if command == "install":
        return _cmd_install(args.source, args.target, args.names, args.dry_run, args.yes)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
