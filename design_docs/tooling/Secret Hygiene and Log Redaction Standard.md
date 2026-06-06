# Secret Hygiene and Log Redaction Standard

## Document Position

This document defines the repository-level secret hygiene rule for tracked
workflow artifacts, especially `.codex/decision-logs/*.jsonl`.

It is a long-lived tooling standard. It does not replace provider-side key
rotation. If a real key is committed or pushed, the key must be revoked or
rotated even after repository history is cleaned.

## Repository Boundary

The following files are local credential surfaces and must not be committed:

- `.bashrc`
- `tmp/key.md`
- `llm-apikey.md`
- `*.apikey`
- `*.secret`

`.codex/decision-logs/*.jsonl` may remain tracked as audit artifacts, but they
must not contain raw secrets copied from terminal commands, prompts, tool
outputs, or configuration values.

## Redaction Rule

When logs need to preserve evidence that a secret-bearing command happened,
keep the structural context and replace the sensitive value with a stable
placeholder such as:

- `sk-REDACTED`
- `Bearer REDACTED`
- `<REDACTED_SECRET>`

Do not partially mask a still-valid secret in committed files. Partial masks are
acceptable only in human-facing reports that are not themselves copied from the
secret source.

## Required Check

Before committing release, handoff, decision-log, or packaging changes, run:

```bash
python scripts/scan_secrets.py --scope worktree
```

Before committing staged changes, run:

```bash
python scripts/scan_secrets.py --scope staged
```

For incident cleanup or release confirmation, run:

```bash
python scripts/scan_secrets.py --scope history
```

The scanner reports detector names and file locations only. It intentionally
does not print matched secret values.

## Build Integration

`python scripts/build.py` runs the worktree secret scan as part of its default
pre-build checks. `--skip-checks` bypasses both version consistency and secret
hygiene checks, so it should be reserved for controlled local iteration only.

## Incident Response

If a secret reaches Git history:

1. Rotate or revoke the secret first.
2. Redact the working tree and remove local credential files from the Git index.
3. Rewrite history to remove or redact the secret-bearing blobs.
4. Force-update affected branches and tags with lease protection where possible.
5. Re-run `python scripts/scan_secrets.py --scope history`.
