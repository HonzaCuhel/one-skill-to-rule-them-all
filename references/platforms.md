# One skill, native host adapters

Keep the same SKILL.md, references and Python helper on every host. Only
installation discovery, invocation and optional activation differ. Use the
actual loaded skill directory to find scripts; do not hard-code a user install.

| Capability | Codex | Claude Code | Other coding agents |
|---|---|---|---|
| Project install directory | `.agents/skills/task-observer` | `.claude/skills/task-observer` | Host's documented skill directory |
| User install directory | `~/.agents/skills/task-observer` | `~/.claude/skills/task-observer` | Explicit host-specific choice |
| Explicit invocation | `$task-observer` | `/task-observer` | Host's native invocation, or read the supplied SKILL.md |
| Instruction hierarchy | Native AGENTS chain and overrides | Native CLAUDE chain | Native loaded instructions |
| UI metadata | `agents/openai.yaml` | Codex metadata does not control Claude | Ignore unsupported metadata |
| Persistence | Explicit absolute workspace and Python helper | The same workspace and helper | Same helper if Python/local files are available; otherwise handoff |

Host documentation: [Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Claude Code skills](https://code.claude.com/docs/en/skills), and
[Agent Skills format](https://agentskills.io/specification). These are setup
references; ordinary observation requires no web request.

## Activation is separate from installation

Start with explicit invocation. If the user wants ongoing observation, add a
small instruction through the host's supported configuration mechanism,
preserving existing settings and the user's intended scope. For example:

> Use task-observer during substantive coding/research tasks. The observer data
> workspace is the absolute path configured for this installation. Keep the
> primary task moving and leave global instructions and live skills unchanged
> unless their modification is explicitly requested.

Replace the workspace phrase with the chosen actual path during setup. Do not
copy this as a vague unresolved configuration. In Codex refer to `$task-observer`;
in Claude Code refer to `/task-observer` or its native skill invocation.

Claude Code can optionally inject reminders through SessionStart hooks. No hook
is installed by this bundle and no Codex hook parity is assumed. A reminder
firing does not prove the model acted on it. Creating a cron/scheduled review is
a separate user request. Respect host-specific read-only and approval modes.

After installation or changes, use a fresh session. Verify the actual skill
read/invocation, the correct source path/version, and any resulting record.
Explicit invocation checks usability; an organic-activation test uses ordinary
work prompts without naming the behavior being measured. Do not count a
same-context subagent as a fresh-host activation test.

## Capabilities and degradation

The helper needs Python 3.8+ and a local filesystem supporting atomic exclusive
hard-link publication (e.g. common APFS/ext4/NTFS setups). It has no third-party
runtime dependencies. Use `python`, `python3`, or `py -3` as appropriate to the
actual interpreter; the CLI has no bash dependency. Unsupported filesystems
fail the write rather than falling back to a truncating operation.

If Python or filesystem writes are unavailable, use a structured handoff in
the response: evidence, scope, target, source kind, suggestion, principle and
what is not persisted. Do not improvise shell writes in place of a failed helper.
If a host supports only shared documents, let its authorized storage workflow
own persistence; the local helper is not a multi-host service.

Two agents on one machine may share one explicitly configured store. Event keys
must identify real source episodes; preserve them on retries. Normal model
subagents return candidate data to their owning session by default so the same
episode is not logged repeatedly. Do not synchronize live stores through Git,
Dropbox or similar tools and claim cross-machine transaction safety.
