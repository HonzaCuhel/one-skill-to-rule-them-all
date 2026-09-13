# Portable local store

Resolve the helper relative to the loaded skill, and use an explicitly selected
absolute data workspace. The examples below run from the skill directory; adapt
the interpreter and replace the example path with the real configured path.

```console
python3 scripts/observer.py --workspace /absolute/private/observer init
python3 scripts/observer.py --workspace /absolute/private/observer doctor
python3 scripts/observer.py --workspace /absolute/private/observer list --status candidate
python3 scripts/observer.py --workspace /absolute/private/observer capture --input observation.json --event-key task-17/correction-1
python3 scripts/observer.py --workspace /absolute/private/observer show OBSERVATION_UUID
```

`init` is explicit, refuses unrecognized non-empty directories, and is
idempotent for a valid store. `doctor`, `list` and `show` never initialize a
directory. Missing, unknown-schema or corrupt stores fail visibly; an empty
successful list is not a substitute for a failed scan.

```text
observer.json                          workspace identity + schema
observations/<uuid>/000001.json         immutable initial capture
observations/<uuid>/000002.json         immutable status revision
```

Each revision contains the complete observation, typed status and provenance.
Publication writes and fsyncs a private temporary file, then creates its final
name with an exclusive hard link. Readers do not see the partial file. A
conflict never overwrites the existing revision. History checks detect broken
sequences and hash mismatches; hashes are corruption checks, not cryptographic
authentication against someone able to rewrite the whole store.

An interrupted write can leave an uncommitted temporary file or empty capture
directory. These are not observations. The helper does not clean arbitrary data
or promise power-loss durability of directory metadata. Keep backups through a
deliberate maintenance procedure when the store is idle; do not sync live stores
across machines or use an untested network filesystem.

`list` returns latest-state summaries, a total and a truncation flag. Filter by
`--status` or `--target`; `--limit` defaults to 50 and supports up to 10000.
`show` returns the full latest revision. Reads across several records are not a
single globally frozen snapshot; a review records the IDs/revisions it read.

## State changes

```console
python3 scripts/observer.py --workspace /absolute/private/observer set-status OBSERVATION_UUID --expected-revision 1 --status accepted --reason "Evidence reviewed"
```

Main path: candidate → accepted → staged → installed → validated. Candidate and
accepted can be rejected or parked; staged can be rejected or parked; installed
and validated can be rolled_back. Parked can become candidate/accepted/rejected;
rejected and rolled_back can reopen as candidate. Each change requires a reason
and the revision actually reviewed. Reload after a revision conflict, then
reassess rather than blindly replaying an old decision.

Staged, installed, validated and rolled_back require `--evidence-ref` pointing
to their supporting artifact/report. Parked requires the same option describing
the condition to revisit. The helper records the claim; it does not evaluate
the referenced evidence or install anything. The reviewer must verify the
artifact before changing state. Resolved observations remain in the store and
can be queried; no destructive archive-move loop exists.

Preserve source evidence through the user's approved retention policy. Do not
manually change a published revision, delete pending proposals on a keep-two
rule, or replace the observer's own rules during an evaluation.

Doctor reports incomplete directories and pending files separately; these may be live writers or interrupted writes. It never deletes them. Hash chains detect some corruption and enforce state transitions, but are not signatures or protection against a writer deliberately rebuilding valid history. Keep the store in a trusted local directory.
