#!/usr/bin/env python3
"""
validate-skill-bundle.py — the pre-delivery gate, as assertions.

Checks a staged skill directory (and optionally its packed .skill bundle)
against the criteria the INSTALLER enforces, not against what seems
sensible. Every check compares a measurement to a bound in the same step:
an unasserted metric manufactures confidence that no defect exists.

Usage
-----
  python3 validate-skill-bundle.py <staged-skill-dir> [--bundle file.skill] [--pack out.skill]

  --pack   writes a well-formed bundle (POSIX separators on any platform)
           after the directory checks pass, then validates it.

Exit status 0 = every check passed; 1 = at least one failed (all failures
are listed, not just the first).

Limits are stated as numbers and labelled with where they come from, so
the check is implementable without guessing and can be updated when the
consumer changes them.
"""

import os
import pathlib
import re
import struct
import string
import sys
import zipfile
from urllib.parse import unquote, urlsplit

MAX_DESCRIPTION_CHARS = 1024   # installer's documented cap on the decoded YAML description
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")   # kebab-case
BUNDLE_DIRS = {"references", "scripts", "assets"}
TEXT_SUFFIXES = {".md", ".txt", ".yml", ".yaml", ".json"}
# Reachability is a lexical scan over this explicit text allowlist. It does not
# interpret imports, execute code, discover computed references, or scan binary
# formats. Source comments/strings follow the same citation conventions as prose.
REFERENCE_TEXT_SUFFIXES = TEXT_SUFFIXES | {
    ".py", ".sh", ".bash", ".zsh", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".rb", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".java", ".swift",
    ".toml", ".ini", ".cfg", ".xml", ".html", ".css",
}
MARKDOWN_ESCAPE_RE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
# Inline links/images, including angle-wrapped destinations and one level of
# balanced parentheses. Reference definitions cover full/collapsed/shortcut links.
DESTINATION = r"(<[^>\n]+>|(?:\\.|[^()\s]|\([^()]*\))+)"
MARKDOWN_LINK_RE = re.compile(r"\[[^\]\n]*\]\(\s*" + DESTINATION)
MARKDOWN_DEF_RE = re.compile(r"(?m)^ {0,3}\[[^\]\n]+\]:[ \t]*" + DESTINATION)
BUILD_JUNK = {"__pycache__", ".DS_Store"}
# Edit residue: strings that only ever enter a file through a failed
# replacement, an unresolved template slot or an unfinished merge. The gate
# checks bundle FORM; this is the one CONTENT assertion, because a literal
# backreference passed apply, gate and install once.
SLOT_WHY = "unresolved template slot"
RESIDUE_RES = [
    (re.compile(r"(?m)^\\[0-9]\s*$"), "literal regex backreference on its own line"),
    (re.compile(r"(?<![\w`])\\[1-9](?![\w])"), "literal regex backreference in prose"),
    (re.compile(r"(?m)^(<<<<<<<|=======|>>>>>>>)( |$)"), "merge conflict marker"),
    (re.compile(r"\{\{[A-Za-z_][A-Za-z0-9_ .-]*\}\}"), SLOT_WHY),
    (re.compile(r"\b(TODO|FIXME|XXX)\b: ?(fill|replace|write)", re.I), "placeholder note left in"),
]
# A file that IS a template carries its slots as the deliverable, not as
# residue: exempt it from the SLOT rule only — every other residue rule and
# every other gate check still runs on it, so the exemption never becomes the
# hand-zip that also skips the checks nobody questioned.
TEMPLATE_MARKER = "<!-- template: slots intentional -->"


def slots_are_intentional(path, body):
    return "template" in str(path).lower() or body.lstrip().startswith(TEMPLATE_MARKER)
SECOND_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n\s*(---\n|name:|description:)", re.S)


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) + "\n" if m else None


def without_fences(body):
    """Ignore literal examples; only prose references are bundle dependencies."""
    lines = []
    fence = None
    for line in body.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", line):
                fence = None
            lines.append("\n")
        elif marker:
            fence = marker.group(1)
            lines.append("\n")
        else:
            lines.append(line)
    return "".join(lines)


def cited_paths(body):
    prose = without_fences(body)
    for span in re.findall(r"`([^`\n]+)`", prose):
        parts = pathlib.PurePosixPath(span).parts
        # Backticks denote dependencies only for the reserved bundle folders;
        # arbitrary command strings and runtime paths remain examples.
        if (not any(c.isspace() for c in span) and "?" not in span and not span.endswith("/")
                and pathlib.PurePosixPath(span).suffix
                and any(part in BUNDLE_DIRS for part in parts)):
            yield span, False
    prose = re.sub(r"`[^`\n]*`", "", prose)
    for regex in (MARKDOWN_LINK_RE, MARKDOWN_DEF_RE):
        for match in regex.finditer(prose):
            target = match.group(1)
            target = target[1:-1] if target.startswith("<") else target
            yield MARKDOWN_ESCAPE_RE.sub(r"\1", target), True


def safe_local_target(root, source, target, fails, is_markdown=False):
    """Return a local file without following a symlink or leaving the root.

    Bare reserved-folder backticks and own-skill-qualified paths are root-relative.
    Markdown destinations are source-file-relative, including reserved folders.
    <other-skill>/references|scripts|assets is an intentional external citation.
    """
    # These are documented template/glob conventions, not concrete files.
    if any(token in target for token in ("*", "{{", "}}", "<", ">", "${")):
        return None
    try:
        url = urlsplit(target)
    except ValueError:
        fails.append(f"invalid cited path in {source.relative_to(root)}: {target!r}")
        return None
    if url.scheme or url.netloc or not url.path:
        return None
    rel = unquote(url.path)
    if "\x00" in rel or "\\" in rel:
        fails.append(f"invalid cited path in {source.relative_to(root)}: {target!r}")
        return None
    parts = pathlib.PurePosixPath(rel).parts
    if len(parts) > 1 and parts[0] == root.name:
        candidate = root.joinpath(*parts[1:])
    elif (len(parts) > 2 and parts[0] not in BUNDLE_DIRS
          and NAME_RE.fullmatch(parts[0]) and parts[1] in BUNDLE_DIRS):
        return None
    elif not is_markdown and parts and parts[0] in BUNDLE_DIRS and not rel.startswith("./"):
        candidate = root / rel
    else:
        candidate = source.parent / rel
    # Normalize lexically, then inspect each component before any file read.
    # Reject symlinks even when they resolve to another in-bundle file.
    lexical = pathlib.Path(os.path.abspath(candidate))
    try:
        lexical.relative_to(root)
    except ValueError:
        fails.append(f"cited path escapes staged root in {source.relative_to(root)}: {target}")
        return None
    current = root
    for part in candidate.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            fails.append(f"symlink in cited path in {source.relative_to(root)}: {target}")
            return None
    if not lexical.is_file():
        fails.append(f"cited path missing from staged set in {source.relative_to(root)}: {target} "
                     "— qualify other-skill citations as `<skill-name>/references/file.md`")
        return None
    return lexical


def check_references(root, text, fails):
    pending = [(root / "SKILL.md", text)]
    visited = set()
    while pending:
        source, body = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        for target, is_markdown in sorted(set(cited_paths(body))):
            path = safe_local_target(root, source, target, fails, is_markdown)
            if path and path not in visited and path.suffix.lower() in REFERENCE_TEXT_SUFFIXES:
                pending.append((path, path.read_text(encoding="utf-8", errors="replace")))


def staged_files(root, fails):
    """Inspect the entire staged tree, pruning symlinks before content checks."""
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs[:] + files:
            path = pathlib.Path(directory) / name
            if name in BUILD_JUNK or path.suffix == ".pyc" or name.startswith(".~lock"):
                fails.append(f"build artefact in staged tree: {path.relative_to(root)}")
            if path.is_symlink():
                fails.append(f"symlink in staged tree: {path.relative_to(root)}")
                if name in dirs:
                    dirs.remove(name)
            elif name in files:
                yield path


def check_dir(skill_dir, fails):
    # Resolve before comparing names: Path('.').name is '' for a relative
    # argument naming the current directory, which false-fails a correct
    # bundle and blames the frontmatter for an argument problem.
    skill_dir = pathlib.Path(skill_dir).absolute()
    if skill_dir.is_symlink():
        fails.append("symlink used as staged root"); return
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_symlink():
        fails.append("symlink used as SKILL.md"); return
    if not skill_md.is_file():
        fails.append("SKILL.md missing"); return
    text = skill_md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        fails.append("frontmatter: no leading --- block"); return
    try:
        import yaml  # validator-only dependency; never substitute a regex parser
        data = yaml.safe_load(fm)
        if not isinstance(data, dict):
            fails.append("frontmatter: does not parse to a mapping")
            data = {}
    except ImportError:
        fails.append("frontmatter: PyYAML is required; install it with `python3 -m pip install PyYAML`")
        return
    except yaml.YAMLError as e:
        fails.append(f"frontmatter: YAML parse error: {e}"); data = {}
    name = data.get("name")
    if not isinstance(name, str):
        fails.append("frontmatter: `name` must be a string")
    elif not name.strip():
        fails.append("frontmatter: `name` empty")
    elif not NAME_RE.fullmatch(name):
        fails.append(f"frontmatter: `name` not kebab-case: {name!r}")
    elif name != skill_dir.name:
        fails.append(f"frontmatter: `name` {name!r} != directory {skill_dir.name!r}")
    desc = data.get("description")
    if not isinstance(desc, str):
        fails.append("frontmatter: `description` must be a string")
    elif not desc.strip():
        fails.append("frontmatter: `description` empty")
    elif len(desc) > MAX_DESCRIPTION_CHARS:
        fails.append(f"description {len(desc)} chars > cap {MAX_DESCRIPTION_CHARS}")
    elif len(desc) > 900:
        print(f"warn: description {len(desc)} chars (cap {MAX_DESCRIPTION_CHARS}) — near the boundary")
    check_references(skill_dir, text, fails)
    # exactly one frontmatter block: a second `---` block (or stray
    # name:/description: lines) directly after the first is a duplicated
    # header that every field check passes by construction
    if SECOND_FRONTMATTER_RE.match(text):
        fails.append("frontmatter: a second frontmatter block follows the first")
    for p in staged_files(skill_dir, fails):
        # Content residue in every text file, not only reachable references.
        if p.suffix.lower() in TEXT_SUFFIXES:
            body = p.read_text(encoding="utf-8", errors="replace")
            # code is where backreferences legitimately live: blank out
            # fenced blocks and inline spans, keeping line numbers intact
            prose = re.sub(r"(?ms)^```.*?^```[ \t]*$", lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)
            prose = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), prose)
            rel = p.relative_to(skill_dir)
            exempt_slots = slots_are_intentional(rel, body)
            for rx, why in RESIDUE_RES:
                if why == SLOT_WHY and exempt_slots:
                    continue
                m = rx.search(prose)
                if m:
                    line = body.count("\n", 0, m.start()) + 1
                    fails.append(f"edit residue in {p.relative_to(skill_dir)}:{line}: {why} ({m.group(0).strip()!r})")


def pack(src, out):
    """Always writes POSIX separators, on any platform."""
    src = pathlib.Path(src)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            arc = f"{src.name}/{f.relative_to(src).as_posix()}"
            assert "\\" not in arc, arc
            z.write(f, arcname=arc)


def check_bundle(path, fails):
    """Central directory as raw bytes: a convenience reader (zipfile.namelist)
    rewrites 0x5C to '/' and would report a malformed archive as clean."""
    data, i, n_members = pathlib.Path(path).read_bytes(), 0, 0
    while True:
        i = data.find(b"PK\x01\x02", i)
        if i < 0:
            break
        n, m, k = (struct.unpack_from("<H", data, i + o)[0] for o in (28, 30, 32))
        name = data[i + 46:i + 46 + n]
        n_members += 1
        if b"\x5c" in name:
            fails.append(f"bundle: backslash in member path {name!r} (installer rejects it)")
        i += 46 + n + m + k
    if n_members == 0:
        fails.append("bundle: no members found")


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    skill_dir = argv[1]
    bundle = pack_to = None
    if "--bundle" in argv:
        bundle = argv[argv.index("--bundle") + 1]
    if "--pack" in argv:
        pack_to = argv[argv.index("--pack") + 1]
    fails = []
    check_dir(skill_dir, fails)
    if pack_to and not fails:
        pack(skill_dir, pack_to); bundle = pack_to
        print(f"packed {pack_to}")
    if bundle:
        check_bundle(bundle, fails)
    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: all gate checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
