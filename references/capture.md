# Capture contract

Prepare JSON through a structured file-write tool or safe serialization; do not
interpolate evidence into a shell command. Use `capture --input` with that file
or stdin. Backticks and shell-looking strings remain data. Runtime storage is
private and is not intended to contain secrets or verbatim confidential logs.

Example using synthetic evidence:

```json
{
  "title": "A build is being used as evidence of checkout completion",
  "target": "verify-output@source-version-or-unknown",
  "scope": "project",
  "source_kind": "direct-user",
  "evidence": "The build passed, but the checkout flow was not exercised.",
  "suggestion": "Bound completion claims to performed checks.",
  "principle": "Separate observed behavior from inference.",
  "source_ref": "synthetic-example",
  "counterevidence": "Not yet tested on adequately verified completions.",
  "related_variants": "No other variant supplied; propagation not established.",
  "confidence": "medium",
  "host": "codex"
}
```

Required strings: `title`, `target`, `scope`, `source_kind`, `evidence`,
`suggestion`, `principle`. Optional strings: `source_ref`, `counterevidence`,
`related_variants`, `confidence`, `host`. Unknown fields and duplicate JSON keys
are rejected. Maximum capture input is 256 KiB; a useful observation should be
far smaller. Confidence, when present, is low/medium/high, not a calibrated score.

Scope is task/project/user/general. Source kind is direct-user/tool-result/
artifact/inference. A target identifies the actual skill and version/path when
known; use an explicit `new:` candidate when none exists. Validation cannot
verify that a target was truly loaded: evidence and review must establish it.

Supply a stable `--event-key` when retrying the same capture or receiving the
same episode from multiple agents. Identical payload + event key returns the
original first revision; different content with the same key is a conflict.
Without an event key, each call creates a fresh UUID. A new example of an old
finding is a new event related during review, not permission to rewrite history.

Look at relevant latest-state summaries, then read full records before resolving
or dismissing them. A rejected candidate's premise can be wrong; preserve the
reason and reopen with a new revision when new evidence warrants it.

For public output, produce a separate reviewed document from selected evidence.
Review titles, body fields, source references and combined identifying details.
The helper never marks a stored observation public or uploads it.
