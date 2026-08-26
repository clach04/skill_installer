# skill_installer

Install a curated subset of Claude/Codex "skills" (Agent Skills, each a
directory with a `SKILL.md`) from a skills repo into your own skills
directory - without pulling in every skill in that repo, and without pulling
in skills that reference each other unless you actually need them.

Initially created with 658d53e6ded8cc0eaa26a96e0580bee9381ca0e3 of mattpocock/skills
before the `/` was removed from the skill cross reference so simple string matching
worked. Post that change a different cross referencing string pattern is used,
which might be too greedy (but so far 2026-08-25 is working correctly). Skill
installer will prompt by default as a sanity check.

Built against [mattpocock/skills](https://github.com/mattpocock/skills)
(`mattpocock_skills` in this README) as its first source, but works against
any directory laid out the same way (a `skills/<bucket>/<name>/SKILL.md`
tree, or a flat `<name>/SKILL.md` tree).

## Why

The upstream repo's own `scripts/link-skills.sh` symlinks *every* skill into
`~/.claude/skills` - by design, and explicitly marked as an unsupported,
dev-only install path. That's fine if you want everything, but it works
against you if you only want a couple of skills and want to keep unrelated
`SKILL.md` files out of context. Skills also aren't always self-contained:
some invoke other skills by name (`/domain-modeling`), and some `SKILL.md`
bodies link to support files (`ADR-FORMAT.md`, `CONTEXT-FORMAT.md`) that live
elsewhere. Installing just the one skill directory you asked for can leave
those references dangling.

`skill_installer` resolves that dependency graph for you, shows you exactly
what it resolved to, and copies (not symlinks) only that set into a target
directory you choose.

See [CONTEXT.md](./CONTEXT.md) for the glossary (Skill, Source, Target,
Bucket, `requires_skill`, `requires_file`, Resolution) and
[docs/adr/](./docs/adr/) for why it copies instead of symlinking and why the
source is a plain path instead of a vendored submodule.

## Requirements

Python 3.10+, no third-party dependencies.

## Usage

List every skill in a source (bucket and description shown; deprecated
skills included and labeled, nothing hidden):

```bash
python -m skill_installer list --source /path/to/mattpocock_skills
python -m skill_installer ls --source /path/to/mattpocock_skills   # alias
python -m skill_installer --source /path/to/mattpocock_skills       # same, default command
```

Install one or more skills into a target directory. Any skill they require
(`requires_skill`), and any file they reference that lives outside its own
skill directory (`requires_file`), is pulled in automatically - each hop is
logged:

```bash
python -m skill_installer install grill-with-docs \
  --source /path/to/mattpocock_skills \
  --target ~/.claude/skills
```

Microsoft Windows
```bash
python -m skill_installer install grill-with-docs --target "%USERPROFILE%\.claude\skills" --source MATTPOCOCK_SKILLS
python -m skill_installer install grill-with-docs --target "%USERPROFILE%\.copilot\skills" --source MATTPOCOCK_SKILLS
python -m skill_installer install grill-with-docs --target "%USERPROFILE%\.pi\agent\skills" --source MATTPOCOCK_SKILLS
python -m skill_installer install grill-with-docs --target "%USERPROFILE%\.agents\skills" --source MATTPOCOCK_SKILLS
...
```

Preview what would change without copying anything:

```bash
python -m skill_installer install grill-with-docs \
  --source /path/to/mattpocock_skills \
  --target ~/.claude/skills \
  --dry-run
```

Microsoft Windows
```bash
python -m skill_installer install grill-with-docs --source MATTPOCOCK_SKILLS --target "%USERPROFILE%\.claude\skills" --dry-run
```

Skip the per-skill confirm prompt (for scripted use):

```bash
python -m skill_installer install grill-with-docs \
  --source /path/to/mattpocock_skills \
  --target ~/.claude/skills \
  --yes
```

Microsoft Windows
```bash
python -m skill_installer install grill-with-docs --source MATTPOCOCK_SKILLS --target "%USERPROFILE%\.claude\skills" --yes
```

## How install decides what to touch

Each selected skill is compared file-by-file (content hash) against its
existing copy in the target directory, if any:

- No existing copy, or no differences -> nothing to confirm; new skills copy
  straight through, unchanged ones are skipped.
- Differences found -> the full change set (added/removed/changed files, with
  a unified diff for changed text files) is shown, and you confirm before it
  overwrites that skill's directory. `--yes` skips the prompt; `--dry-run`
  shows the diff and stops.

There's no separate provenance manifest - the diff view itself is the safety
net. A file the target has that the source doesn't (e.g. something you hand-
edited, or a leftover from a different install method) shows up as a
`removed` line, so you see it before it's gone rather than after.

## What's not built yet

- Interactive picker (`install` with no names given). The CLI is
  argv-driven only for now, by design - see [docs/adr/](./docs/adr/) and
  project history for why this came second.
- Multiple `--source` directories in one invocation. Only one source per
  command right now.
