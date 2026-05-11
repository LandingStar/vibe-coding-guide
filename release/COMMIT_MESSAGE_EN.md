# Commit Message (English)

```
release: package the v0.9.6 preview release around the graph-view work

Package the current graph-view work into a new preview release batch: move the runtime and official instance to 0.9.6, bump the VS Code extension to 0.1.4, and carry the G6 graph-view PoC, host-side parallel preview, and Graph Config interaction into a fresh distributable surface.

## Changes

- Land the G6-driven relation-graph V2 preview in the VS Code progress-graph surface while keeping the original baseline preview intact, including hover / click / adjacency highlight / node detail / runtime-binding emphasis
- Close the host-side interaction slice with Reset Zoom/Pan, collapsible host chrome, a Graph Config bar that shrinks into the top-right floating trigger, metrics overlay, and draggable split sizing
- Eliminate the remaining Graph Config title jump / shrink / scrollbar artifacts by ending collapse on the real collapsed button instead of a cross-container moving title layer
- Move the dual-package and release docs surface to `0.9.6` and bump the extension artifact line to `0.1.4`
- Keep the delivery boundary unchanged: `doc-based-coding-v0.9.6.zip` still carries only the two wheels and release docs, the VSIX remains separate, and control-panel action semantics stay out of scope for this batch

## Verified

- `npm run build`: passed
- `release/verify_version_consistency.py`: All versions consistent
- `scripts/release.py --skip-tests --no-isolation`: generated `release/doc-based-coding-v0.9.6.zip` and synced the new wheel / VSIX batch
```
