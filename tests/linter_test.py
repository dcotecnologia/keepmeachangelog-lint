from keepmeachangelog.cli import main
from keepmeachangelog.linter import Config, format_text, lint

GOOD = """# Changelog

## [Unreleased]

## [1.1.0] - 2024-02-01

### Added

- thing

## [1.0.0] - 2024-01-01 [YANKED]

### Fixed

- bug

[Unreleased]: https://x/compare/v1.1.0...HEAD
[1.1.0]: https://x/compare/v1.0.0...v1.1.0
[1.0.0]: https://x/releases/v1.0.0
"""


def msgs(t):
    return [p.message for p in lint(t)]


def test_good():
    assert lint(GOOD) == []


def test_bad_date_and_order():
    t = GOOD.replace("2024-02-01", "2023-13-01")
    assert any("invalid date" in m for m in msgs(t))
    t = GOOD.replace("2024-02-01", "2023-02-01")
    assert any("dated after" in m for m in msgs(t))


def test_unknown_empty_dup_section():
    t = GOOD.replace("### Added\n\n- thing", "### Stuff\n\n### Stuff\n")
    m = msgs(t)
    assert any("unknown section" in x for x in m)
    assert any("empty section" in x for x in m)
    assert any("duplicate section" in x for x in m)


def test_missing_link_and_title():
    t = GOOD.replace("[1.0.0]: https://x/releases/v1.0.0\n", "").replace(
        "# Changelog", "# Log"
    )
    m = msgs(t)
    assert any("missing link" in x for x in m)
    assert any("title" in x for x in m)


def test_unreleased_rules():
    t = GOOD.replace("## [Unreleased]", "## [Unreleased] - 2024-03-01")
    assert any("must not have a date" in m for m in msgs(t))


def test_cli(tmp_path, capsys):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(GOOD)
    assert main([str(f)]) == 0
    f.write_text("nothing")
    assert main([str(f)]) == 1
    assert main([str(tmp_path / "nope.md")]) == 1


def test_config(tmp_path, capsys):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        GOOD.replace("### Added", "### Changed").replace(
            "[1.0.0]: https://x/releases/v1.0.0\n", ""
        )
    )
    assert main([str(f)]) == 1
    c = tmp_path / "lint.toml"
    c.write_text('sections = ["Changed", "Fixed"]\nrequire-links = false\n')
    assert main(["--config", str(c), str(f)]) == 0
    c.write_text("[tool.keepmeachangelog]\nbogus = 1\n")
    assert main(["--config", str(c), str(f)]) == 2
    assert main(["--config", str(tmp_path / "nope.toml"), str(f)]) == 2


def test_validation_depth(tmp_path):
    t = GOOD.replace("2024-01-01", "2025-99-99")
    assert lint(t)
    assert lint(t, Config(validation_depth=1)) == []
    f = tmp_path / "CHANGELOG.md"
    f.write_text(t)
    assert main([str(f)]) == 1
    assert main(["--validation-depth", "1", str(f)]) == 0
    c = tmp_path / "c.toml"
    c.write_text("validation-depth = 1\n")
    assert main(["--config", str(c), str(f)]) == 0


def test_invalid_heading_and_section_outside_version():
    m = msgs("# Changelog\nintro text\n\n## Foo\n### Added\n- x\n")
    assert any("invalid version heading" in x for x in m)
    assert any("section outside" in x for x in m)


def test_unreleased_variants():
    t = (
        "# Changelog\n\n## [1.0.0] - 2024-01-01\n\n## [unreleased] - 2024-01-02\n\n"
        "## [unreleased]\n\n[1.0.0]: https://x/u\n[Unreleased]: https://x/u\n"
    )
    m = msgs(t)
    assert any("must not have a date" in x for x in m)
    assert any("must be the first" in x for x in m)
    assert any("duplicate version" in x for x in m)


def test_version_and_date_errors():
    t = (
        "# Changelog\n\n## [1.0] - 2024-01-01\n\n## [2.0.0]\n\n"
        "## [3.0.0] - 20240101\n\n## [4.0.0] - 2024-13-01\n"
    )
    m = msgs(t)
    assert any("not a valid Semantic Version" in x for x in m)
    assert any("missing a release date" in x for x in m)
    assert sum("invalid date" in x for x in m) == 2


def test_ordering_with_prerelease():
    t = (
        "# Changelog\n\n## [1.0.0] - 2024-01-01\n\n## [1.0.0-rc.1] - 2024-02-01\n\n"
        "## [2.0.0] - 2023-01-01\n\n[1.0.0]: https://x/u\n[1.0.0-rc.1]: https://x/u\n[2.0.0]: https://x/u\n"
    )
    m = msgs(t)
    assert any("[1.0.0-rc.1] is dated after [1.0.0]" in x for x in m)
    assert any("[2.0.0] should come before [1.0.0-rc.1]" in x for x in m)
    assert not any("[1.0.0-rc.1] should come before" in x for x in m)


def test_code_fence_is_content_and_ignored():
    t = "# Changelog\n\n## [1.0.0] - 2024-01-01\n\n### Added\n\n```\n## fake\n```\n\n[1.0.0]: https://x/u\n"
    assert lint(t) == []


def test_allow_empty_sections():
    t = GOOD.replace("- thing\n\n", "")
    assert any("empty section" in x for x in msgs(t))
    assert lint(t, Config(allow_empty_sections=True)) == []


MESSY_LINES = [
    "# changelog",
    "intro text   ",  # trailing spaces on purpose
    "## 1.0.1 - 2024-02-01",
    "### fixes",
    "- a  ",
    "",
    "",
    "- b",
    "## [v1.0.0]-2024-01-01 [YANKED]",
    "### Added:",
    "- c",
    "```",
    "keep   this",
    "",
    "as is",
    "```",
    "### Weird",
    "[1.0.0]: https://github.com/o/r/releases/tag/v1.0.0",
    "[9.9.9]: https://github.com/o/r/releases/tag/v9.9.9",
    "[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/",
    "",
]
MESSY = "\n".join(MESSY_LINES)

FIXED = """# Changelog

intro text

## [1.0.1] - 2024-02-01

### Fixed

- a

- b

## [1.0.0] - 2024-01-01 [YANKED]

### Added

- c
```
keep   this

as is
```

### Weird

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/

[1.0.1]: https://github.com/o/r/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/o/r/releases/tag/v1.0.0
"""


def test_format_text():
    assert format_text(MESSY) == FIXED
    assert format_text(FIXED) == FIXED
    assert format_text("") == ""
    assert format_text("a\r\nb") == "a\nb\n"


def test_format_with_unreleased_and_config_repo():
    t = "# Changelog\n## unreleased\n## [1.0.0] - 2024-01-01\n"
    c = Config(repo_url="https://gitlab.com/o/r/", tag_prefix="")
    out = format_text(t, c)
    assert "[Unreleased]: https://gitlab.com/o/r/compare/1.0.0...HEAD" in out
    assert "[1.0.0]: https://gitlab.com/o/r/releases/tag/1.0.0" in out


def test_format_problems_reported():
    m = msgs(MESSY)
    assert any("expected a blank line" in x for x in m)
    assert any("expected '# Changelog'" in x for x in m)
    assert any("unknown section 'Weird'" in x for x in m)
    assert any("has no matching version" in x for x in m)
    assert not any("missing link" in x for x in m)


def test_remove_extra_blank_line():
    t = GOOD.replace("# Changelog\n\n", "# Changelog\n\n\n")
    assert any("remove this line" in x for x in msgs(t))


def test_link_problems():
    t = GOOD.replace("https://x/releases/v1.0.0", "ftp://bad")
    assert any("invalid link URL for [1.0.0]" in x for x in msgs(t))
    assert any(
        "missing link" in x
        for x in msgs(GOOD.replace("[1.1.0]: https://x/compare/v1.0.0...v1.1.0\n", ""))
    )


def test_wrong_link_target_is_fixable():
    t = FIXED.replace("compare/v1.0.0...v1.0.1", "compare/v0.0.1...v1.0.1")
    assert any(
        "expected '[1.0.1]: https://github.com/o/r/compare/v1.0.0...v1.0.1'" in x
        for x in msgs(t)
    )
    assert format_text(t) == FIXED


def test_cli_fix(tmp_path, capsys):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(MESSY)
    assert main([str(f)]) == 1
    assert main(["--fix", str(f)]) == 1  # fixed, but "Weird" section remains
    out = capsys.readouterr().out
    assert "fixed" in out and "unknown section 'Weird'" in out
    assert "### Weird" in f.read_text()
    f.write_text(FIXED.replace("### Weird\n\n", ""))
    assert main(["--fix", str(f)]) == 0


def test_canonical_section_alias_not_configured():
    c = Config(sections=frozenset({"Added"}))
    assert "unknown section 'fixes'" in " ".join(
        msgs_c("## [1.0.0] - 2024-01-01\n\n### fixes\n\n- a\n", c)
    )


def msgs_c(t, c):
    return [p.message for p in lint(t, c)]


def _cl(*entries):
    body = "# Changelog\n\n"
    for ver, date, sec in entries:
        body += f"## [{ver}] - {date}\n\n### {sec}\n\n- x\n\n"
    return body.rstrip("\n") + "\n"


def test_sections_allowed_per_release_type():
    # patch release may only have Fixed/Security
    t = _cl(("1.0.1", "2024-02-01", "Added"), ("1.0.0", "2024-01-01", "Added"))
    assert any("only 'fixed, security'" in x and "patch" in x for x in msgs_nolinks(t))
    # minor release cannot have Removed
    t = _cl(("1.1.0", "2024-02-01", "Removed"), ("1.0.0", "2024-01-01", "Added"))
    assert any("minor release" in x for x in msgs_nolinks(t))
    # major allows everything; the oldest entry has no predecessor
    t = _cl(("2.0.0", "2024-02-01", "Removed"), ("1.0.0", "2024-01-01", "Removed"))
    assert not any("only '" in x for x in msgs_nolinks(t))
    # valid patch
    t = _cl(("1.0.1", "2024-02-01", "Fixed"), ("1.0.0", "2024-01-01", "Added"))
    assert not any("only '" in x for x in msgs_nolinks(t))


def test_release_diff_cases():
    from keepmeachangelog.linter import _release_diff

    assert _release_diff("1.0.0", "1.0.0+b") is None
    assert _release_diff("1.0.0", "1.0.1") == "patch"
    assert _release_diff("1.0.0", "1.1.0") == "minor"
    assert _release_diff("1.0.0", "2.0.0") == "major"
    assert _release_diff("2.0.0-rc.1", "2.0.0") == "major"
    assert _release_diff("1.1.0-rc.1", "1.1.0") == "minor"
    assert _release_diff("1.0.1-rc.1", "1.0.1") == "patch"
    assert _release_diff("1.0.0-rc.1", "1.1.0") == "major"  # node-semver quirk
    assert _release_diff("1.0.0-rc.1", "1.0.0-rc.2") == "prerelease"
    assert _release_diff("1.0.0", "1.0.0-rc.2") == "major"


def test_validation_depth_ignores_unreleased_and_window():
    t = _cl(("1.0.1", "2024-02-01", "Added"), ("1.0.0", "2024-01-01", "Added"))
    t = t.replace("# Changelog\n\n", "# Changelog\n\n## [Unreleased]\n\n", 1)
    # the pair (1.0.1, 1.0.0) is outside a window of 1 released version
    assert not any("only '" in x for x in msgs_nolinks(t, Config(validation_depth=1)))
    assert any("only '" in x for x in msgs_nolinks(t, Config(validation_depth=2)))


def test_empty_section_in_unreleased_is_allowed():
    t = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n## [1.0.0] - 2024-01-01\n\n### Added\n\n- x\n"
    assert not any("empty section" in x for x in msgs_nolinks(t))


def test_required_version(tmp_path):
    t = _cl(("1.0.0", "2024-01-01", "Added"))
    assert any(
        "no changelog entry for version 2.0.0" in x
        for x in msgs_nolinks(t, Config(version="2.0.0"))
    )
    assert not any(
        "no changelog entry" in x for x in msgs_nolinks(t, Config(version="1.0.0"))
    )
    f = tmp_path / "CHANGELOG.md"
    f.write_text(t)
    py = tmp_path / "pyproject.toml"
    py.write_text('[project]\nversion = "9.9.9"\n')
    assert main(["--version-from", str(py), str(f)]) == 1
    assert main(["--version", "1.0.0", str(f)]) == 1  # no links => still failing
    py.write_text("[project]\n")
    assert main(["--version-from", str(py), str(f)]) == 2
    c = tmp_path / "c.toml"
    c.write_text(f'version-from = "{py}"\n')
    assert main(["--config", str(c), str(f)]) == 2
    c.write_text('version = "1.0.0"\nrequire-links = false\n')
    assert main(["--config", str(c), str(f)]) == 0


def msgs_nolinks(t, c=None):
    from dataclasses import replace

    return [p.message for p in lint(t, replace(c or Config(), require_links=False))]


def test_config_repo_url_and_tag_prefix(tmp_path):
    from keepmeachangelog.cli import load_config

    c = tmp_path / "c.toml"
    c.write_text('repo-url = "https://x.io/o/r"\ntag-prefix = "rel-"\n')
    cfg = load_config(c)
    assert (cfg.repo_url, cfg.tag_prefix) == ("https://x.io/o/r", "rel-")


def test_equal_versions_are_skipped_in_section_rule():
    t = _cl(("1.0.0", "2024-02-01", "Added"), ("1.0.0", "2024-01-01", "Added"))
    assert not any("only '" in x for x in msgs_nolinks(t))


def test_release_diff_prerelease_to_different_release():
    from keepmeachangelog.linter import _release_diff

    assert _release_diff("1.2.3-rc.1", "1.3.0") == "minor"
