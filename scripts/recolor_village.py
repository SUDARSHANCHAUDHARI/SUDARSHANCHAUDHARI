"""Recolour the night-view 3D contribution village from blue to red/black.

Also: language donut and legend in red shades, radar scale labels drawn on top of the
radar line, and the bottom contributions/stars/forks line removed (the Stats and streak
cards are the single source for those numbers).
"""
import re, sys, pathlib

PIE = ["#ff2e4d", "#b3122e", "#ff8a3d", "#ff6b7d", "#7a1424", "#ffb3bc"]


def red(m):
    r, g, b = (int(x) for x in m.group(1).split(","))
    if b > r:  # blue building shades -> red shades
        return f"rgb({b},{round(g * 0.2)},{round(r * 1.2)})"
    return m.group(0)


def recolour_pie(svg):
    """Map each donut slice colour (in drawing order) to a red shade, legend included."""
    seen = []
    for c in re.findall(r'style="fill: (#[0-9a-fA-F]{6});" class="stroke-bg"', svg):
        if c.lower() not in seen:
            seen.append(c.lower())
    for i, c in enumerate(seen):
        svg = re.sub(re.escape(c), PIE[i % len(PIE)], svg, flags=re.I)
    return svg


def drop_bottom_stats(svg):
    """Remove the <g> holding the contributions / stars / forks line."""
    start = svg.find('<g><text style="font-size: 32px; font-weight: bold;"')
    if start < 0:
        return svg
    depth, i = 0, start
    for m in re.finditer(r"<g\b|</g>", svg[start:]):
        depth += 1 if m.group(0) == "<g" else -1
        if depth == 0:
            return svg[:start] + svg[start + m.end():]
    return svg


def ticks_on_top(svg):
    """Move the radar scale labels after the radar polygon so the line does not cover them."""
    ticks = re.findall(r'<text[^>]*class="fill-weak">(?:1|10|100|1K|10K)</text>', svg)
    poly = re.search(r'<polygon class="radar"[^>]*?(?:/>|>\s*</polygon>)', svg)
    if not ticks or not poly:
        return svg
    for t in ticks:
        svg = svg.replace(t, "", 1)
    poly = re.search(r'<polygon class="radar"[^>]*?(?:/>|>\s*</polygon>)', svg)
    return svg[:poly.end()] + "".join(ticks) + svg[poly.end():]


if len(sys.argv) < 2:
    sys.exit("recolor_village.py: usage: recolor_village.py <village.svg>")
p = pathlib.Path(sys.argv[1])
if not p.is_file():
    sys.exit(f"recolor_village.py: no such file: {p}")
svg = recolour_pie(p.read_text())
svg = drop_bottom_stats(svg)
svg = ticks_on_top(svg)
svg = re.sub(r"rgb\(\s*(\d+\s*,\s*\d+\s*,\s*\d+)\s*\)", red, svg)
for old, new in {"#00000f": "#050102", "#eeeeff": "#fff1f2", "#aaaaaa": "#a8828a", "#444444": "#3a0d14", "rgb(255,200,55)": "#ff6b7d"}.items():
    svg = re.sub(re.escape(old), new, svg, flags=re.I)
p.write_text(svg)
