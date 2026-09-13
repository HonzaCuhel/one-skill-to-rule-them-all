# Task Observer — one skill for coding agents

[![Tests](https://github.com/HonzaCuhel/one-skill-to-rule-them-all/actions/workflows/tests.yml/badge.svg)](https://github.com/HonzaCuhel/one-skill-to-rule-them-all/actions/workflows/tests.yml)

Turn task corrections into scoped, reviewable skill improvements. **One shared skill bundle for Claude Code, Codex and compatible coding agents**, with native discovery instructions and a small local observation store.

This is Jan Čuhel's portable fork of [Eoghan Henn's One Skill to Rule Them All](https://github.com/rebelytics/one-skill-to-rule-them-all), based on upstream commit `7518a85`. The original methodology and CC BY 4.0 attribution are retained. [AllstarGER's earlier Codex port](https://github.com/AllstarGER/one-skill-to-rule-them-all) predates this work; this is not the first Codex adaptation.

**Portable version 1.0.0 changes the storage format and workflow.** It is not a drop-in upstream v3 update. Existing observation logs remain untouched; read the [migration guide](references/migration.md).

## What changes in this fork

- One canonical `SKILL.md`, six shared references and one Python helper. CC and Codex receive identical runtime bytes.
- Native Codex `.agents/skills` and Claude Code `.claude/skills` discovery; no guessed instruction precedence or automatically installed hooks.
- UUID observations, retry event keys and immutable JSON revisions. Concurrent writers cannot replace an existing revision.
- Explicit scope, source kind, counterevidence and private observations. A tool output is evidence, not permission.
- Separate proposed, installed and behaviorally validated states; source-based staging and held-out evaluation guidance.
- Actual YAML validation and recursive local-reference checks, with regression tests.
- An allowlisted installer that refuses existing destinations, plus a reproducible bundle and installation hash receipt.

The observer helps maintain a growing skill library. For an AI engineer, its useful output is a traceable hypothesis such as “the evaluation workflow confuses a build check with a deployed behavior check,” followed by a small patch and a relevant test. It is not model training, a desktop monitor, an autonomous self-updater or proof that an agent will always remember to observe. For a few occasional skills, a direct edit may cost less.

## Try it in a project

Requires Python 3.8+ and a filesystem supporting exclusive hard links for the data store. The runtime and installer use the standard library only.

Clone this fork:

```bash
git clone https://github.com/HonzaCuhel/one-skill-to-rule-them-all.git
cd one-skill-to-rule-them-all
```

Create the host's project skill parent directory if absent. Then choose **one** command and replace the example with an actual absolute path:

```bash
# Codex
python3 scripts/package_skill.py install --destination /absolute/project/.agents/skills/task-observer

# Claude Code
python3 scripts/package_skill.py install --destination /absolute/project/.claude/skills/task-observer
```

The destination's parent must already exist; `task-observer` itself must not. The installer refuses symlinks in paths, including ancestor aliases; on macOS use the canonical `/private/tmp` instead of `/tmp` for temporary trials. Installation neither initializes a store nor changes AGENTS.md, CLAUDE.md, global settings or schedules.

In a fresh agent session invoke `$task-observer` (Codex) or `/task-observer` (Claude Code). Start with a bounded retrospective. For persistence, explicitly select a private absolute data directory outside the installed skill and initialize it using the installed helper:

```bash
python3 /absolute/project/.agents/skills/task-observer/scripts/observer.py --workspace /absolute/private/observer-data init
python3 /absolute/project/.agents/skills/task-observer/scripts/observer.py --workspace /absolute/private/observer-data doctor
```

Use the Claude install path instead when appropriate. Give the chosen workspace to the agent. No workspace means an explicitly unsaved handoff, not an invented global memory location.

See the [user guide](USER-GUIDE.md) for a complete capture/review example and the [host matrix](docs/COMPATIBILITY.md) for verification limits.

## Build and test

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
mkdir -p dist
python3 scripts/package_skill.py install --destination "$PWD/dist/task-observer"
python3 scripts/validate-skill-bundle.py "$PWD/dist/task-observer"
python3 scripts/package_skill.py build --output "$PWD/dist/task-observer.skill"
```

Use a fresh output directory on subsequent runs; the tools deliberately refuse overwrites. The ZIP contains only the ten runtime files from the explicit manifest. Research, historical sources, tests and packaging tools are excluded. The install receipt checks consistency with recorded hashes; it is not a release signature.

CI runs helper, validator and packaging tests across Linux, macOS and Windows. A green software test does **not** establish native skill activation or improved model outcomes. [Compatibility and validation](docs/COMPATIBILITY.md) states what was actually measured.

## Project notes

- [Changes and upstream coordination](docs/UPSTREAM-CHANGES.md): reproducible fixes, current issue/PR overlap and contributions that can be proposed separately.
- [Changelog](CHANGELOG.md): declared behavior changes.
- [Contributing](CONTRIBUTING.md): focused changes, evidence and attribution.
- [Historical v3.2 references](docs/upstream-v3.2/README.md): source material, excluded from installation.
- [License](LICENSE.txt): CC BY 4.0. Original by Eoghan Henn / rebelytics; portable changes by Jan Čuhel. No endorsement by upstream, Anthropic or OpenAI is implied.
