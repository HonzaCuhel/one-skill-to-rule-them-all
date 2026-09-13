# Portable Task Observer Implementation Plan

> For agentic workers: use test-driven implementation and independent review. The user approved the shared-core direction on 2026-09-13 and publication to their fork. No upstream message or PR is authorized by this plan.

Goal: ship one skill bundle for Codex, Claude Code and capability-compatible coding agents, with reproducible fixes and explicit compatibility limits.

Architecture: one root SKILL.md and on-demand shared references; host guidance is data in references, not separate skill copies. A standard-library Python helper owns a versioned append-only observation store. A separately tested bundle validator requires PyYAML. The old upstream files remain recoverable in Git; legacy migration is not run or silently changed.

## Scope and acceptance

- [x] Fix bundle validation of YAML description types/length and transitive local references. `python3 -m unittest discover -s tests -p test_bundle_validator.py -v` must fail on upstream before the fixes and pass afterwards.
- [x] Add `scripts/observer.py`: explicit init, read-only doctor/list/show, idempotent capture, revision-checked status transitions. `tests/test_observer.py` must cover unknown schemas, missing stores, literal hostile strings, 32 concurrent captures, duplicate event keys, stale revisions, interrupted publication and no overwrite.
- [x] Replace the runtime shell/archival snippets with the shared helper. UUID identities and immutable revisions remove max+1 allocation and destructive archive moves; resolved records remain searchable. Do not claim distributed synchronization or migrate legacy logs automatically.
- [x] Provide one canonical build/install bundle from an explicit allowlist. Installation is explicit, refuses overwrites and excludes Git/history/proposals/private logs. Test clean Codex and Claude directory layouts in temporary projects and compare installed bytes.
- [x] Write concise host adapters for native skill invocation, native instruction precedence and handoff when Python/filesystem/persistence is unavailable. Retain signal quality, deduplication, skill families, review/staging, attribution, privacy and behavioral evaluation guidance.
- [x] Add CI on Linux/macOS/Windows for helper and bundle tests; local verification is reported separately from CI results. Update README/USER-GUIDE with actual commands and limits, preserved credit and the existing Codex port link.
- [ ] Have independent reviewers inspect specification compliance and then code quality. Resolve actionable findings; execute final tests, inspect public diff and publish only the prepared changes to the user's fork.

## Upstream coordination snapshot

Checked 2026-09-13: main still `7518a858cf5b550bf3dc61b1b625f4cb0b5fa87f`. Open PRs are #119 (legacy migration), #130 (staging base), #134 (observation-header heuristic), #141 (Claude plugin). These patches are not duplicated. Native Bash parsing is now reported in issue #152, with no matching open PR. Bundle-validator failures F01/F02 remain candidates for separate upstreamable commits. This fork's new storage protocol is a declared methodology change, not a drop-in rewrite of #119.

## Evidence boundaries

No paid model batch, external-service deployment, global skill activation or automatic self-installation. Synthetic helper tests, package installation tests, native host discovery and model-behavior tests are different evidence levels. Do not label unrun host/model tests as passing. Keep the previous audit and pilot under research/proposals as historical material, excluded from the installed bundle.

## Implementation verification

2026-09-13: 60 tests passed on macOS Python 3.11.8 and Linux Python 3.12.3. The actual installed helpers in isolated Codex/Claude layouts shared one store, deduplicated an episode, preserved six lifecycle revisions and retained valid install receipts. The exact ten-file bundle passed the validator. See research/portable-validation.json. Native-host activation and comparative model efficacy remain unverified; CI publication results are tracked separately.
