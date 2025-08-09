# Documentation Best Practices for a Python Package

## Core, visible docs (front door)

* **README.md**
  Purpose, one‑liner, badges (PyPI, CI, coverage, license), install commands (pip/uv/conda), a 60‑second **Quickstart**, 2–3 **usage snippets**, links to docs/FAQ/changelog.
* **Project metadata (pyproject.toml)**
  Clear `name`, `description`, `readme` (points at README), `license`, `authors`, **Trove classifiers** (Python versions, license, topic), `project.urls` (Homepage, Docs, Changelog, Issues, Discussions), `dependencies`, `optional-dependencies` (e.g., `dev`, `docs`, `tests`). This drives what users see on PyPI.
* **LICENSE**
  Standard SPDX license (MIT/Apache‑2.0/BSD‑3‑Clause, etc.).
* **CHANGELOG.md**
  Keep‑a‑Changelog style; human‑readable summaries per release, with dates and links to tags. Note deprecations & breaking changes explicitly.
* **CONTRIBUTING.md**
  Dev setup (uv/pipx/rye/poetry), running tests (`pytest`), lint/format (ruff/black), type checking (pyright/mypy), commit style, branch strategy, how to file issues/PRs.
* **CODE\_OF\_CONDUCT.md**
  Contributor Covenant (or similar), contact for moderation.
* **SECURITY.md**
  How to report vulnerabilities, supported versions, expected response SLAs.
* **CITATION.cff** (optional but nice)
  Lets users cite your package; GitHub renders a “Cite this repository” button.
* **ROADMAP.md** (optional)
  Near‑term goals, big bets, stability timeline.

## API & user guidance (the “how do I use this?” layer)

* **Docstrings first**
  NumPy/Google style, with types. Keep examples minimal but runnable. This feeds your API docs.
* **Hosted docs site** (Sphinx or MkDocs)

  * **Getting Started / Tutorials**: narrative guides with small, complete examples.
  * **How‑To recipes**: focused tasks (configure X, plug into Y).
  * **Reference**: auto‑generated from code (interlinks, parameter docs).
  * **Explanation / Design notes**: tradeoffs, architecture, key abstractions.
  * **FAQ/Troubleshooting**: common import/runtime errors, version pin conflicts.
  * **Migration guides** for breaking releases.
  * Versioned docs tied to tags.
* **Examples/** (or `docs/examples/`)
  Small scripts and, if relevant, Jupyter notebooks tested via CI (e.g., `pytest --nbmake`).

## Quality signals (trust & maintainability)

* **Badges**
  CI status, coverage %, PyPI version, Python versions, license, docs build link.
* **Testing docs**
  How to run tests quickly; note minimum supported Python, OS matrix, and how to run slow/optional tests.
* **Performance notes** (if relevant)
  Big‑O, microbenchmarks, or links to Benchmarks page; guidance on memory/throughput tradeoffs.
* **Compatibility policy**
  Supported Python versions (e.g., “CPython 3.9–3.13”), deprecation window, semver stance (or CalVer).
* **Security posture**
  Dependency policy (pin or upper bounds), runtime sandboxing notes (if any).

## Community & ops (the “how we ship” layer)

* **Issue/PR templates** (`.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`)
  Repro steps, env info, checklist for tests/docs/Changelog updates.
* **DISCUSSIONS** (optional)
  For Q\&A and ideation separate from issues.
* **GOVERNANCE.md** (bigger projects)
  Maintainers, decision process, release managers.
* **FUNDING.yml** (optional)
  GitHub Sponsors/Opencollective.
* **CODEOWNERS**
  Automatic reviewer routing.

## Distribution & release docs

* **Release guide** (`docs/dev/release.md`)
  Version bump steps, changelog update, tagging, building wheels (`pipx run build`), verifying (`twine check`), publishing (`twine upload`), creating a GitHub Release with notes and link to Changelog.
* **Wheels & platforms**
  If you ship native code, document how wheels are built (cibuildwheel) and which platforms are supported.
* **Signing (optional)**
  How artifacts are signed/verified if you do that.

## Repository housekeeping that users appreciate

* **Clear directory layout**
  `src/<package>/`, `tests/`, `docs/`, `examples/`. Explain this layout briefly in CONTRIBUTING.
* **.editorconfig / linters**
  Keep style consistent; mention in CONTRIBUTING how to run `ruff`/`black`.
* **Deprecation policy**
  How long deprecated APIs linger, how warnings are emitted, and where migration notes live.
* **Telemetry/Privacy** (if applicable)
  Document any data collection and how to disable it.

## Minimal “golden path” checklist

* README with quickstart + badges, LICENSE, pyproject with good classifiers/URLs.
* CHANGELOG kept current for every release.
* CONTRIBUTING + test/lint/type instructions.
* API docs site (auto‑built) with tutorials and reference.
* SECURITY + CODE OF CONDUCT.
* Release guide; tags and GitHub Releases match PyPI.
* Issue/PR templates; examples tested in CI.

## Basic Checklist

* Everything from `Minimal “golden path” checklist`
* Comprehensive and insightful `doc/Developer-Guide.md`
* Comprehensive and insightful `doc/User-Guide.md`
