# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-16

### Added

- Add `keepmeachangelog` command and pre-commit hook that validate a changelog against Keep a Changelog 1.1.0
- Add the same release rules as `mindsers/changelog-reader-action`: valid SemVer, increasing order, listed items per section and sections allowed per release type
- Add formatting checks (spacing, section names, headings, version links) and `--fix` to correct them
- Add `--config`, `--validation-depth`, `--version` and `--version-from` options

[Unreleased]: https://github.com/dcotecnologia/keepmeachangelog-lint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dcotecnologia/keepmeachangelog-lint/releases/tag/v0.1.0
