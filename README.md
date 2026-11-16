# keepmeachangelog

[![Tests](https://github.com/dcotecnologia/keepmeachangelog-lint/actions/workflows/tests.yml/badge.svg)](https://github.com/dcotecnologia/keepmeachangelog-lint/actions/workflows/tests.yml)
[![Coverage](https://raw.githubusercontent.com/dcotecnologia/keepmeachangelog-lint/badges/coverage.svg)](https://github.com/dcotecnologia/keepmeachangelog-lint/actions/workflows/tests.yml)
[![Release](https://github.com/dcotecnologia/keepmeachangelog-lint/actions/workflows/release.yml/badge.svg)](https://github.com/dcotecnologia/keepmeachangelog-lint/actions/workflows/release.yml)
[![Latest release](https://img.shields.io/github/v/release/dcotecnologia/keepmeachangelog-lint)](https://github.com/dcotecnologia/keepmeachangelog-lint/releases/latest)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Keep a Changelog](https://img.shields.io/badge/changelog-Keep%20a%20Changelog%201.1.0-E05735)](https://keepachangelog.com/en/1.1.0/)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-blue)](https://semver.org/spec/v2.0.0.html)

Linter for changelogs following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## pre-commit

```yaml
repos:
  - repo: https://github.com/dcotecnologia/keepmeachangelog-lint
    rev: v0.1.0
    hooks:
      - id: keepmeachangelog-lint
        args: [--fix]
```

### Pointing at a specific file

By default the hook runs on files named `CHANGELOG` / `CHANGELOG.md` (any directory).
To lint a differently named or located file, override `files` in your config:

```yaml
      - id: keepmeachangelog-lint
        files: ^docs/HISTORY\.md$
```

To lint a file even when it is not staged, add `always_run: true` and `pass_filenames: false`
with the path as an argument:

```yaml
      - id: keepmeachangelog-lint
        args: [docs/HISTORY.md]
        pass_filenames: false
        always_run: true
```

Or run directly: `keepmeachangelog CHANGELOG.md`.

## Config

`--config path/to/file.toml` (keys at top level, or under `[tool.keepmeachangelog]`
so you can point at a `pyproject.toml`):

```toml
title = "Changelog"                 # expected "# <title>"
sections = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
require-links = true                # each version needs a "[x.y.z]: url"
allow-empty-sections = false
validation-depth = 10              # optional: only the latest N released versions (Unreleased not counted); omit = all
version = "1.4.0"                  # optional: the changelog must have an entry for it
version-from = "pyproject.toml"    # optional: same, read from [project].version
repo-url = "https://github.com/o/r"  # optional: enables generating/fixing version links
tag-prefix = "v"
```

`--validation-depth N`, `--version X` and `--version-from pyproject.toml` on the command line override the file.

In pre-commit: `args: [--config, .changelog-lint.toml]`.

## Rules

- `# Changelog` title
- Version headings `## [x.y.z] - YYYY-MM-DD` (SemVer, valid ISO date, optional `[YANKED]`) or `## [Unreleased]` (first, no date)
- Latest version first (by version and date); no duplicate versions
- Sections only `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; no duplicates, none empty
- Each version has a link reference `[x.y.z]: <url>`

### Same checks as `mindsers/changelog-reader-action`

So the pre-commit hook fails on whatever would fail the release workflow:

- every released version is a valid SemVer; versions are in strictly increasing order (latest first)
- a section must have listed items (`Unreleased` is exempt)
- sections allowed by release type, comparing each version with the previous one:
  patch: `Fixed`, `Security`; minor: also `Added`, `Changed`, `Deprecated`; major/other: also `Removed`
- `validation-depth` counts the newest N released versions (Unreleased excluded); the oldest one in the window is not compared with a predecessor
- `--version-from pyproject.toml` fails if the changelog has no entry for the project version (the action's "No log entry found for version X")

Not covered: `version_scheme: pep440`. Note the action only validates when `validation_level` is `warn` or `error` (default `none`).

## License

[MIT](LICENSE)
