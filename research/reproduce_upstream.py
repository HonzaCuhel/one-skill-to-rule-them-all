#!/usr/bin/env python3
"""Bounded synthetic reproductions; never touches installed skills or real logs.

Run with Python 3. Every mutation is inside a TemporaryDirectory. A successful
reproduction is evidence of current behavior, not a passing quality gate.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = "7518a858cf5b550bf3dc61b1b625f4cb0b5fa87f"
sys.dont_write_bytecode = True


def run(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, timeout=20, **kw)


def main():
    sources = ["SKILL.md", "scripts/migrate-log.py", "scripts/validate-skill-bundle.py"]
    for name in sources:
        expected = subprocess.check_output(["git", "show", f"{PIN}:{name}"], cwd=ROOT)
        if expected != (ROOT / name).read_bytes():
            raise SystemExit(f"Source differs from audited pin: {name}")
    spec = importlib.util.spec_from_file_location("upstream_validator", ROOT / sources[2])
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    results = []
    with tempfile.TemporaryDirectory(prefix="observer-synthetic-") as tmp:
        base = Path(tmp)
        skill = base / "sample-skill"
        skill.mkdir()
        skill_md = skill / "SKILL.md"

        def validate(text):
            skill_md.write_text(text, encoding="utf-8")
            fails = []
            validator.check_dir(skill, fails)
            return fails

        normal = "---\nname: sample-skill\ndescription: A valid short description.\n---\n\nObserve.\n"
        control = validate(normal)
        results.append({"id": "CONTROL_VALID", "expected": "accept valid skill", "observed_failures": control, "control_passed": not control})
        overlong = "---\nname: sample-skill\ndescription: |\n  " + "x" * 1100 + "\n---\n\nObserve.\n"
        failures = validate(overlong)
        results.append({"id": "F01_LITERAL_DESCRIPTION", "expected": "reject description longer than 1024", "observed_failures": failures, "reproduced": not failures, "actual_description_chars_without_final_newline": 1100, "regex_measured_chars": len(validator.folded_description(validator.frontmatter(overlong)))})

        # A normal inline description over the cap must fail: positive control.
        failures = validate("---\nname: sample-skill\ndescription: " + "x" * 1100 + "\n---\n\nObserve.\n")
        results.append({"id": "CONTROL_LONG_INLINE", "observed_failures": failures, "control_passed": any("cap" in f for f in failures)})

        validate(normal)
        refs = skill / "references"
        refs.mkdir()
        (refs / "review.md").write_text("Read `references/missing.md` before reviewing.\n", encoding="utf-8")
        failures = validate(normal + "\nRead `references/review.md` for review.\n")
        results.append({"id": "F02_TRANSITIVE_REFERENCE", "expected": "reject missing bundled reference reachable through another reference", "observed_failures": failures, "reproduced": not failures})
        failures = validate(normal + "\nRead `references/missing.md`.\n")
        results.append({"id": "CONTROL_DIRECT_REFERENCE", "observed_failures": failures, "control_passed": any("missing" in f for f in failures)})

        # Literal documented archival/ID block, only its documented path and
        # slug placeholders substituted. No production data or dangerous payload.
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        blocks = re.findall(r"(?m)^[ \t]*```bash\n(.*?)\n[ \t]*```[ \t]*$", skill_text, re.S)
        snippet = next(b for b in blocks if "next_id=$(( hi + 1 ))" in b)
        parsed = run(["/bin/bash", "--noprofile", "--norc", "-n", "-c", snippet])
        results.append({"id": "F03_MACOS_BASH_SYNTAX", "expected": "documented bash snippet parses on native macOS bash", "bash_version": run(["/bin/bash", "--version"]).stdout.splitlines()[0], "returncode": parsed.returncode, "stderr": parsed.stderr, "reproduced": parsed.returncode != 0 and "syntax error" in parsed.stderr and ";;" in parsed.stderr})
        # Native bash cannot parse the complete snippet. Test the exact archival
        # decision body separately, outside its surrounding command substitution.
        # These are isolated algorithm reproductions, NOT full-snippet successes.
        archive_body = snippet[snippet.index("    hdr=$(awk"):snippet.index("  done; printf")]

        def archive_case(name, title, status, collision=False):
            workspace = base / name
            log = workspace / "skill-observations" / "observation-log"
            (log / "archive").mkdir(parents=True)
            source = log / "0001-example.md"
            source.write_text(f'---\nid: 1\ntitle: "{title}"\nstatus: {status}\nresolved: 2000-01-01\n---\nACTIVE SYNTHETIC BODY\n', encoding="utf-8")
            dest = log / "archive" / source.name
            if collision:
                dest.write_text("ARCHIVED SYNTHETIC ORIGINAL\n", encoding="utf-8")
            shell = 'd="$1"; today=$(date +%F); for f in "$d/0001-example.md"; do\n' + archive_body + '\ndone\n'
            result = run(["/bin/bash", "--noprofile", "--norc", "-c", shell, "fixture", str(log)], env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
            return {"returncode": result.returncode, "source_exists": source.exists(), "archive_body": dest.read_text(encoding="utf-8") if dest.exists() else None, "stderr": result.stderr}

        observed = archive_case("collision space", "Resolved synthetic entry", "actioned", True)
        results.append({"id": "F04_ARCHIVE_OVERWRITE", "test_scope": "isolated exact archival decision body", "expected": "preserve pre-existing archive destination or refuse collision", "observed": observed, "reproduced": observed["returncode"] == 0 and observed["archive_body"] != "ARCHIVED SYNTHETIC ORIGINAL\n"})
        observed = archive_case("title-match", "Investigate status: actioned parsing", "open")
        results.append({"id": "F05_ARCHIVE_STATUS_SUBSTRING", "test_scope": "isolated exact archival decision body", "expected": "keep status open even with a stale resolved field", "observed": observed, "reproduced": observed["returncode"] == 0 and not observed["source_exists"]})
        observed = archive_case("control-open", "Ordinary open entry", "open")
        results.append({"id": "CONTROL_OPEN_ARCHIVE", "observed": observed, "control_passed": observed["returncode"] == 0 and observed["source_exists"]})

        legacy = base / "legacy.md"
        legacy.write_text("### Observation 7: Synthetic migration\n**Status:** OPEN\n**Date:** 2026-09-12\n**Skill:** sample-skill\n**Issue:** Synthetic evidence.\n", encoding="utf-8")
        out = base / "converted"
        (out / "archive").mkdir(parents=True)
        original = out / "0007-synthetic-migration.md"
        original.write_text("PREEXISTING SYNTHETIC OBSERVATION\n", encoding="utf-8")
        floor = out / "archive" / ".id-floor"
        floor.write_text("99\n", encoding="utf-8")
        result = run([sys.executable, str(ROOT / sources[1]), "--convert", str(legacy), "--out", str(out)])
        results.append({"id": "KNOWN_PR119_MIGRATION", "already_reported": "https://github.com/rebelytics/one-skill-to-rule-them-all/pull/119", "returncode": result.returncode, "overwritten": original.read_text() != "PREEXISTING SYNTHETIC OBSERVATION\n", "floor_after": floor.read_text().strip(), "reproduced": original.read_text() != "PREEXISTING SYNTHETIC OBSERVATION\n" and floor.read_text().strip() == "7"})

    report = {"upstream_commit": PIN, "python": sys.version.split()[0], "platform": platform.platform(), "scope": "synthetic local repros only; no live agent efficacy evaluation", "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}, "results": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(r.get("control_passed", r.get("reproduced", False)) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
