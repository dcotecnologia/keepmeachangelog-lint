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
        GOOD.replace("### Added", "### Docs").replace(
            "[1.0.0]: https://x/releases/v1.0.0\n", ""
        )
    )
    assert main([str(f)]) == 1
    c = tmp_path / "lint.toml"
    c.write_text('sections = ["Docs", "Fixed"]\nrequire-links = false\n')
    assert main(["--config", str(c), str(f)]) == 0
    c.write_text("[tool.keepmeachangelog]\nbogus = 1\n")
    assert main(["--config", str(c), str(f)]) == 2
    assert main(["--config", str(tmp_path / "nope.toml"), str(f)]) == 2


def test_validation_depth(tmp_path):
    t = GOOD.replace("2024-01-01", "2025-99-99")
    assert lint(t)
    assert lint(t, Config(validation_depth=2)) == []
    f = tmp_path / "CHANGELOG.md"
    f.write_text(t)
    assert main([str(f)]) == 1
    assert main(["--validation-depth", "2", str(f)]) == 0
    c = tmp_path / "c.toml"
    c.write_text("validation-depth = 2\n")
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


MESSY = """# changelog
intro text   
## 1.0.1 - 2024-02-01
### fixes
- a  


- b
## [v1.0.0]-2024-01-01 [YANKED]
### Added:
- c
```
keep   this

as is
```
### Weird
[1.0.0]: https://github.com/o/r/releases/tag/v1.0.0
[9.9.9]: https://github.com/o/r/releases/tag/v9.9.9
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
"""

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
