# Changelog

## Portable 1.0.0 — 2026-09-13

First shared-core release candidate in this fork, based on upstream v3.2 commit 7518a85.

- One canonical runtime bundle and native CC/Codex setup guidance.
- New explicit private observation store with immutable JSON revisions, retry keys and revision conflicts.
- Replaces shell-based ID allocation/archiving; preserves legacy sources without executing migration.
- Tightens YAML and recursive-reference bundle validation.
- Adds deterministic packaging, no-overwrite installation, receipt verification and platform CI.
- Declares activation/efficacy evidence limits and retains original/prior-port credit.

Breaking change: upstream v3 observation logs and previous Codex memory files are not the new store format. Follow references/migration.md. No automatic upgrade, self-installation, hook or scheduler is included.
