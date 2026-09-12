# Reviewing evidence and proposing changes

Read the full evidence before grouping or rejecting candidates. A skill can
be correct while the model ignores it; extra instructions may make that worse.
Classify the cause: missing guidance, conflicting guidance, activation failure,
tool limitation, unsuitable task, user preference, or unsupported inference.

Choose the smallest change likely to help: remove a conflicting rule, clarify
an existing decision, adjust a trigger, add a deterministic check, or add a
separate skill only when the workflow is distinct. Check related variants and
upstream issues before proposing another implementation.

For each changed target, retain an immutable baseline outside discovery paths,
its exact source/version and content hash, the proposed artifact and its hash,
and an explanation of the intended behavioral difference. If the current
source differs from that baseline, review a three-way diff before refreshing
the draft. Never classify a text difference alone as a semantic superset.

Prepare a focused diff and a review packet. Respect the user's existing
authorization for drafting and editing; do not repeatedly ask about already
authorized scope. Installation, publication, outreach and cost increases are
separate actions and follow the user's actual authorization for each.

Validation has three distinct layers:

1. Structural: parse metadata, resolve shipped references, inspect packaging.
2. Mechanical: execute changed helper behavior in synthetic fixtures, including
   rejection controls, collisions, stale state and platform failures.
3. Behavioral: compare unchanged vs proposed skill on the same held-out tasks,
   using the same host, model, tool access and budget; score actual outcomes.

Use task completion, recurrence of the original failure, false observations,
review time and token/cost overhead. Observation count and skill growth are
activity metrics, not success metrics. Keep test tasks and expected answers
away from the observer while it derives proposed rules. A prompted dry run
does not prove organic activation or improvement over baseline.

If deploying an accepted candidate later, verify the installed bytes and test
a fresh session. Record the result and preserve an explicit rollback path.
The observer must not install its own proposed changes or evaluate them as
successful merely because it wrote them. During a pilot freeze its own rules;
queue self-observations for separate human review.
