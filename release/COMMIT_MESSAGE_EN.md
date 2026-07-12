# Commit Message (English)

```text
release: package the v0.9.9 installed-contract fix

Resolve the Subagent Report schema from the target workspace when consuming
worker trajectory updates from an installed wheel. Bootstrap the report schema
and worker procedure with the official instance, and make the build prove this
path through an isolated dual-wheel install and CLI consumption smoke.
Exclude root build/dist outputs from pack hashes so packaging no longer causes
post-build lock drift while source and nested pack content remain protected.

Clarify that Local Work lane count proves logical decomposition rather than
scheduler/provider concurrency. Package the current readback and orchestration
baseline without starting host inversion; keep the Direct/Managed mode facility
matrix as follow-up work. The independently versioned VSIX remains 0.2.1.

Verified by the full release flow: `2371 passed, 3 skipped`, isolated installed
smoke and Electron smoke passed, and `doc-based-coding-v0.9.9.zip` was created.
```
