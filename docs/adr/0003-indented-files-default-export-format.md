# Indented files as the default flatten format

`flatten` output renders each inlined file indented by four spaces rather than
wrapped in fenced code blocks. Fences break whenever a skill's own content
contains a code fence of equal or greater length (grilling's round template
already contains a ``` block), while indentation is collision-proof. The cost
is that the inlined content no longer renders as markdown for the consumer;
`--fences` opts into dynamic-length fences (one more backtick than the longest
backtick run in the file) when that fidelity matters more.
