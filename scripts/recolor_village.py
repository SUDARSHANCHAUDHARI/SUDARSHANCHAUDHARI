"""Recolour the night-view 3D contribution village from blue to red/black.

Also: language donut and legend in red shades, radar scale labels drawn on top of the
radar line, and the bottom contributions/stars/forks line removed (the Stats and streak
cards are the single source for those numbers).
"""
import re, sys, pathlib

PIE = ["#ff2e4d", "#b3122e", "#ff8a3d", "#ff6b7d", "#7a1424", "#ffb3bc"]

# Roof colour per contribution level, dark (no contributions) to bright (most).
# The generator emits .cont-{top,left,right}-{level} rules whose level index already
# orders the five buckets, so the ramp is applied by index rather than by sorting the
# incoming fills: the index is the contribution level itself and cannot misorder.
RAMP = ["#3a0d14", "#7a1424", "#b3122e", "#ff2e4d", "#ff8a9a"]

# Each cube shows a roof and two walls. The generator derives its walls with d3's
# darker(0.5)/darker(1) (factors 0.84 and 0.70), which is too subtle to read against a
# near-black background, so the walls are stepped down harder here.
FACE_SCALE = {"top": 1.0, "left": 0.75, "right": 0.58}


def shade(hex_colour, scale):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, round(c * scale)) for c in (r, g, b))


def recolour_village(svg):
    """Map every .cont-<face>-<level> rule onto the red ramp.

    Returns the SVG and the roof colour used per level, so the caller can report what
    was applied instead of trusting that the substitution happened.
    """
    roofs = {}
    for level, base in enumerate(RAMP):
        for face, scale in FACE_SCALE.items():
            colour = shade(base, scale)
            pattern = rf"(\.cont-{face}-{level}\s*\{{\s*fill:\s*)[^;}}]+"
            svg, n = re.subn(pattern, lambda m: m.group(1) + colour, svg)
            if n and face == "top":
                roofs[level] = colour
    return svg, roofs


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
    # The polygon carries an <animate> child, so it has to be matched to its closing tag.
    poly = re.search(r'<polygon class="radar"[^>]*/>|<polygon class="radar".*?</polygon>', svg, re.S)
    if not ticks or not poly:
        return svg
    for t in ticks:
        svg = svg.replace(t, "", 1)
    poly = re.search(r'<polygon class="radar"[^>]*/>|<polygon class="radar".*?</polygon>', svg, re.S)
    return svg[:poly.end()] + "".join(ticks) + svg[poly.end():]


def luminance(hex_colour):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# The bug this guards against was not a missing colour but a flat one: the old mapping
# emitted five roof shades whose luminance differed by as little as 4, so every level read
# as the same red. A level must be separated from its neighbour by more than that.
MIN_LEVEL_GAP = 10.0


def flat_levels(roofs):
    """Consecutive roof levels that are too close in luminance to tell apart."""
    flat = []
    ordered = [roofs[lv] for lv in sorted(roofs)]
    for i in range(1, len(ordered)):
        gap = luminance(ordered[i]) - luminance(ordered[i - 1])
        if gap < MIN_LEVEL_GAP:
            flat.append(f"level {i - 1}->{i} gap {gap:.1f}")
    return flat


def blue_leftovers(svg):
    """Any remaining colour whose blue channel dominates red, i.e. missed by the recolour."""
    left = []
    for m in re.finditer(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", svg):
        r, g, b = (int(x) for x in m.groups())
        if b > r:
            left.append(m.group(0))
    for m in re.finditer(r"#([0-9a-fA-F]{6})\b", svg):
        h = m.group(1)
        if int(h[4:6], 16) > int(h[0:2], 16):
            left.append(m.group(0))
    return sorted(set(left))


def main(argv):
    if len(argv) < 2:
        sys.exit("recolor_village.py: usage: recolor_village.py <village.svg>")
    p = pathlib.Path(argv[1])
    if not p.is_file():
        sys.exit(f"recolor_village.py: no such file: {p}")
    try:
        svg = p.read_text()
    except OSError as e:
        sys.exit(f"recolor_village.py: cannot read {p}: {e}")

    svg = recolour_pie(svg)
    svg = drop_bottom_stats(svg)
    svg = ticks_on_top(svg)
    svg, roofs = recolour_village(svg)
    for old, new in {"#00000f": "#050102", "#eeeeff": "#fff1f2", "#aaaaaa": "#a8828a",
                     "#444444": "#3a0d14", "rgb(255,200,55)": "#ff6b7d"}.items():
        svg = re.sub(re.escape(old), new, svg, flags=re.I)

    try:
        p.write_text(svg)
    except OSError as e:
        sys.exit(f"recolor_village.py: cannot write {p}: {e}")

    print(f"recolor_village.py: {len(roofs)} levels recoloured: "
          + ", ".join(f"{lv}={c}" for lv, c in sorted(roofs.items())))
    # A leftover blue is reported, not fatal: a donut language colour can be legitimately
    # blue-dominant, and exiting here would leave the generated blue village for the next
    # step to publish unchanged.
    leftover = blue_leftovers(svg)
    if leftover:
        print("::warning::recolor_village.py: blue-dominant colours left: "
              + " ".join(leftover))

    problems = []
    if len(set(roofs.values())) < 4:
        problems.append(f"only {len(set(roofs.values()))} distinct roof shades")
    flat = flat_levels(roofs)
    if flat:
        problems.append("roof levels too close to tell apart: " + ", ".join(flat))
    if problems:
        sys.exit("recolor_village.py: " + "; ".join(problems))


if __name__ == "__main__":
    main(sys.argv)
