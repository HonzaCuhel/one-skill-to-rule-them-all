import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/package_skill.py"
SPEC = importlib.util.spec_from_file_location("package_skill", SCRIPT)
package = importlib.util.module_from_spec(SPEC)
if SCRIPT.exists():
    SPEC.loader.exec_module(package)


class PackageSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "source"
        self.source.mkdir()
        self.manifest = (
            "SKILL.md", "LICENSE.txt", "agents/openai.yaml", "scripts/observer.py",
            "references/capture.md", "references/review.md", "references/platforms.md",
            "references/storage.md", "references/migration.md", "references/signals.md",
        )
        for rel in self.manifest:
            path = self.source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("fixture " + rel + "\n").encode())

    def install(self, root="codex"):
        dest = self.base / root / "skills" / "task-observer"
        dest.parent.mkdir(parents=True, exist_ok=True)
        package.install(self.source, dest)
        return dest

    def test_codex_and_claude_have_identical_bytes_and_valid_receipts(self):
        targets = [self.install("codex"), self.install("claude")]
        for dest in targets:
            package.verify_install(dest)
            self.assertEqual(sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()),
                             sorted(self.manifest + (".task-observer-install.json",)))
            for rel in self.manifest:
                self.assertEqual((dest / rel).read_bytes(), (self.source / rel).read_bytes())
        self.assertEqual((targets[0] / ".task-observer-install.json").read_bytes(),
                         (targets[1] / ".task-observer-install.json").read_bytes())

    def test_zip_deterministic_allowlist_only(self):
        for rel in ("history/private.md", "proposals/a.md", ".git/config", "scripts/migrate-log.py",
                    "scripts/validate-skill-bundle.py", "scripts/package_skill.py"):
            path = self.source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("excluded", encoding="utf-8")
        outputs = [self.base / "a.skill", self.base / "b.skill"]
        for output in outputs:
            package.build(self.source, output)
        self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
        with zipfile.ZipFile(outputs[0]) as archive:
            self.assertEqual(archive.namelist(), sorted("task-observer/" + rel for rel in self.manifest))
            for rel in self.manifest:
                self.assertEqual(archive.read("task-observer/" + rel), (self.source / rel).read_bytes())

    def test_existing_output_never_overwritten(self):
        output = self.base / "existing.skill"
        output.write_bytes(b"keep")
        with self.assertRaises((ValueError, OSError)):
            package.build(self.source, output)
        self.assertEqual(output.read_bytes(), b"keep")

    def test_existing_destination_even_empty_is_untouched(self):
        dest = self.base / "task-observer"
        dest.mkdir()
        with self.assertRaises((ValueError, OSError)):
            package.install(self.source, dest)
        self.assertEqual(list(dest.iterdir()), [])
        (dest / "keep").write_bytes(b"keep")
        with self.assertRaises((ValueError, OSError)):
            package.install(self.source, dest)
        self.assertEqual((dest / "keep").read_bytes(), b"keep")

    def test_destination_name_must_match(self):
        with self.assertRaises(ValueError):
            package.install(self.source, self.base / "wrong-name")
        self.assertFalse((self.base / "wrong-name").exists())

    def test_source_symlink_file_directory_and_ancestor_rejected(self):
        for rel in ("SKILL.md", "references/capture.md"):
            with self.subTest(rel=rel):
                real = self.source / rel
                payload = real.read_bytes()
                external = self.base / "external"
                external.write_bytes(payload)
                real.unlink()
                real.symlink_to(external)
                with self.assertRaises(ValueError):
                    package.build(self.source, self.base / "bad.skill")
                real.unlink()
                real.write_bytes(payload)
        alias = self.base / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            package.build(alias, self.base / "bad.skill")
        holder = self.base / "holder"
        holder.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError):
            package.build(holder / "source", self.base / "bad.skill")
        (self.source / "references").rename(self.base / "external-references")
        (self.source / "references").symlink_to(self.base / "external-references", target_is_directory=True)
        with self.assertRaises(ValueError):
            package.build(self.source, self.base / "bad.skill")

    def test_symlink_destination_and_parent_rejected(self):
        real = self.base / "real"
        real.mkdir()
        dest = self.base / "task-observer"
        dest.symlink_to(real, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            package.install(self.source, dest)
        alias = self.base / "alias"
        alias.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            package.install(self.source, alias / "task-observer")
        self.assertEqual(list(real.iterdir()), [])

    def test_modified_missing_and_unexpected_install_files_rejected(self):
        dest = self.install()
        original = (dest / "SKILL.md").read_bytes()
        (dest / "SKILL.md").write_bytes(b"modified")
        with self.assertRaises(ValueError):
            package.verify_install(dest)
        (dest / "SKILL.md").write_bytes(original)
        (dest / "extra.md").write_bytes(b"unexpected")
        with self.assertRaises(ValueError):
            package.verify_install(dest)
        (dest / "extra.md").unlink()
        (dest / "SKILL.md").unlink()
        with self.assertRaises(ValueError):
            package.verify_install(dest)

    def test_receipt_manifest_tampering_rejected(self):
        dest = self.install()
        receipt_path = dest / ".task-observer-install.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["files"]["SKILL.md"] = "0" * 64
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            package.verify_install(dest)

    def test_missing_source_does_not_create_destination(self):
        (self.source / "LICENSE.txt").unlink()
        dest = self.base / "task-observer"
        with self.assertRaises((ValueError, OSError)):
            package.install(self.source, dest)
        self.assertFalse(dest.exists())

    def test_verify_rejects_symlink_in_installed_tree(self):
        dest = self.install()
        external = self.base / "external"
        external.write_bytes((dest / "SKILL.md").read_bytes())
        (dest / "SKILL.md").unlink()
        (dest / "SKILL.md").symlink_to(external)
        with self.assertRaises(ValueError):
            package.verify_install(dest)

    def test_failed_install_removes_only_its_created_destination(self):
        dest = self.base / "task-observer"
        real_write = package.write_new
        calls = []

        def fail_third_write(path, content, created):
            calls.append(path)
            if len(calls) == 3:
                raise OSError("simulated disk failure")
            return real_write(path, content, created)

        with mock.patch.object(package, "write_new", fail_third_write):
            with self.assertRaisesRegex(OSError, "simulated disk failure"):
                package.install(self.source, dest)
        self.assertFalse(dest.exists())
        self.assertTrue(self.source.exists())

    def test_rollback_preserves_unexpected_concurrent_file(self):
        dest = self.base / "task-observer"

        def concurrent_change(path, content, created):
            (dest / "user-file").write_bytes(b"keep")
            raise OSError("simulated concurrent change")

        with mock.patch.object(package, "write_new", concurrent_change):
            with self.assertRaises(OSError):
                package.install(self.source, dest)
        self.assertEqual((dest / "user-file").read_bytes(), b"keep")

    def test_cli_build_install_and_verify_without_site_packages(self):
        output = self.base / "cli.skill"
        dest = self.base / "task-observer"
        commands = (
            ("build", "--source", str(self.source), "--output", str(output)),
            ("install", "--source", str(self.source), "--destination", str(dest)),
            ("verify-install", "--destination", str(dest)),
        )
        for command in commands:
            result = subprocess.run([sys.executable, "-S", str(SCRIPT), *command],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        (dest / "SKILL.md").write_bytes(b"modified")
        result = subprocess.run([sys.executable, "-S", str(SCRIPT), *commands[-1]],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("SHA-256 mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
