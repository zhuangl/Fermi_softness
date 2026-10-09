# Contributing

[中文](CONTRIBUTING.zh-CN.md) · [Developer guide](docs/developer-guide.en.md)

Install `.[gui,dev]`, run `pytest -q`, then `ruff check src tests validation`.
Keep numerical code independent of Qt/VTK so it runs on compute servers.
Check documentation with `python validation/generate_cli_reference.py --check`
and `python validation/check_docs.py`. Update both language versions together.

Every new input format must have an independent reference check. Useful tests
include direct Fourier sums, analytical fields, coefficient-norm integrals and
VASP's own partial densities. Do not accept a visually plausible image as a
numerical validation. Include failing or truncated inputs in format tests.

Report bugs with the version, command, traceback, metadata and a small shareable
fixture. Never attach POTCAR or proprietary VASP source. An anonymized or
synthetic fixture is preferable when a calculation cannot be distributed.

Before changing units, degeneracies, symmetry or PAW normalization, update the
method contract and prove the new convention with independent tests. Keep
unsupported or incompletely tested features explicit in documentation.

Pull requests should explain the user-visible result and provide test evidence.
Images should be inspected at their actual exported resolution; preserve saved
scene files so figures are reproducible.
