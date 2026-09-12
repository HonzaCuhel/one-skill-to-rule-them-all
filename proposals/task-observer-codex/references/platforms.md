# Platform adapters for the pilot

This draft has one portable methodology. The host owns instruction discovery,
tool permissions, task scheduling and context compaction.

| Capability | Codex | Claude Code |
|---|---|---|
| Local pilot directory after deliberate installation | `.agents/skills/task-observer-codex/` or `~/.agents/skills/task-observer-codex/` | `.claude/skills/task-observer-codex/` or `~/.claude/skills/task-observer-codex/` |
| Explicit invocation | `$task-observer-codex` | `/task-observer-codex` |
| Instruction loading | Host-provided AGENTS chain, including overrides | Host-provided CLAUDE chain |
| UI metadata | `agents/openai.yaml` | Do not assume Codex metadata controls Claude |
| Session activation | User instruction or explicit invocation; no hook parity assumed | Optional SessionStart reminder, separately configured and tested |
| Review scheduling | Use the host's supported scheduler only when requested | Use the host's supported scheduler only when requested |

Locate resources relative to the skill that was actually loaded, not a
hard-coded global installation path. If two copies with the same name exist,
record the path/version actually used; do not assume merging or precedence.
Do not reimplement AGENTS discovery by crawling home directories: native
Codex supports overrides and configured fallbacks that a naive crawler misses.

Suggested pilot scope is one project and one writer. Select a stable dedicated
observer data directory outside this repository before enabling persistence;
both agents may use the same format, but this draft has no concurrency control.
Do not place observer data inside Codex's managed memory tree, a plugin cache,
or any installed skills directory. Obey existing memory-write restrictions.

Missing directory, unavailable mount, permission denial, read-only mode,
ENOSPC and unsupported tool are different states. Report the observed state.
Never interpret a denial as permission to bypass the responsible control.

For activation evidence, use a fresh session with ordinary work. Inspect the
actual skill-load/read and capture events; self-reported invocation is weaker
evidence. Explicit invocation tests usability only, not organic activation.

The pilot imports no old logs automatically. Legacy monolithic Codex logs,
upstream v3 Markdown files and this draft's records are separate formats.
Before any future import, retain the original, validate schema and counts,
preserve source identities and reject collisions without modifying targets.
