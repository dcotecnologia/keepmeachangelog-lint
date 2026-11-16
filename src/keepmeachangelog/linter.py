"""Keep a Changelog 1.1.0 rules (https://keepachangelog.com/en/1.1.0/)."""

from __future__ import annotations

import difflib
import itertools
import re
from dataclasses import dataclass, field
from datetime import date
from typing import NamedTuple

SECTIONS = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
ALIASES = {
    "add": "Added",
    "adds": "Added",
    "new": "Added",
    "change": "Changed",
    "changes": "Changed",
    "deprecate": "Deprecated",
    "deprecates": "Deprecated",
    "remove": "Removed",
    "removes": "Removed",
    "fix": "Fixed",
    "fixes": "Fixed",
    "bugfix": "Fixed",
    "bugfixes": "Fixed",
}
# sections allowed per release type, same as mindsers/changelog-reader-action
PATCH_ALLOWED = ("fixed", "security")
MINOR_ALLOWED = ("added", "changed", "deprecated", "fixed", "security")
MAJOR_ALLOWED = ("added", "removed", "changed", "deprecated", "fixed", "security")
# tolerant: also matches "## 1.0.0 - date", "## [v1.0.0]-date", "## [unreleased]"
HEADING_RE = re.compile(
    r"^##\s+\[?v?(?P<v>unreleased|\d[^\]\s]*)\]?"
    r"(?:\s*[-–—]\s*(?P<d>[^\s\[]\S*))?(?P<y>\s*\[YANKED\])?\s*$",
    re.IGNORECASE,
)
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$"
)
LINK_RE = re.compile(r"^\[(?P<v>[^\]]+)\]:\s*(?P<u>\S+)")
URL_RE = re.compile(r"https?://\S+")
BASE_RE = re.compile(r"(https?://[^/\s]+/[^/\s]+/[^/\s]+?)/(?:compare|releases)/")


@dataclass(frozen=True)
class Config:
    title: str = "Changelog"
    sections: frozenset[str] = field(default_factory=lambda: frozenset(SECTIONS))
    require_links: bool = True
    allow_empty_sections: bool = False
    validation_depth: int | None = None  # only the latest N versions; None = all
    repo_url: str | None = None  # e.g. https://github.com/owner/repo (else inferred)
    tag_prefix: str = "v"
    version: str | None = None  # the changelog must have an entry for this version


DEFAULT = Config()


class Problem(NamedTuple):
    line: int
    message: str


def _semver_key(v: str) -> tuple:
    m = SEMVER_RE.match(v)
    assert m is not None
    core = tuple(int(x) for x in m.group(0).split("-")[0].split("+")[0].split("."))
    pre = m.group(4)
    # a release sorts after its own pre-releases
    return core, (1, ()) if pre is None else (
        0,
        tuple(
            (0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre[1:].split(".")
        ),
    )


def _release_diff(older: str, newer: str) -> str | None:
    """Replicate node-semver `diff`, with pre* collapsed."""
    ko, kn = _semver_key(older), _semver_key(newer)
    if ko == kn:
        return None
    low, high = (older, newer) if ko < kn else (newer, older)

    def parts(v: str) -> tuple[int, int, int, bool]:
        m = SEMVER_RE.match(v)
        assert m is not None
        return int(m[1]), int(m[2]), int(m[3]), bool(m[4])

    lmaj, lmin, lpat, lpre = parts(low)
    hmaj, hmin, hpat, hpre = parts(high)
    if lpre and not hpre:
        if not lpat and not lmin:
            return "major"
        if (lmaj, lmin, lpat) == (hmaj, hmin, hpat):
            return "minor" if lmin and not lpat else "patch"
    if lmaj != hmaj:
        return "major"
    if lmin != hmin:
        return "minor"
    if lpat != hpat:
        return "patch"
    return "prerelease"


def canonical_name(v: str) -> str:
    return "Unreleased" if v.lower() == "unreleased" else v


def version_like(label: str) -> bool:
    return canonical_name(label) == "Unreleased" or bool(SEMVER_RE.match(label))


def canonical_section(name: str, config: Config) -> str | None:
    """Return the configured section matching `name` (case/alias tolerant)."""
    key = name.strip().rstrip(":").strip().lower()
    for s in config.sections:
        if s.lower() == key:
            return s
    alias = ALIASES.get(key)
    return alias if alias in config.sections else None


def _base(config: Config, urls: list[str]) -> str | None:
    if config.repo_url:
        return config.repo_url.rstrip("/")
    for u in urls:
        if m := BASE_RE.match(u):
            return m[1]
    return None


def expected_links(names: list[str], base: str, prefix: str) -> dict[str, str]:
    """Build the GitHub-style link targets for versions listed latest first."""
    released = [n for n in names if n != "Unreleased"]
    out: dict[str, str] = {}
    for i, v in enumerate(released):
        if i + 1 < len(released):
            out[v] = f"{base}/compare/{prefix}{released[i + 1]}...{prefix}{v}"
        else:
            out[v] = f"{base}/releases/tag/{prefix}{v}"
    if "Unreleased" in names and released:
        out["Unreleased"] = f"{base}/compare/{prefix}{released[0]}...HEAD"
    return out


def format_text(text: str, config: Config = DEFAULT) -> str:
    """Return the canonical form of a changelog (what `--fix` writes)."""
    items: list[tuple[str, str]] = []
    existing: dict[str, str] = {}
    names: list[str] = []
    in_fence = False
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            items.append(("text", raw.rstrip()))
            continue
        if in_fence:
            items.append(("raw", raw))
            continue
        line = raw.rstrip()
        if not line:
            items.append(("blank", ""))
        elif (m := LINK_RE.match(line)) and version_like(m["v"]):
            existing[canonical_name(m["v"])] = m["u"]
        elif line.startswith("# "):
            same = line[2:].strip().lower() == config.title.lower()
            items.append(("head", f"# {config.title}" if same else line))
        elif line.startswith("## "):
            vm = HEADING_RE.match(line)
            if vm:
                v = canonical_name(vm["v"])
                names.append(v)
                line = f"## [{v}]" + (f" - {vm['d']}" if vm["d"] else "")
                line += " [YANKED]" if vm["y"] else ""
            items.append(("head", line))
        elif line.startswith("### "):
            name = line[4:].strip()
            items.append(("head", f"### {canonical_section(name, config) or name}"))
        else:
            items.append(("text", line))

    res: list[str] = []
    need_blank = False
    for kind, t in items:
        if kind == "blank":
            if res and res[-1] != "":
                res.append("")
        elif kind == "head":
            if res and res[-1] != "":
                res.append("")
            res.append(t)
            need_blank = True
        else:
            if need_blank and res[-1] != "":
                res.append("")
            need_blank = False
            res.append(t)
    while res and res[-1] == "":
        res.pop()

    base = _base(config, list(existing.values()))
    expected = expected_links(names, base, config.tag_prefix) if base else {}
    block: list[str] = []
    for v in dict.fromkeys(names):
        if url := expected.get(v) or existing.get(v):
            block.append(f"[{v}]: {url}")
    if block:
        res += ([""] if res else []) + block
    return "\n".join(res) + "\n" if res else ""


def _format_problems(text: str, config: Config) -> list[Problem]:
    a = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    b = format_text(text, config).split("\n")
    out: list[Problem] = []
    for tag, i1, _, j1, j2 in difflib.SequenceMatcher(
        None, a, b, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            continue
        line = min(i1 + 1, len(a))
        if j1 == j2:
            msg = "remove this line"
        elif b[j1]:
            msg = f"expected '{b[j1]}'"
        else:
            msg = "expected a blank line"
        out.append(Problem(line, f"formatting: {msg} (fixable with --fix)"))
    return out


def lint(text: str, config: Config = DEFAULT) -> list[Problem]:
    lines = text.splitlines()
    out: list[Problem] = []
    want = f"# {config.title}"
    if not any(line.startswith("# ") for line in lines):
        out.append(Problem(1, f"missing top-level '{want}' title"))
    elif (
        next(line for line in lines if line.startswith("# ")).strip().lower()
        != want.lower()
    ):
        out.append(Problem(1, f"title should be '{want}'"))

    versions: list[tuple[int, str, str | None]] = []  # line, name, date
    links: dict[str, tuple[int, str]] = {}
    seen_versions: set[str] = set()
    section_seen: set[str] = set()
    sections_by_version: dict[str, list[str]] = {}
    cur_version: str | None = None
    cur_section: tuple[int, str] | None = None
    section_has_content = False
    in_fence = False

    def close_section() -> None:
        if (
            cur_section
            and not section_has_content
            and not config.allow_empty_sections
            and cur_version != "Unreleased"  # the release action skips Unreleased
        ):
            out.append(Problem(cur_section[0], f"empty section '### {cur_section[1]}'"))

    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            section_has_content = section_has_content or bool(line.strip())
            continue
        if m := LINK_RE.match(line):
            links[canonical_name(m["v"])] = (n, m["u"])
            continue
        if line.startswith("## "):
            close_section()
            cur_section, section_has_content, section_seen = None, False, set()
            vm = HEADING_RE.match(line)
            if not vm:
                out.append(
                    Problem(
                        n,
                        "invalid version heading, expected "
                        "'## [x.y.z] - YYYY-MM-DD' or '## [Unreleased]'",
                    )
                )
                cur_version = None
                continue
            v, d = canonical_name(vm["v"]), vm["d"]
            cur_version = v
            if v in seen_versions:
                out.append(Problem(n, f"duplicate version [{v}]"))
            seen_versions.add(v)
            if v == "Unreleased":
                if d or vm["y"]:
                    out.append(Problem(n, "[Unreleased] must not have a date"))
                if versions:
                    out.append(Problem(n, "[Unreleased] must be the first version"))
            else:
                if not SEMVER_RE.match(v):
                    out.append(Problem(n, f"[{v}] is not a valid Semantic Version"))
                if d is None:
                    out.append(Problem(n, f"[{v}] is missing a release date"))
                else:
                    try:
                        date.fromisoformat(d)
                        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                            raise ValueError
                    except ValueError:
                        out.append(Problem(n, f"invalid date '{d}', use YYYY-MM-DD"))
            versions.append((n, v, d))
        elif line.startswith("### "):
            close_section()
            raw_name = line[4:].strip()
            name = canonical_section(raw_name, config) or raw_name
            section_has_content = False
            cur_section = (n, name)
            if cur_version is None:
                out.append(Problem(n, "section outside of a version"))
            if name not in config.sections:
                out.append(
                    Problem(
                        n,
                        f"unknown section '{name}', expected one of "
                        f"{', '.join(sorted(config.sections))}",
                    )
                )
            if name in section_seen:
                out.append(Problem(n, f"duplicate section '{name}' in [{cur_version}]"))
            section_seen.add(name)
            if cur_version is not None:
                sections_by_version.setdefault(cur_version, []).append(name.lower())
        elif line.strip() and cur_section:
            section_has_content = True
    close_section()

    # ordering: latest first, by date and by version
    released = [
        (n, v, d) for n, v, d in versions if v != "Unreleased" and SEMVER_RE.match(v)
    ]
    for (_, pv, pd), (n, v, d) in itertools.pairwise(released):
        if _semver_key(v) >= _semver_key(pv):
            out.append(Problem(n, f"[{v}] should come before [{pv}] (latest first)"))
        if pd and d and pd < d:
            out.append(Problem(n, f"[{v}] is dated after [{pv}] (latest first)"))

    # same window as the release action: the newest `validation_depth` released
    # versions (Unreleased excluded); each is compared with the next older one
    rel = [(n, v) for n, v, _ in versions if v != "Unreleased" and SEMVER_RE.match(v)]
    depth = config.validation_depth
    window = rel if depth is None else rel[:depth]
    for (n, v), (_, older) in itertools.pairwise(window):
        kind = _release_diff(older, v)
        if kind is None:
            continue
        allowed = {"patch": PATCH_ALLOWED, "minor": MINOR_ALLOWED}.get(
            kind, MAJOR_ALLOWED
        )
        if any(sec not in allowed for sec in sections_by_version.get(v, [])):
            out.append(
                Problem(
                    n,
                    f"only '{', '.join(allowed)}' sections are allowed for version "
                    f"{v} ({kind} release after {older})",
                )
            )

    names = [v for _, v, _ in versions]
    if config.version is not None and config.version not in names:
        out.append(Problem(1, f"no changelog entry for version {config.version}"))
    for label, (n, url) in links.items():
        if not version_like(label):
            continue
        if not URL_RE.fullmatch(url):
            out.append(Problem(n, f"invalid link URL for [{label}]: '{url}'"))
        elif label not in names:
            out.append(Problem(n, f"link [{label}] has no matching version"))

    # when the repo URL is known, missing/wrong links are reported as fixable
    # formatting problems instead
    fixable = _base(config, [u for _, u in links.values()]) is not None
    for n, v, _ in versions:
        if config.require_links and v not in links and not fixable:
            out.append(Problem(n, f"missing link reference definition '[{v}]: <url>'"))

    out += _format_problems(text, config)
    result = sorted(out)
    if depth is not None and len(rel) > depth:
        cutoff = rel[depth][0]
        result = [p for p in result if p.line < cutoff]
    return result
