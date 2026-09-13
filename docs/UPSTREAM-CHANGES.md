# Changes and upstream coordination

Based on upstream commit [7518a85](https://github.com/rebelytics/one-skill-to-rule-them-all/tree/7518a858cf5b550bf3dc61b1b625f4cb0b5fa87f), checked 2026-09-13. This is a portable fork with declared new behavior, not an upstream release or an assertion of maintainer endorsement.

## Fixes and replacements

| Problem | Evidence / prior work | Portable result |
|---|---|---|
| Literal YAML descriptions bypass 1024-character validation; malformed/non-string values underchecked | Historical F01 plus regression fixtures | Actual decoded YAML type/length validation |
| Referenced files can point to missing local references unnoticed | Historical F02 plus recursive/escaped/relative-link fixtures | Recursive lexical reference validation with cycle handling and containment checks |
| Native macOS Bash 3.2 cannot parse the embedded archive/ID block | Historical F03; now [upstream issue #152](https://github.com/rebelytics/one-skill-to-rule-them-all/issues/152) | Runtime replaced with Python helper; no Bash snippet shipped |
| Archive destination collision can overwrite an older entry | Historical F04 isolated algorithm reproduction | No archival moves; immutable revisions and exclusive publication |
| Status-like title text plus stale resolved date can archive an open item | Historical F05 isolated algorithm reproduction | Parsed JSON state and explicit transition validation |
| Concurrent/retried observations can duplicate identities or lose updates | New concurrent CLI fixtures | UUIDs, explicit retry episode key, exclusive publication, expected revisions; semantic dedup remains reviewer work |
| Installation/staging mistaken for observed behavioral success | Current issue themes, including [#154](https://github.com/rebelytics/one-skill-to-rule-them-all/issues/154) | Explicit evidence levels and receipts; no claim that prompt-only instructions enforce future behavior |

The original archive/migration algorithms remain available in the pinned history and historical documents. Removing them from this fork's runtime is an architectural replacement, not a surgical patch to their upstream implementation.

## Existing work we do not duplicate

As of the snapshot, upstream open PRs include [#119](https://github.com/rebelytics/one-skill-to-rule-them-all/pull/119) (legacy migration), [#130](https://github.com/rebelytics/one-skill-to-rule-them-all/pull/130) (staging base), [#134](https://github.com/rebelytics/one-skill-to-rule-them-all/pull/134) (header heuristics) and [#141](https://github.com/rebelytics/one-skill-to-rule-them-all/pull/141) (Claude plugin). They should be rechecked before any outreach. We do not copy or claim those patches as new work.

[AllstarGER's earlier Codex adaptation](https://github.com/AllstarGER/one-skill-to-rule-them-all) is prior art. This fork contributes a shared core, current native host discovery, an explicit persistent-store boundary and executable reliability checks. It does not claim to invent Codex support.

## Potential focused upstream contribution

The validator and its regression tests can be reviewed independently of the new storage protocol. A proposed PR should state:
1. the actual YAML parsing and transitive-reference failure;
2. the new PyYAML development dependency;
3. the supported lexical link forms and parser limitations;
4. regression controls and exact tested platforms.

A separate discussion could offer the shared core and host adapters. The maintainer may reasonably prefer upstream's existing methodology. Do not bundle a storage redesign into a purported validator bug fix. No upstream PR, issue comment or email is sent by this repository's preparation.

## Declared methodology changes

- Opt-in configured persistence and handoff fallback replace guessed global workspace locations.
- Immutable JSON revisions replace numeric Markdown files, auto-archive and ID floors.
- Capture fields describe scope, source provenance, counterevidence and related variants.
- Baselines, staged changes, installed files and validated behavior are distinct.
- Review and activation frequency follow the user's requested workflow; no unconditional checkpoint quota or installed scheduler.
- Legacy logs require a separate bounded migration decision; no automatic conversion.

Historical research under `research/` describes the pinned upstream version. The proposal under `proposals/task-observer-codex/` is an earlier draft, not the current runtime bundle. All are excluded by the bundle manifest.
