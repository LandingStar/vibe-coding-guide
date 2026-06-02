# Commit Message (English)

```text
release: package the v0.9.7 preview release with a pinned graph component boundary

Package the current Knowledge Graph Engine integration into a new preview release batch: move the runtime and official instance to 0.9.7, bump the VS Code extension to 0.2.0, and replace the development-only external graph path with a release-local tarball.

## Changes

- Integrate external `@note-web/knowledge-graph-engine` into the VS Code progress graph preview, replacing the archived G6 route
- Keep the VSIX runtime self-contained for graph webview renderer / worker code so users do not install the graph engine npm package
- Switch `vscode-extension/package.json` to `file:vendor/note-web-knowledge-graph-engine-0.1.0.tgz`
- Include the two wheels, VSIX, graph engine tarball, and install docs in the release zip
- Extend release checks to reject development-only graph engine file dependencies and to separate runtime batch versions from the independent VSIX version line

## Verified

- `python release/verify_version_consistency.py --skip-wheel-files`: passed
- `python scripts/build.py --no-isolation`: passed
- `npm run build`: passed
- `node --test dist/test/progressGraphPreviewHtml.test.js`: passed
- `node --test dist/test/progressGraphColorGroups.test.js`: passed
- `node --test dist/test/aiChatToolLoop.test.js`: passed
- `python scripts/release.py --skip-tests --no-isolation`: generated `release/doc-based-coding-v0.9.7.zip` and `release/doc-based-coding-0.2.0.vsix`
```
