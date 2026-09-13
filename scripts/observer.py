#!/usr/bin/env python3
"""Portable, local Task Observer store. Python 3.8+, standard library only.

One immutable JSON snapshot per revision. Same-filesystem exclusive hard-link
publication exposes only complete records and refuses competing revisions.
No shell execution, telemetry, agent configuration edits or implicit migration.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

SCHEMA = 1
REQUIRED = ("title", "target", "scope", "source_kind", "evidence", "suggestion", "principle")
OPTIONAL = ("source_ref", "counterevidence", "related_variants", "confidence", "host")
TRANSITIONS = {
    "candidate": {"accepted", "rejected", "parked"},
    "accepted": {"staged", "rejected", "parked"},
    "staged": {"installed", "rejected", "parked"},
    "installed": {"validated", "rolled_back"},
    "validated": {"rolled_back"},
    "parked": {"candidate", "accepted", "rejected"},
    "rejected": {"candidate"},
    "rolled_back": {"candidate"},
}


class StoreError(Exception):
    pass


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def parse_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise StoreError("duplicate JSON field: " + key)
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(StoreError("non-finite JSON number")))
    except (ValueError, UnicodeError) as exc:
        raise StoreError("invalid JSON") from exc


def read_json(path):
    if path.is_symlink():
        raise StoreError("symlink not allowed in observer store: " + str(path))
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024:
        raise StoreError("record exceeds 1 MiB")
    return parse_json(raw)


def publish(path, value):
    """Atomic no-replace publication; fail closed if hard links unsupported."""
    encoded = encode(value)
    if len(encoded) > 1024 * 1024:
        raise StoreError("record exceeds 1 MiB")
    fd, temporary = tempfile.mkstemp(prefix=".pending-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def workspace(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise StoreError("workspace must be an absolute path")
    if path.is_symlink():
        raise StoreError("workspace must not be a symlink")
    return path.resolve()


def store_info(root):
    marker = root / "observer.json"
    if not marker.exists():
        raise StoreError("workspace not initialized; use init explicitly")
    info = read_json(marker)
    if not isinstance(info, dict) or type(info.get("schema_version")) is not int or info["schema_version"] != SCHEMA:
        raise StoreError("unsupported workspace schema")
    try:
        uuid.UUID(info["workspace_id"])
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise StoreError("invalid workspace identity") from exc
    observations = root / "observations"
    if observations.is_symlink() or not observations.is_dir():
        raise StoreError("observations directory missing or symlinked")
    return info


def initialize(root):
    if (root / "observer.json").exists():
        return store_info(root)
    if root.exists() and any(root.iterdir()):
        raise StoreError("refusing to initialize a non-empty, unrecognized workspace")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    (root / "observations").mkdir(mode=0o700, exist_ok=True)
    info = {"schema_version": SCHEMA, "workspace_id": str(uuid.uuid4()), "created_at": now()}
    try:
        publish(root / "observer.json", info)
    except FileExistsError:
        pass
    return store_info(root)


def payload(value):
    if not isinstance(value, dict):
        raise StoreError("capture input must be an object")
    unknown = set(value) - set(REQUIRED + OPTIONAL)
    if unknown:
        raise StoreError("unknown capture fields: " + ", ".join(sorted(unknown)))
    for key in REQUIRED:
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise StoreError("non-empty string required: " + key)
    for key in OPTIONAL:
        if key in value and not isinstance(value[key], str):
            raise StoreError("string required: " + key)
    if value["scope"] not in {"task", "project", "user", "general"}:
        raise StoreError("invalid scope")
    if value["source_kind"] not in {"direct-user", "tool-result", "artifact", "inference"}:
        raise StoreError("invalid source_kind")
    if value.get("confidence", "low") not in {"low", "medium", "high"}:
        raise StoreError("invalid confidence")
    if len(encode(value)) > 256 * 1024:
        raise StoreError("capture exceeds 256 KiB; minimize evidence")
    return dict(value)


def identity(value):
    try:
        parsed = str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise StoreError("invalid observation UUID") from exc
    if parsed != value:
        raise StoreError("observation UUID must be canonical")
    return value


def history(root, key):
    directory = root / "observations" / identity(key)
    if directory.is_symlink():
        raise StoreError("observation directory must not be a symlink")
    if not directory.is_dir():
        raise StoreError("observation not found")
    files = sorted(directory.glob("*.json"))
    if not files:
        raise StoreError("observation has no published revision")
    result = []
    for i, file in enumerate(files, 1):
        record = read_json(file)
        if not isinstance(record, dict) or type(record.get("schema_version")) is not int or record["schema_version"] != SCHEMA:
            raise StoreError("unsupported observation schema: " + str(file))
        if file.name != "%06d.json" % i or record.get("id") != key or type(record.get("revision")) is not int or record["revision"] != i:
            raise StoreError("corrupt observation identity or revision sequence")
        if record.get("status") not in TRANSITIONS or record.get("visibility") != "private":
            raise StoreError("invalid observation state")
        captured = payload({k: record[k] for k in REQUIRED + OPTIONAL if k in record})
        if record.get("capture_sha256") != digest(captured):
            raise StoreError("capture integrity mismatch")
        if i == 1:
            if record["status"] != "candidate" or "parent_sha256" in record:
                raise StoreError("invalid initial observation state")
        else:
            if record.get("parent_sha256") != digest(result[-1]):
                raise StoreError("revision integrity mismatch")
            if record["capture_sha256"] != result[0]["capture_sha256"]:
                raise StoreError("capture changed across revisions")
            validate_transition(result[-1]["status"], record["status"],
                                record.get("reason"), record.get("evidence_ref"))
        result.append(record)
    return result


def capture(root, value, event_key=None):
    info = store_info(root)
    value = payload(value)
    if event_key is not None and (not event_key.strip() or len(event_key) > 1024):
        raise StoreError("event key must be non-empty and at most 1024 characters")
    key = str(uuid.uuid5(uuid.UUID(info["workspace_id"]), event_key)) if event_key is not None else str(uuid.uuid4())
    directory = root / "observations" / key
    if directory.is_symlink():
        raise StoreError("observation directory must not be a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    record = dict(value, schema_version=SCHEMA, id=key, revision=1, status="candidate", visibility="private", created_at=now(), capture_sha256=digest(value))
    try:
        publish(directory / "000001.json", record)
    except FileExistsError:
        existing = history(root, key)[0]
        if event_key is None or existing["capture_sha256"] != record["capture_sha256"]:
            raise StoreError("event key collision with different content; original preserved")
        return existing
    return record


def validate_transition(previous, status, reason, evidence_ref):
    if status not in TRANSITIONS[previous]:
        raise StoreError("invalid status transition: %s -> %s" % (previous, status))
    if not isinstance(reason, str) or not reason.strip():
        raise StoreError("a transition reason is required")
    if status in {"staged", "installed", "validated", "rolled_back"} and not (isinstance(evidence_ref, str) and evidence_ref.strip()):
        raise StoreError("--evidence-ref is required for artifact/validation states")
    if status == "parked" and not (isinstance(evidence_ref, str) and evidence_ref.strip()):
        raise StoreError("--evidence-ref must describe the unpark condition")


def set_status(root, key, revision, status, reason, evidence_ref=None):
    store_info(root)
    current = history(root, key)[-1]
    if current["revision"] != revision:
        raise StoreError("revision conflict; reload before deciding")
    validate_transition(current["status"], status, reason, evidence_ref)
    next_record = dict(current, revision=revision + 1, status=status, reason=reason, evidence_ref=evidence_ref, changed_at=now(), parent_sha256=digest(current))
    try:
        publish(root / "observations" / key / ("%06d.json" % next_record["revision"]), next_record)
    except FileExistsError as exc:
        raise StoreError("revision conflict; competing update preserved") from exc
    return next_record


def records(root):
    store_info(root)
    result = []
    for directory in sorted((root / "observations").iterdir()):
        if directory.name.startswith("."):
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise StoreError("unexpected item in observations directory")
        identity(directory.name)
        # A capture may have created its directory but not published revision 1.
        if not list(directory.glob("*.json")):
            continue
        result.append(history(root, directory.name)[-1])
    return result


def pending_writes(root):
    directories = [p for p in (root / "observations").iterdir()
                   if p.is_dir() and not p.is_symlink() and not p.name.startswith(".")]
    incomplete = sum(not any(p.glob("*.json")) for p in directories)
    temporary = sum(1 for p in [root] + directories for _ in p.glob(".pending-*.tmp"))
    return incomplete, temporary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="explicit absolute, persistent data directory")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("doctor", help="read-only integrity and count check")
    listing = commands.add_parser("list", help="read-only latest-state summaries")
    listing.add_argument("--status", choices=sorted(TRANSITIONS))
    listing.add_argument("--target")
    listing.add_argument("--limit", type=int, default=50)
    show = commands.add_parser("show")
    show.add_argument("id")
    entry = commands.add_parser("capture")
    entry.add_argument("--input", required=True, help="JSON input file or - for stdin")
    entry.add_argument("--event-key", help="stable event identity for retry deduplication")
    update = commands.add_parser("set-status")
    update.add_argument("id")
    update.add_argument("--expected-revision", type=int, required=True)
    update.add_argument("--status", choices=sorted(TRANSITIONS), required=True)
    update.add_argument("--reason", required=True)
    update.add_argument("--evidence-ref")
    args = parser.parse_args(argv)
    try:
        root = workspace(args.workspace)
        if args.command == "init":
            result = initialize(root)
        elif args.command == "capture":
            if args.input == "-":
                raw = sys.stdin.buffer.read(256 * 1024 + 1)
            else:
                with open(args.input, "rb") as stream:
                    raw = stream.read(256 * 1024 + 1)
            if len(raw) > 256 * 1024:
                raise StoreError("capture input exceeds 256 KiB")
            result = capture(root, parse_json(raw), args.event_key)
        elif args.command == "set-status":
            result = set_status(root, args.id, args.expected_revision, args.status, args.reason, args.evidence_ref)
        elif args.command == "show":
            store_info(root)
            result = history(root, args.id)[-1]
        else:
            latest = records(root)
            if args.command == "doctor":
                incomplete, temporary = pending_writes(root)
                result = {"ok": True, "incomplete_directories": incomplete, "pending_files": temporary,
                          "warnings": ["Unpublished writes exist; a writer may still be active. Inspect before cleanup."] if incomplete or temporary else [],
                          "schema_version": SCHEMA, "records": len(latest), "by_status": {s: sum(r["status"] == s for r in latest) for s in sorted(TRANSITIONS)}}
            else:
                if args.limit < 1 or args.limit > 10000:
                    raise StoreError("limit must be between 1 and 10000")
                selected = [r for r in latest if (not args.status or r["status"] == args.status) and (not args.target or r["target"] == args.target)]
                fields = ("id", "revision", "title", "target", "scope", "source_kind", "status")
                result = {"total": len(selected), "records": [{k: r[k] for k in fields} for r in selected[:args.limit]], "truncated": len(selected) > args.limit}
        sys.stdout.buffer.write(encode(result))
        return 0
    except (StoreError, OSError) as exc:
        print("observer: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
