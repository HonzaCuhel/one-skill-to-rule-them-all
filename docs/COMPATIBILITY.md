# Compatibility and evidence

Snapshot: 2026-09-13. Portable skill version 1.0.0; observation schema 1.

| Layer | Intended support | Evidence |
|---|---|---|
| Shared skill format | Agent Skills-compatible Markdown, native CC/Codex discovery | Source checked against official host/spec documentation; bundle validation |
| Codex project install | `.agents/skills/task-observer` | Isolated directory installation and byte/hash checks |
| Claude Code project install | `.claude/skills/task-observer` | Same isolated installation and identical runtime bytes |
| Python helper/installer | Python 3.8+, standard library | All 60 tests passed on macOS Python 3.11.8 and Linux Python 3.12.3; initial helper tests also ran on macOS Python 3.8.8 |
| OS coverage | Linux, macOS, Windows on suitable local filesystems | Automated CI matrix; consult the linked run for actual result |
| Other coding agents | Native skill reader plus Python/filesystem, or explicit handoff | Capability design only; no named third host certified |
| Native agent activation | Fresh session reading actual installed source | Not yet independently verified on both native hosts |
| Improved agent outcomes | Useful observations with acceptable false positives/overhead | No controlled comparative efficacy result yet |

[CI run history](https://github.com/HonzaCuhel/one-skill-to-rule-them-all/actions/workflows/tests.yml) is the authoritative current platform-test status. Test results are not a guarantee of automatic activation, instruction adherence or productivity improvement.

## Runtime limits

The observation store uses exclusive same-filesystem hard links to publish fully written JSON revisions. Cooperating local writers are supported; unsupported filesystems fail writes. No fallback truncation, destructive archival or distributed lock service is provided. File contents are flushed before publication, but directory fsync/power-loss durability is not guaranteed.

Capture supports a 256 KiB maximum minimized payload; stored snapshots are bounded to 1 MiB. The helper rejects unknown schema versions, invalid lifecycles and stale expected revisions. It checks a hash chain, not an authenticated history. A process with filesystem write permission can rewrite the whole store.

List is a per-record read, not a consistent cross-record transaction snapshot. Pending files or empty observation directories may indicate a live or interrupted writer. Doctor reports them and performs no destructive repair.

The installer requires an absent destination and existing parent, rejects symlink components, and rolls back only files it created. Installation is not atomically published as a whole directory; run it before starting the host. A crash may leave a partial directory that must be inspected before a retry. Receipt hashes detect drift relative to that receipt, not a maliciously replaced receipt.

## Evaluation still to run

For each native host: install in a clean temporary project, start a genuinely fresh session, explicitly invoke the skill, and verify the loaded source/version and a synthetic observation. Then run ordinary prompts without naming observation behavior to measure organic activation.

For efficacy: freeze the observer, compare baseline and portable skill with the same model/tools/budget on held-out coding/research tasks, and independently score useful corrections, unsupported generalization, false observations, privacy boundary errors and overhead. Keep inference/personal-preference cases and no-observation controls. Report failed attempts and cost. Do not silently upgrade the model or run paid batches as an installation check.
