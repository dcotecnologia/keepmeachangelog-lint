# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add an npm wrapper package (`npm/`) so the linter runs with `npx`, `bunx` and `yarn dlx`; it runs the Python package pinned to the same version through `uvx`, `pipx` or `python`
- Publish the npm package to npm from the release workflow
- Document how to use the linter in Node projects (`npx`, `bunx`, `yarn dlx`, scripts and pre-commit) and add an npm badge

## [0.2.0] - 2026-11-26

### Added

- Add support for `package.json` in `--version-from` and `version-from`, so Node projects can require a changelog entry for their version
- Add directory arguments (for example `keepmeachangelog .`), which lint the `CHANGELOG.md` inside the directory
- Add the `keepmeachangelog version` and `keepmeachangelog help` subcommands

## [0.1.0] - 2026-11-16

### Added

- Add `keepmeachangelog` command and pre-commit hook that validate a changelog against Keep a Changelog 1.1.0
- Add the same release rules as `mindsers/changelog-reader-action`: valid SemVer, increasing order, listed items per section and sections allowed per release type
- Add formatting checks (spacing, section names, headings, version links) and `--fix` to correct them
- Add `--config`, `--validation-depth`, `--version` and `--version-from` options

[Unreleased]: https://github.com/dcotecnologia/keepmeachangelog-lint/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/dcotecnologia/keepmeachangelog-lint/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dcotecnologia/keepmeachangelog-lint/releases/tag/v0.1.0
