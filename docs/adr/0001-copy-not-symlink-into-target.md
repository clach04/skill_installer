# 1. Copy, not symlink, into the target directory

## Status

Accepted

## Context

`mattpocock_skills/scripts/link-skills.sh` already installs skills by
symlinking every skill directory from the repo into `~/.claude/skills` and
`~/.agents/skills`. That script is explicitly documented as a dev-only,
unsupported installer that links everything, unfiltered - the opposite of
what this tool is for (installing a curated subset, to keep unrelated `.md`
files out of context).

Given that precedent, symlinking a curated subset into the same kind of
target was the obvious first option: it keeps installed skills fresh on every
`git pull` of the source, same as the existing script.

## Decision

The tool copies selected skill directories into `--target` instead of
symlinking them.

## Consequences

- Installed skills are a frozen snapshot; picking up upstream changes
  requires re-running `install` (mitigated by the diff-and-confirm flow,
  which shows exactly what changed before overwriting).
- The tool never risks colliding with `link-skills.sh` or any other tool that
  manages symlinks into the same well-known directories (`~/.claude/skills`,
  `~/.agents/skills`), because `--target` is caller-specified and unrelated
  to those paths.
- Works identically on Windows and Linux; directory symlinks on Windows
  require elevated privileges or Developer Mode, which copying avoids
  entirely.
