# Observation contract — pilot v1

Store each candidate as a Markdown file with a YAML header in the configured
private observer workspace. Use a fresh UUID as the identity and filename;
do not infer a new identity from the highest filename in a shared directory.
This is a proposed format, not upstream v3.2 compatibility. Quote strings and
every list element. Unknown schema versions require review, not silent import.

Required fields:

| Field | Meaning |
|---|---|
| `schema_version` | Literal `task-observer-pilot/1` |
| `id` | Unique UUID |
| `created_at` | ISO 8601 timestamp with timezone |
| `status` | `candidate`, `accepted`, `staged`, `installed`, `validated`, `rejected`, `parked`, `superseded`, `rolled_back` |
| `title` | Short failure or opportunity description |
| `visibility` | `private` by default; `public-reviewed` only after export review |
| `scope` | `task`, `project`, `user`, or `general` |
| `source_kind` | `direct-user`, `tool-result`, `artifact`, or `inference` |
| `evidence` | Minimal factual observation, separate from interpretation |
| `source_ref` | Safe durable pointer, or explicit `unavailable`; no fabricated citation |
| `target` | Actual skill identity/path/version or explicit new candidate |
| `confidence` | `low`, `medium`, `high`, with justification in the body |
| `occurrences` | Count of distinct observed episodes, not agent repetitions |
| `counterevidence` | Contradicting cases or explicit `not-yet-tested` |
| `related_variants` | Checked variants and propagation decision, or `none` with reason |

Body: evidence and alternative explanations; proposed change; applicability
and exclusions; test that could falsify the benefit; rationale for the scope.
Confidence is a judgment, never a calibrated probability unless measured.
Do not require an occurrence threshold for a direct user instruction, and
never inflate recurrence by counting multiple agents seeing the same episode.

Lifecycle changes keep a dated reason and actor. A rejected candidate records
the premise and reconsideration condition; a parked one records its trigger.
`staged` means a draft exists, `installed` means installed bytes were verified,
and `validated` requires downstream behavior evidence. A failed test leaves
the candidate unvalidated and may justify rollback. Keep historical identities.

The draft does not supply a schema validator, transaction engine or retention
daemon. Until those are built, use small, single-writer pilots. Review
retention explicitly before long-running capture, keep logs out of Git, and
never attach private observation files to a public issue.
