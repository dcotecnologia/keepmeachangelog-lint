# keepmeachangelog

Linter for changelogs following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## pre-commit

```yaml
repos:
  - repo: https://github.com/dcotecnologia/keepmeachangelog
    rev: v0.1.0
    hooks:
      - id: keepmeachangelog-lint
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
validation-depth = 10              # optional: only the latest N versions (incl. Unreleased); omit = all
```

`--validation-depth N` on the command line overrides the file.

In pre-commit: `args: [--config, .changelog-lint.toml]`.

## Rules

- `# Changelog` title
- Version headings `## [x.y.z] - YYYY-MM-DD` (SemVer, valid ISO date, optional `[YANKED]`) or `## [Unreleased]` (first, no date)
- Latest version first (by version and date); no duplicate versions
- Sections only `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; no duplicates, none empty
- Each version has a link reference `[x.y.z]: <url>`
