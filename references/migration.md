# Upgrading an existing installation

This fork updates Task Observer for coding agents from upstream v3.2.0-era
methodology. It introduces a new JSON revision store. It is not a compatible
reader/writer of upstream's numbered Markdown logs or AllstarGER's monolithic
Codex memory log.

## Existing Codex or Claude Code skill

Preserve the old installation and its logs outside skill-discovery directories.
Inspect its source of truth and existing activation settings. Install the new
bundle into a separate test project first; the installer refuses to overwrite
an existing destination. Use the same `task-observer` bundle for both agents.
After the user accepts the replacement, retire the old discovered copy through
their existing skill-management workflow, then install at the intended path.
Do not leave two same-named skills active and assume they merge.

Choose a new empty persistent workspace and explicitly initialize it. Existing
logs remain read-only evidence. For a bounded backlog transfer, read selected
legacy entries, preserve their original source/id references and scope, and
capture only still-relevant candidates with stable event keys. Use `artifact`
as the source kind; do not pretend an imported record is a fresh correction.
Record the original resolution separately in evidence. New records begin as
candidates and require review rather than being silently labeled validated.

No automated bulk importer is shipped. In particular, the legacy converter's
overwrite and decreasing-floor issues already have upstream PR #119. That
script is retained only in Git/history documentation, not in the portable
bundle. Do not run it against live data from this skill. Keep original logs
until transferred entries and references have been checked.

## Review before wider rollout

Check a fresh Codex session and a fresh Claude Code session separately. Verify
the loaded path/version, capture output and stored bytes. Start with one
project, then widen scope only when the workflow proves useful. Rollback means
restoring the previous skill through the approved management workflow and
keeping the new store as separate evidence; no reverse conversion is claimed.
