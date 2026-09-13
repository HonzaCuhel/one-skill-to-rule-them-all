# Contributing to this portable fork

This repository is Jan Čuhel's portable adaptation of Eoghan Henn's Task Observer. Please distinguish this fork's behavior from upstream v3.2. The original contribution policy is preserved under [historical docs](docs/upstream-v3.2/CONTRIBUTING.md).

Prefer focused changes with a concrete trigger and before/after result. For executable defects add a failing regression test, make the smallest useful fix, and run the relevant tests. For skill wording, describe the intended behavioral difference and how to evaluate it; a substring assertion is not evidence of model behavior.

Run `python3 -m unittest discover -s tests -v` with the development dependencies. Validate an installed bundle as shown in README. Keep one canonical runtime bundle; host adapters belong in the shared reference instead of duplicated skills. Do not put personal observations or client data into fixtures, issues or bundles.

Search both upstream issues and pull requests before proposing an upstream contribution. This fork's storage format is a deliberate change, so do not present it as a transparent text cleanup. Validator fixes can be reviewed separately. Credit existing reports and solutions; the earlier Codex port is acknowledged in README.

Contributions use CC BY 4.0, retaining original attribution and identifying changes. We welcome corrections to compatibility claims backed by the host/interpreter version, commands, and observable result. Do not describe a platform as tested merely because its install path is documented.
