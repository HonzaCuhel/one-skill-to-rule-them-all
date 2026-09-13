import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "bundle_validator", Path(__file__).resolve().parents[1] / "scripts/validate-skill-bundle.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class BundleValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "example-skill"
        self.root.mkdir()
        self.skill()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def skill(self, description="A valid description.", body="", name="example-skill"):
        self.write("SKILL.md", f"---\nname: {name}\ndescription: {description}\n---\n{body}\n")

    def check(self):
        failures = []
        with contextlib.redirect_stdout(io.StringIO()):
            validator.check_dir(self.root, failures)
        return failures

    def assertFailure(self, fragment):
        failures = self.check()
        self.assertTrue(any(fragment in item for item in failures), failures)

    def test_valid_control(self):
        self.assertEqual(self.check(), [])

    def test_description_yaml_styles_use_decoded_length(self):
        for style in ('"{}"', "'{}'", "|-\n  {}", ">-\n  {}"):
            with self.subTest(style=style):
                self.skill(style.format("a" * 1024))
                self.assertEqual(self.check(), [])
                self.skill(style.format("a" * 1025))
                self.assertFailure("1025 chars > cap 1024")

    def test_literal_and_folded_clipping_newline_counts(self):
        for style in ("|\n  {}", ">\n  {}"):
            with self.subTest(style=style):
                self.skill(style.format("a" * 1023))
                self.assertEqual(self.check(), [])
                self.skill(style.format("a" * 1024))
                self.assertFailure("1025 chars > cap 1024")

    def test_yaml_quoted_escapes_count_after_decoding(self):
        self.skill('"' + r"\u0061" * 1024 + '"')
        self.assertEqual(self.check(), [])

    def test_nonstring_description_rejected(self):
        for value in ("null", "true", "123", "[one, two]", "{one: two}"):
            with self.subTest(value=value):
                self.skill(value)
                self.assertFailure("`description` must be a string")

    def test_empty_description_rejected(self):
        for value in ('""', '"   "', "|-\n  "):
            with self.subTest(value=value):
                self.skill(value)
                self.assertFailure("`description` empty")

    def test_nonstring_name_rejected(self):
        self.root = self.root.rename(self.root.with_name("123"))
        self.skill(name="123")
        self.assertFailure("`name` must be a string")

    def test_invalid_yaml_rejected(self):
        self.skill("[unterminated")
        self.assertFailure("YAML parse error")

    def test_missing_yaml_dependency_fails_explicitly(self):
        with mock.patch.dict("sys.modules", {"yaml": None}):
            self.assertFailure("PyYAML")

    def test_nested_missing_reference_rejected(self):
        self.skill(body="`references/a.md`")
        self.write("references/a.md", "Read `scripts/missing.py`.")
        self.assertFailure("scripts/missing.py")

    def test_nested_markdown_relative_reference(self):
        self.skill(body="[Guide](references/nested/a.md)")
        self.write("references/nested/a.md", '[Next](../b.md#usage "B guide")')
        self.write("references/b.md", "Useful details.")
        self.assertEqual(self.check(), [])
        (self.root / "references/b.md").unlink()
        self.assertFailure("../b.md")

    def test_root_prefixed_backticks_from_nested_file(self):
        self.skill(body="`references/nested/a.md`")
        self.write("references/nested/a.md", "`references/b.md` and `example-skill/scripts/check.py`")
        self.write("references/b.md", "Details.")
        self.write("scripts/check.py", "pass\n")
        self.assertEqual(self.check(), [])

    def test_reference_cycle_terminates(self):
        self.skill(body="[A](references/a.md)")
        self.write("references/a.md", "[B](b.md)")
        self.write("references/b.md", "[A](a.md)")
        self.assertEqual(self.check(), [])

    def test_sibling_qualified_and_external_references_exempt(self):
        self.skill(body="`other-skill/references/a.md` [Other](other-skill/references/a.md) "
                   "[Web](https://example.com/a) [Mail](mailto:hello@example.com) [Anchor](#here)")
        self.assertEqual(self.check(), [])

    def test_markdown_reference_definition_and_image(self):
        self.skill(body="[Guide][guide]\n\n[guide]: references/a.md\n![Diagram](assets/diagram.png)")
        self.write("references/a.md", "Useful guide.")
        self.assertFailure("assets/diagram.png")
        self.write("assets/diagram.png", "image placeholder")
        self.assertEqual(self.check(), [])

    def test_template_and_glob_paths_exempt(self):
        self.skill(body="`references/*.md` `references/?.md` `references/<topic>.md` `references/{{topic}}.md` "
                   "[Example](references/<topic>.md)")
        self.assertEqual(self.check(), [])

    def test_fenced_examples_and_template_slots_stay_valid(self):
        self.skill(body="`references/`\n```markdown\n[Example](references/not-real.md)\n```\n"
                   "~~~\n`references/also-not-real.md`\n~~~\n`references/template.md`")
        self.write("references/template.md", "Template contains {{topic}} slots.")
        self.assertEqual(self.check(), [])

    def test_reserved_folder_cannot_be_mistaken_for_other_skill(self):
        self.skill(body="`references/scripts/missing.py`")
        self.assertFailure("references/scripts/missing.py")

    def test_own_qualified_markdown_link_and_extensionless_link(self):
        self.skill(body="[Guide](example-skill/references/a.md)")
        self.write("references/a.md", "[Licence](../LICENSE)")
        self.assertFailure("../LICENSE")
        self.write("LICENSE", "Licence text")
        self.assertEqual(self.check(), [])

    def test_markdown_spaces_percent_encoding_and_query(self):
        self.skill(body='[Guide](<references/my guide.md> "Title")')
        self.write("references/my guide.md", "[Next](next%20guide.md?version=1#section)")
        self.write("references/next guide.md", "Details")
        self.assertEqual(self.check(), [])

    def test_percent_encoded_escape_and_backtick_escape_rejected(self):
        (self.root.parent / "outside.md").write_text("Private", encoding="utf-8")
        for body in ("[Outside](%2e%2e/outside.md)", "`references/../../outside.md`"):
            with self.subTest(body=body):
                self.skill(body=body)
                self.assertFailure("escapes staged root")

    def test_escape_rejected_even_if_target_exists(self):
        (self.root.parent / "outside.md").write_text("Private", encoding="utf-8")
        self.skill(body="[Outside](../outside.md)")
        self.assertFailure("escapes staged root")

    def test_symlink_file_never_read(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("Private", encoding="utf-8")
        self.skill(body="[Link](references/link.md)")
        (self.root / "references").mkdir()
        (self.root / "references/link.md").symlink_to(outside)
        original = Path.read_text

        def guarded_read(path, *args, **kwargs):
            self.assertFalse(path.is_symlink(), f"read symlink: {path}")
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", guarded_read):
            self.assertFailure("symlink")

    def test_symlink_directory_rejected(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "a.md").write_text("Private", encoding="utf-8")
        (self.root / "references").symlink_to(outside, target_is_directory=True)
        self.skill(body="`references/a.md`")
        self.assertFailure("symlink")

    def test_symlink_skill_never_read(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("Private", encoding="utf-8")
        (self.root / "SKILL.md").unlink()
        (self.root / "SKILL.md").symlink_to(outside)
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
            self.assertFailure("symlink")

    def test_unreachable_symlink_never_read(self):
        self.write("references/a.md", "Real reference.")
        (self.root / "references/link.md").symlink_to(self.root / "references/a.md")
        self.assertFailure("symlink")


    def test_nested_markdown_reserved_folder_is_file_relative(self):
        self.skill(body="`references/a.md`")
        self.write("references/a.md", "[Next](assets/b.md) and `assets/root.txt`")
        self.write("references/assets/b.md", "Nested asset guide.")
        self.write("assets/root.txt", "Root asset.")
        self.assertEqual(self.check(), [])
        (self.root / "references/assets/b.md").unlink()
        self.write("assets/b.md", "Wrong location must not satisfy the link.")
        self.assertFailure("assets/b.md")

    def test_markdown_escaped_punctuation_in_destinations(self):
        self.skill(body=r"[Guide](references/my\_guide.md)")
        self.write("references/my_guide.md", "[Next][next]\n\n" + r"[next]: next\_guide.md")
        self.write("references/next_guide.md", "Next guide.")
        self.assertEqual(self.check(), [])
        (self.root / "references/next_guide.md").unlink()
        self.assertFailure("next_guide.md")

    def test_escaped_markdown_punctuation_does_not_bypass_root_safety(self):
        self.skill(body=r"[Outside](\.\./outside.md)")
        self.assertFailure("escapes staged root")

    def test_reachable_structured_text_and_source_references(self):
        examples = {
            "references/config.yaml": 'guide: "`references/missing.md`"',
            "references/config.yml": 'guide: "`references/missing.md`"',
            "references/config.json": '{"guide": "`references/missing.md`"}',
            "scripts/check.py": '# See `references/missing.md`.',
            "scripts/check.js": '// See `references/missing.md`.',
            "scripts/check.sh": '# See `references/missing.md`.',
        }
        for rel, body in examples.items():
            with self.subTest(rel=rel):
                self.skill(body=f"`{rel}`")
                self.write(rel, body)
                self.assertFailure("references/missing.md")
                self.write("references/missing.md", "Now present.")
                self.assertEqual(self.check(), [])
                (self.root / "references/missing.md").unlink()

    def test_reachable_binary_is_not_scanned_as_text(self):
        self.skill(body="![Diagram](assets/diagram.png)")
        self.write("assets/diagram.png", "`references/not-a-real-dependency.md`")
        self.assertEqual(self.check(), [])


if __name__ == "__main__":
    unittest.main()
