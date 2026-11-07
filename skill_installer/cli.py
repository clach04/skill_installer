"""Argv-driven CLI: `list`/`ls` (default) and `install`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compat import check_installed
from .flatten import DEFAULT_PREAMBLE, flatten
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

    flatten_p = sub.add_parser("flatten", help="render skills as a single markdown document")
    flatten_p.add_argument("names", nargs="+")
    flatten_p.add_argument("--source", required=True, type=Path)
    flatten_p.add_argument("--output", type=Path, help="write to file instead of stdout")
    flatten_p.add_argument("--all-files", action="store_true", help="inline every text file in each skill directory, not just SKILL.md and files it links to")
    flatten_p.add_argument("--fences", action="store_true", help="wrap file content in dynamic-length fences instead of indenting it")
    flatten_p.add_argument("--no-deps", action="store_true", help="export only the named skills, without resolving their dependencies")
    preamble_g = flatten_p.add_mutually_exclusive_group()
    preamble_g.add_argument("--preamble", help="use this text as the preamble instead of the default")
    preamble_g.add_argument("--preamble-file", type=Path, help="use the contents of this file as the preamble instead of the default")
    preamble_g.add_argument("--no-preamble", action="store_true", help="emit no preamble")

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

    if not dry_run:
        check_installed(target, sorted(resolution.skills))

    return 0


def _cmd_flatten(args: argparse.Namespace) -> int:
    preamble = DEFAULT_PREAMBLE
    if args.no_preamble:
        preamble = None
    elif args.preamble is not None:
        preamble = args.preamble
    elif args.preamble_file is not None:
        preamble = args.preamble_file.read_text(encoding="utf-8")

    try:
        doc = flatten(
            args.names,
            args.source,
            all_files=args.all_files,
            use_fences=args.fences,
            no_deps=args.no_deps,
            preamble=preamble,
        )
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output is not None:
        args.output.write_text(doc, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        # UTF-8 regardless of console codepage (skill content may contain emoji)
        sys.stdout.buffer.write(doc.encode("utf-8"))
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
    if command == "flatten":
        return _cmd_flatten(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
