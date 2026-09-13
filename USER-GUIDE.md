# Using the portable Task Observer

The workflow is: observe available task evidence → capture a scoped candidate → review its cause → stage a small change → apply it within authorization → evaluate the resulting behavior.

The same files serve CC and Codex. Installation and activation are different steps; follow [README.md](README.md) and the [host adapter](references/platforms.md). There is no daemon observing other applications.

## 1. Select the data boundary

Choose an explicit private absolute workspace outside Git and skill discovery. Run the installed helper with `--workspace /absolute/private/observer-data init`. Initialization is explicit; doctor, list and show do not create a missing workspace.

If there is no authorized persistent store, keep a concise handoff in the task response. The skill must say that the candidate is unsaved.

## 2. Capture one useful signal

Save this synthetic example as `capture.json`:

```json
{
  "title": "Distinguish build evidence from delivered behavior",
  "target": "verify-output",
  "scope": "project",
  "source_kind": "direct-user",
  "evidence": "The user corrected a completion claim based only on a successful build.",
  "suggestion": "Report the observable behavior that was tested before claiming delivery.",
  "principle": "A claim must stay within its verification evidence.",
  "confidence": "medium",
  "source_ref": "synthetic-example-1",
  "counterevidence": "A build-only request may legitimately need only a build result.",
  "related_variants": "Review sibling deployment verification skills before generalizing."
}
```

Run the actual installed helper path:

```bash
python3 /absolute/installed/task-observer/scripts/observer.py --workspace /absolute/private/observer-data capture --input capture.json --event-key synthetic-example-1/correction-1
```

It returns a UUID, revision 1, status `candidate` and visibility `private`. Retrying the same episode key and payload returns the same initial record; using that key with different content fails. Omitting the key creates a new identity, so semantic deduplication still requires the reviewer's judgment. Review the actual target before applying any lesson. A proposed new skill can use `target: "new:working-name"`.

Capture text is data and is never executed as shell code. It is also not automatically redacted. Store the smallest useful abstract evidence and review all fields before any separately authorized publication.

## 3. Read before changing state

```bash
python3 /absolute/installed/task-observer/scripts/observer.py --workspace /absolute/private/observer-data list --status candidate --limit 50
python3 /absolute/installed/task-observer/scripts/observer.py --workspace /absolute/private/observer-data show REPLACE_WITH_UUID
```

List reports whether its result is truncated. Inspect full records, rejected recurrence and sibling skills as needed. Classify the cause: instruction defect, harness/tool defect, model execution failure, missing knowledge, temporary preference or evidence too weak to decide.

For an accepted proposal:

```bash
python3 /absolute/installed/task-observer/scripts/observer.py --workspace /absolute/private/observer-data set-status REPLACE_WITH_UUID --expected-revision 1 --status accepted --reason "Reviewed the source and counterexample"
```

Concurrent stale reviewers get a conflict instead of overwriting each other. Reload and decide again; do not blindly retry the same decision on a newer revision.

## 4. Stage, install and evaluate separately

Keep an immutable baseline and proposed patch outside installed skill directories. Follow the [review contract](references/review.md), including upstream source identity and a three-way comparison when both live and proposed versions changed.

States proceed `candidate → accepted → staged → installed → validated`. Artifact states require `--evidence-ref`, for example a reviewed patch path, installation receipt or an evaluation report. The helper records the supplied reference; it cannot verify that an agent actually read a skill or improved its result.

Other transitions support rejection, parking with an unpark condition, and rollback. Installed or validated observations can be marked `rolled_back`; this records an actual rollback and does not itself restore any files. Full transition rules are in [storage.md](references/storage.md).

Use unchanged model/tool budgets, held-out cases, negative cases and independent scoring. Freeze the observer while evaluating it. Record useful findings, false observations, elapsed time, tokens and human review cost. Neither a presence check nor a reminder firing is evidence of better outcomes.

## 5. Inspect failures

Run `doctor` before a review. It validates published records and reports counts, incomplete directories and pending files. Pending items may belong to live writers; inspect them before cleanup. Failed writes never trigger an unsafe overwrite fallback. Unsupported filesystems require a different authorized persistent location or a handoff.

The store is for cooperating processes on one machine. It is not signed, not encrypted by the helper, and not a distributed database. Existing OS access controls still matter. Do not sync a live store through Git or a cloud-drive tool and assume transaction safety.

## Existing users

Portable 1.0.0 does not convert upstream v3 logs, old Codex memory files or numeric IDs automatically. Keep backups and use the [bounded migration procedure](references/migration.md). It does not execute the historical migration helper. To revert the installed skill, restore the saved previous bundle; the new store remains separate.

For user-wide installation, choose the host's documented user skill directory explicitly. First complete a project-local trial and fresh-session activation check. Hook installation, recurring review, global configuration, paid evaluations and publication remain separate actions requiring the corresponding user scope.
