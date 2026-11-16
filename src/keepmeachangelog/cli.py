from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

from .linter import Config, format_text, lint


def load_config(path: Path) -> Config:
    """Load a TOML file; keys may be top-level or under [tool.keepmeachangelog-
    lint]."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    data = data.get("tool", {}).get("keepmeachangelog", data)
    known = {
        "title",
        "sections",
        "require-links",
        "allow-empty-sections",
        "validation-depth",
        "repo-url",
        "tag-prefix",
        "version",
        "version-from",
    }
    if unknown := set(data) - known:
        raise ValueError(f"unknown option(s): {', '.join(sorted(unknown))}")
    base = Config()
    return Config(
        title=data.get("title", base.title),
        sections=frozenset(data.get("sections", base.sections)),
        require_links=data.get("require-links", base.require_links),
        allow_empty_sections=data.get(
            "allow-empty-sections", base.allow_empty_sections
        ),
        validation_depth=data.get("validation-depth", base.validation_depth),
        repo_url=data.get("repo-url", base.repo_url),
        tag_prefix=data.get("tag-prefix", base.tag_prefix),
        version=_version_from(data["version-from"])
        if "version-from" in data
        else data.get("version", base.version),
    )


def _version_from(path: str) -> str:
    """Read [project].version from a pyproject.toml."""
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))["project"]["version"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="keepmeachangelog",
        description="Lint CHANGELOG files (Keep a Changelog 1.1.0)",
    )
    p.add_argument("files", nargs="*", default=["CHANGELOG.md"])
    p.add_argument("--config", type=Path, help="TOML config file")
    p.add_argument(
        "--validation-depth",
        type=int,
        metavar="N",
        help="only validate the latest N versions (default: all)",
    )
    p.add_argument("--version", help="require a changelog entry for this version")
    p.add_argument(
        "--version-from",
        metavar="PYPROJECT",
        help="like --version, read from [project].version of a pyproject.toml",
    )
    p.add_argument(
        "--fix",
        action="store_true",
        help="rewrite files in canonical format (spacing, section names, links)",
    )
    args = p.parse_args(argv)
    try:
        config = load_config(args.config) if args.config else Config()
        if args.version_from:
            config = replace(config, version=_version_from(args.version_from))
        if args.version:
            config = replace(config, version=args.version)
        if args.validation_depth is not None:
            config = replace(config, validation_depth=args.validation_depth)
    except (OSError, ValueError, KeyError) as e:  # TOMLDecodeError is a ValueError
        print(
            f"{args.config or args.version_from}: invalid config: {e!r}",
            file=sys.stderr,
        )
        return 2
    rc = 0
    for f in args.files:
        path = Path(f)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"{f}: cannot read: {e}", file=sys.stderr)
            rc = 1
            continue
        if args.fix:
            fixed = format_text(text, config)
            if fixed != text:
                path.write_text(fixed, encoding="utf-8")
                print(f"{f}: fixed")
                text = fixed
        for prob in lint(text, config):
            print(f"{f}:{prob.line}: {prob.message}")
            rc = 1
    return rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
