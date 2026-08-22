# Language

**Skill**:
An installable unit consisting of a directory containing a `SKILL.md`, plus
every other file alongside it (support docs, `agents/*.yaml`, etc). The whole
directory is the atomic unit of install - never a subset of its files.

**Source**:
A local directory passed via `--source` that the tool scans for **Skills**.
Not managed or cloned by this tool; the caller is responsible for the
directory existing and being up to date.

**Target**:
The local directory passed via `--target` that selected **Skills** (and their
resolved dependencies) are copied into.

**Bucket**:
The category folder a **Skill** lives in within a **Source** (for example
`engineering`, `productivity`, `misc`, `personal`, `in-progress`, `deprecated`
in the `mattpocock_skills` source). Shown alongside every skill in listings,
including deprecated ones - nothing is hidden by default.

**requires_skill**:
A dependency edge from one **Skill** to another. Discovered by scanning a
`SKILL.md` body for `/token` references and matching `token` against the set
of known **Skill** names in the same **Source**. A `/token` that doesn't match
a known skill name is prose, not a dependency.

**requires_file**:
A dependency edge from a **Skill** to a specific file, discovered by parsing
markdown links (`[text](path)`) in its `SKILL.md` and keeping only links whose
target resolves to a real file on disk. Only matters for install purposes
when the target lies outside the referencing skill's own directory - a
sibling file is already covered by copying the whole skill directory.

**Resolution**:
Expanding one or more selected **Skills** into the full transitive closure of
their **requires_skill** edges (and any **requires_file** targets outside a
skill's own directory), producing the complete set of directories/files that
must be copied for the selection to work standalone in the **Target**.
