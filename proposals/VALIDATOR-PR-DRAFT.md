# Unsent upstream PR draft

Status: prepared locally only. Recheck upstream issues and PRs before submitting.

**Title:** Validate decoded YAML descriptions and transitive bundled references

**Proposed change:** [commit 73a0561](https://github.com/HonzaCuhel/one-skill-to-rule-them-all/commit/73a0561), independent of the portable store redesign.

## Body

The bundle gate can accept an overlong YAML literal-block description because it measures the block marker rather than the decoded value. It also misses a missing bundled file when that reference is reached through another reference file.

This change validates the actual YAML scalar type and decoded length, and follows supported local Markdown/backtick citations transitively with cycle handling and staged-root containment. It distinguishes file-relative Markdown destinations from the existing root-relative backtick convention, decodes Markdown escapes, and rejects symlinked staged files before reading them.

PyYAML is now a required **validator/development** dependency rather than an optional regex fallback. It is declared in requirements-dev.txt. The runtime skill does not need a YAML dependency. Release/validation environments must install that dependency; the fork's release workflow demonstrates this separately.

Validation: 31 focused regression tests passed on macOS and Linux. Cases include overlong literal/folded/escaped descriptions, non-string and invalid YAML, direct/transitive missing references, cycles, relative/escaped paths, containment, symlinks and external-skill exemptions. The portable fork also runs these tests in its cross-platform CI.

Scope: this remains a documented lexical reference check, not a full Markdown parser, Python import resolver or dynamic-dependency analyzer. It scans a defined set of reachable text formats and excludes fenced examples and binaries.

The separate portable store, new observation lifecycle and Codex/Claude setup changes are not part of this proposed contribution.

## Before submission

- Rebase or cherry-pick only the focused commit onto current upstream.
- Check whether an issue or PR now covers the same validator cases.
- Confirm how upstream wants PyYAML installed in its release gate.
- Include the verified CI run and platform details available at submission time.
- Keep original attribution; do not claim the existing Codex port or PR #119 as new work.
