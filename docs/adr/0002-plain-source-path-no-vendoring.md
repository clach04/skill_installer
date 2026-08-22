# 2. Plain `--source` path, no submodule or clone management

## Status

Accepted

## Context

This tool's first (and, so far, only) intended source is
`mattpocock_skills`, a repo the user does not own or maintain. Two ways to
give the tool access to a source were considered:

1. Vendor the source repo into this one, as a git submodule pinned to a ref.
2. Read from a plain local directory path passed by the caller, with no
   cloning or version pinning owned by this tool.

Vendoring would guarantee the tool always has a source available and pin
exactly which upstream commit is in use, at the cost of tying the tool to one
specific repo/ref and adding submodule-management complexity. The user
expects to eventually point this tool at more than one source (their own
skill sets alongside `mattpocock_skills`), which a single pinned submodule
does not fit.

## Decision

`source` is a plain local directory path, given per-invocation as `--source`.
The tool does not clone, pull, or pin any source repo; the caller is
responsible for the directory existing and being at whatever state they want
scanned.

## Consequences

- No submodule-update workflow to maintain; `git pull` in the source repo is
  entirely outside this tool's concern.
- Supporting multiple sources later (e.g. a personal skills directory
  alongside `mattpocock_skills`) requires no change to how a source is
  represented - it is already just a path.
- The tool has no way to guarantee a source is at a known-good state; a
  caller pointing `--source` at a broken or mid-edit checkout gets whatever
  is on disk, with no version safety net.
