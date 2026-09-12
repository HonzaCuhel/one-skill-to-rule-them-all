# Unsent upstream issue drafts

These are local drafts against `7518a858cf5b550bf3dc61b1b625f4cb0b5fa87f`.
Recheck current HEAD and issues/PRs before submitting. Neither an issue nor a
PR has been opened. The patches suggested below have not been implemented.

## Draft 1: Bundle validator accepts overlong literal-block descriptions

**Title:** validate-skill-bundle: measure the parsed description, including literal blocks

The validator accepts a skill whose description exceeds its own 1024-character
limit when the description uses a YAML literal block (`|`). A 1100-character
inline description is rejected, while the same content in a literal block
passes. `folded_description()` returns the one-character indicator `|`, and
`check_dir()` measures that instead of the value it already parsed with YAML.

Verified on upstream commit `7518a85`, Python 3.8.8, PyYAML 6.0.2. Both cases
use a directory named `sample-skill`, matching its frontmatter name, and no
other files or references. The valid short description also passes.

Minimal input shape:

```yaml
name: sample-skill
description: |
  a line containing 1100 characters
```

The last line describes the fixture; the runnable reproduction constructs the
actual 1100-character string, so it does not accidentally test the short text
shown above. It also includes the opening/closing SKILL frontmatter fences.

Suggested fix: validate the type and length of the parsed description, covering
literal and folded block variants, quoting, empty strings and non-string YAML
values. Explicitly define the behavior when PyYAML is absent; an unchecked
fallback must not report equivalent validation.

Adjacent: #61 fixed directory-name handling, #81/#134 concern observation-log
header detection. This case concerns description-length validation of a skill
bundle. A repository index search found no exact duplicate, but I would be
happy to attach the reproduction to an existing item if it belongs elsewhere.

Reproduction prepared locally: `python3 -B research/reproduce_upstream.py`,
case `F01_LITERAL_DESCRIPTION`, with controls `CONTROL_VALID` and
`CONTROL_LONG_INLINE`. The script will be attached or linked when submitted;
it is not presently available on the public fork's main branch.

Prepared with Codex. Synthetic local reproduction only; no production failure
rate or behavioral performance claim.

## Draft 2: ID/archive snippet fails native macOS Bash syntax check

**Title:** The ID/archive snippet does not parse in macOS Bash 3.2

Against `7518a85`, the complete Bash fence under “Id and filename” fails a
syntax-only check in macOS's bundled `/bin/bash` 3.2.57. The reported failure
is near `;;` in the `case` nested inside the command substitution. This occurs
before any log reads or writes; it is not a permissions or missing-directory
failure.

```text
/bin/bash: -c: line 9: syntax error near unexpected token `;;'
```

The exact snippet is extracted from the pinned SKILL.md and passed to
`/bin/bash --noprofile --norc -n -c`. No agent rewrite or shell translation
is involved. Prepared local reproduction: `research/reproduce_upstream.py`,
case `F03_MACOS_BASH_SYNTAX`.

The text specifies bash but does not establish a tested minimum version at
this snippet. Suggested direction: document and test the minimum shell, or
move the operation to a portable helper with equivalent failure behavior.
I have not tested Bash 5/Linux or Windows in this reproduction.

This belongs next to the open portability issue #77; the old #16 was about
GNU/BSD utilities rather than this parser behavior. Prefer adding the fixture
there if a separate issue would fragment that work.

## Other results to coordinate, not bundle into a large first PR

- `F02_TRANSITIVE_REFERENCE`: valid direct reference to a file which names a
  missing further bundled reference is accepted. The direct-missing control
  is rejected. Scope: validator only.
- `F04_ARCHIVE_OVERWRITE`: the isolated exact archival decision body overwrites
  a pre-existing archive destination of the same filename with exit 0.
- `F05_ARCHIVE_STATUS_SUBSTRING`: that body can archive an open entry if an
  unrelated header field contains `status: actioned` and `resolved` is stale.
  This requires the stale date; it is not a claim that normal new open entries
  all archive. The ordinary-open control stays active.
- F04/F05 test the body outside the surrounding command substitution because
  the complete snippet cannot parse in the tested native shell. Keep this
  qualification in any report.
- The migration overwrite and decreasing floor are already covered by PR #119.
  Offer regression fixtures there and preserve its contributors' credit.
