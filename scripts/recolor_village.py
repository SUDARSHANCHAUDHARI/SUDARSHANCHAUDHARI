"""Recolour the night-view 3D contribution village from blue to red/black."""
import re, sys, pathlib

def red(m):
    r, g, b = (int(x) for x in m.group(1).split(","))
    if b > r:  # blue building shades -> red shades
        return f"rgb({b},{round(g * 0.2)},{round(r * 1.2)})"
    return m.group(0)

p = pathlib.Path(sys.argv[1])
svg = re.sub(r"rgb\(\s*(\d+\s*,\s*\d+\s*,\s*\d+)\s*\)", red, p.read_text())
for old, new in {"#00000f": "#050102", "#eeeeff": "#fff1f2", "#aaaaaa": "#a8828a", "#444444": "#3a0d14", "rgb(255,200,55)": "#ff6b7d"}.items():
    svg = re.sub(re.escape(old), new, svg, flags=re.I)
p.write_text(svg)
