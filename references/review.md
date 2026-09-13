# Review and improve skills

Review when requested, or through a separately configured authorized schedule.
Do not block ordinary work with repeated review offers. A review without open
candidates can finish without modifying skills or inventing work.

## Understand the evidence

Run the read-only integrity check and record the IDs/revisions examined. Read
the full relevant records, target skills and source context before grouping or
proposing a disposition. Consider new candidates arriving during the review
separately; never claim the current review covered a later snapshot.

Distinguish a missing rule from a rule the model ignored, a conflicting global
instruction, tool failure, activation gap, scope choice or unsupported inference.
Check rejected and parked items when recurrence is relevant. Read the premise
behind rejection rather than treating it as a permanent veto.

Check relevant sibling skills and host variants. Share methodology only where
evidence supports it; put differences in host guidance. A named family registry
can help a large library, but is not a prerequisite and must not be invented.
General principles are proposals until accepted within the user's actual scope.

## Stage a concrete change

1. Resolve the target's source of truth: maintained repo, user-owned source,
   symlink manager or plugin upstream. Do not edit a generated installation
   and assume the change will survive the next synchronization.
2. Preserve a complete immutable baseline and its hash outside discovery
   directories. Read the current source and any pending draft before editing.
   If both changed, compare baseline/current/proposal as a three-way diff.
3. Make the smallest useful change: remove duplication, clarify a decision,
   change a trigger, add a check, or create a new skill only for a distinct
   workflow. Keep tool choices adaptable unless a constraint is necessary.
4. Create a review packet containing baseline hash, proposed hash, intended
   behavioral difference, target scope/variants, sources, tests and installation
   state. Preserve attribution and the original license for derived content.
5. Update the record with the revision you reviewed and the evidence path.
   Staged is not installed. Install only where the user already authorized it;
   otherwise hand over the review packet without repeatedly asking for already
   granted drafting/editing permission.

Before publication, check existing issues and PRs against current upstream HEAD,
honor the maintainer's contribution channel and identify existing work. Do not
send the report or publish a patch merely because a review drafted it.

## Verify what changed

Structural checks: valid metadata, complete reachable references, matching
bundle contents. Deterministic checks: changed scripts reject unsafe/invalid
inputs and handle collisions, missing stores and supported host environments.
Installation checks: installed bytes match the proposal and a fresh session
loads the intended version. None of these alone proves a better task outcome.

For behavior, derive the change from one set of evidence and compare old versus
new skill on held-out tasks, preserving model, tools and budget. Score actual
outcomes independently. Include negative cases (no capture warranted; sufficient
verification really performed), false generalizations, task completion, review
time and token/cost overhead. Do not score the observer's own assertion that it
improved things as success. State counts and denominators, and keep a failed
or null result visible.

Use a fresh host session for activation evidence; telling a subagent to apply a
skill measures prompted use. Fix the evaluation definition before running it,
keep expected answers out of the skill's context, and do not increase a paid
model or budget beyond the user's authorization.

Freeze the observer while measuring it. Queue self-observations for separate
review, retain rollback artifacts, and mark validated only after downstream
evidence supports it. A rollback is a recorded decision, not deletion of history.
