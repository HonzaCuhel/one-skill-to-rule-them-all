#!/usr/bin/env python3
"""Build or install the same allowlisted skill bytes for any host.

Uses only Python's standard library. Installation requires an explicit,
previously absent task-observer destination and an existing parent directory.
It does not alter host configuration, observation stores, or other skills.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile


NAME = "task-observer"
SKILL_VERSION = "1.0.0"
RECEIPT_VERSION = 1
RECEIPT = ".task-observer-install.json"
MANIFEST = tuple(sorted((
    "SKILL.md", "LICENSE.txt", "agents/openai.yaml", "scripts/observer.py",
    "references/capture.md", "references/review.md", "references/platforms.md",
    "references/storage.md", "references/migration.md", "references/signals.md",
)))


def checked_path(value):
    """Reject symlinks in every component before canonicalizing the path."""
    path = Path(value).absolute()
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"symlink is not allowed: {current}")
    return path.resolve()


def read_regular(path):
    path = checked_path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"not a regular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f"not a regular file: {path}")
        return stream.read()


def source_bytes(source):
    root = checked_path(source)
    if not root.is_dir():
        raise ValueError(f"source is not a directory: {root}")
    return {rel: read_regular(root / rel) for rel in MANIFEST}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def receipt_bytes(files):
    hashes = {rel: sha256(content) for rel, content in files.items()}
    return canonical_json({
        "version": RECEIPT_VERSION,
        "skill_version": SKILL_VERSION,
        "files": hashes,
        "manifest_sha256": sha256(canonical_json(hashes)),
    }) + b"\n"


def identity(path):
    details = path.lstat()
    return details.st_dev, details.st_ino


def rollback(created):
    """Remove only entries created by this operation, never a replaced entry.

    rmdir refuses directories containing unexpected files. This deliberately
    leaves a partial install if another process has changed the owned tree.
    """
    for path, original, directory in reversed(created):
        try:
            checked_path(path.parent)
            if identity(path) != original:
                continue
            if directory:
                path.rmdir()
            else:
                path.unlink()
        except (OSError, ValueError):
            continue


def write_new(path, content, created):
    checked_path(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        details = os.fstat(stream.fileno())
        created.append((path, (details.st_dev, details.st_ino), False))
        stream.write(content)


def build(source, output):
    files = source_bytes(source)
    output = checked_path(output)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for rel, content in files.items():
            info = zipfile.ZipInfo(f"{NAME}/{rel}", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, content)
    created = []
    try:
        write_new(output, buffer.getvalue(), created)
    except BaseException:
        rollback(created)
        raise
    return output


def install(source, destination):
    files = source_bytes(source)
    destination = checked_path(destination)
    if destination.name != NAME:
        raise ValueError(f"destination basename must be {NAME}")
    if not destination.parent.is_dir():
        raise ValueError("destination parent must already exist")
    created = []
    try:
        # mkdir is exclusive, including for an existing empty directory. POSIX
        # rename would replace that directory, so publication is not atomic.
        destination.mkdir()
        created.append((destination, identity(destination), True))
        for rel, content in files.items():
            path = destination / rel
            if path.parent != destination and not path.parent.exists():
                path.parent.mkdir()
                created.append((path.parent, identity(path.parent), True))
            write_new(path, content, created)
        write_new(destination / RECEIPT, receipt_bytes(files), created)
        verify_install(destination)
    except BaseException:
        rollback(created)
        raise
    return destination


def verify_install(destination):
    destination = checked_path(destination)
    if destination.name != NAME or not destination.is_dir():
        raise ValueError(f"expected an installed {NAME} directory")
    try:
        receipt = json.loads(read_regular(destination / RECEIPT))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid installation receipt") from error
    if not isinstance(receipt, dict) or receipt.get("version") != RECEIPT_VERSION:
        raise ValueError("unsupported installation receipt version")
    if receipt.get("skill_version") != SKILL_VERSION:
        raise ValueError("unsupported installed skill version")
    hashes = receipt.get("files")
    if not isinstance(hashes, dict) or set(hashes) != set(MANIFEST):
        raise ValueError("receipt manifest does not match canonical file list")
    if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
           for value in hashes.values()):
        raise ValueError("invalid SHA-256 in installation receipt")
    if receipt.get("manifest_sha256") != sha256(canonical_json(hashes)):
        raise ValueError("receipt manifest SHA-256 mismatch")
    expected = set(MANIFEST) | {RECEIPT}
    allowed_dirs = {str(Path(rel).parent) for rel in MANIFEST} - {"."}
    found = set()
    for parent, dirs, filenames in os.walk(destination, followlinks=False):
        for name in dirs + filenames:
            path = checked_path(Path(parent) / name)
            rel = path.relative_to(destination).as_posix()
            if name in dirs:
                if rel not in allowed_dirs:
                    raise ValueError(f"unexpected installed directory: {rel}")
            else:
                if rel not in expected:
                    raise ValueError(f"unexpected installed file: {rel}")
                found.add(rel)
    if found != expected:
        raise ValueError("missing installed files: " + ", ".join(sorted(expected - found)))
    for rel in MANIFEST:
        if sha256(read_regular(destination / rel)) != hashes[rel]:
            raise ValueError(f"installed file SHA-256 mismatch: {rel}")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for action in ("build", "install", "verify-install"):
        command = commands.add_parser(action)
        if action != "verify-install":
            command.add_argument("--source", type=Path, default=Path(__file__).absolute().parent.parent)
        command.add_argument("--output" if action == "build" else "--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            build(args.source, args.output)
            print(f"Built {args.output}")
        elif args.command == "install":
            install(args.source, args.destination)
            print(f"Installed and verified {args.destination}")
        else:
            verify_install(args.destination)
            print(f"Verified {args.destination}")
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
