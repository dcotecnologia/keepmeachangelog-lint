"""Generate a flat SVG coverage badge from a coverage.py XML report.

Usage: python3 scripts/coverage_badge.py coverage.xml coverage.svg
"""

import sys
import xml.etree.ElementTree as ET


def percent(xml_path: str) -> float:
    root = ET.parse(xml_path).getroot()
    lines_valid = int(root.get("lines-valid", 0))
    branches_valid = int(root.get("branches-valid", 0))
    total = lines_valid + branches_valid
    if total == 0:
        return float(root.get("line-rate", 0)) * 100
    covered = int(root.get("lines-covered", 0)) + int(root.get("branches-covered", 0))
    return covered / total * 100


def color(pct: float) -> str:
    for limit, hex_color in (
        (100, "#4c1"),
        (90, "#97ca00"),
        (80, "#a4a61d"),
        (70, "#dfb317"),
        (50, "#fe7d37"),
    ):
        if pct >= limit:
            return hex_color
    return "#e05d44"


def badge(pct: float) -> str:
    value = f"{pct:.0f}%" if pct == 100 or pct < 99.5 else f"{pct:.1f}%"
    label, lw, vw = "coverage", 62, 44
    w = lw + vw
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {value}">'
        f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/>'
        f'<rect x="{lw}" width="{vw}" height="20" fill="{color(pct)}"/></g>'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{lw / 2}" y="14">{label}</text><text x="{lw + vw / 2}" y="14">{value}</text></g></svg>\n'
    )


if __name__ == "__main__":
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(badge(percent(sys.argv[1])))
