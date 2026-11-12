"""Shared System effect layer for every SVG on the profile.

GitHub shows an SVG through <img>, which runs CSS animation but no script, so each effect is
CSS inside the SVG. add_fx() appends one <g class="fx"> just before </svg>, sized from the
root viewBox, so it works on cards we build and on third-party charts we only recolour.

Effects (all red/black, all off under prefers-reduced-motion):
  edge   - the frame breathes red
  beam   - a light band sweeps across, then rests
  photo  - slow zoom on the embedded image, pulsing red vignette, rising embers
  glitch - a red ghost of the image jumps sideways for a few frames

    python3 scripts/fx.py <file.svg>...       add edge + beam in place (idempotent)
    python3 scripts/fx.py --selftest
"""
import re
import sys
import pathlib

RED, EMBER, GLOW = "#ff2e4d", "#ff8a3d", "#ff6b7d"
MARK = 'class="fx"'


def size(svg):
    root = re.search(r"<svg\b[^>]*>", svg, re.S)
    if not root:
        raise ValueError("no <svg> root tag")
    tag = root.group(0)
    vb = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', tag)
    if vb:
        return tuple(float(v) for v in vb.groups())
    w = re.search(r'\bwidth="([\d.]+)', tag)
    h = re.search(r'\bheight="([\d.]+)', tag)
    if not (w and h):
        raise ValueError("root <svg> has neither a viewBox nor a numeric width and height")
    return 0.0, 0.0, float(w.group(1)), float(h.group(1))


def embers(x0, y0, w, h, n=14):
    # fixed spread rather than random, so a rebuild gives a byte-identical file
    dots = []
    for i in range(n):
        x = x0 + w * ((i * 0.618034) % 1)
        r = 1.4 + (i % 3) * 0.8
        dur = 6 + (i * 7 % 5)
        delay = -(i * 1.3 % dur)
        fill = EMBER if i % 3 else GLOW
        dots.append(f'<circle class="fx-ember" cx="{x:.1f}" cy="{y0 + h + 6:.1f}" r="{r:.1f}" fill="{fill}" '
                    f'style="animation-duration:{dur}s;animation-delay:{delay:.1f}s"/>')
    return "".join(dots)


def layer(x0, y0, w, h, photo=False):
    band = max(w * 0.18, 60)
    rise = -(h + 20)
    css = [
        ".fx-edge{fill:none;stroke:%s;stroke-width:2;animation:fx-edge 3.2s ease-in-out infinite}" % RED,
        "@keyframes fx-edge{0%,100%{stroke-opacity:.2}50%{stroke-opacity:.85}}",
        ".fx-beam{animation:fx-beam 7s cubic-bezier(.4,0,.6,1) infinite}",
        "@keyframes fx-beam{0%%{transform:translateX(%.0fpx)}55%%,100%%{transform:translateX(%.0fpx)}}" % (-band, w + band),
    ]
    parts = [
        f'<linearGradient id="fx-band" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{RED}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{RED}" stop-opacity=".22"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>',
    ]
    body = [f'<rect class="fx-beam" x="{x0:.1f}" y="{y0:.1f}" width="{band:.1f}" height="{h:.1f}" fill="url(#fx-band)"/>']
    if photo:
        css += [
            ".fx-vig{animation:fx-vig 4s ease-in-out infinite}",
            "@keyframes fx-vig{0%,100%{opacity:.55}50%{opacity:.95}}",
            ".fx-ember{opacity:0;animation:fx-rise 7s linear infinite}",
            "@keyframes fx-rise{0%%{transform:translateY(0);opacity:0}15%%{opacity:.9}85%%{opacity:.6}"
            "100%%{transform:translateY(%.0fpx);opacity:0}}" % rise,
        ]
        parts.append('<radialGradient id="fx-vg" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#050102" stop-opacity="0"/>'
                     f'<stop offset="1" stop-color="#3a0008" stop-opacity=".85"/></radialGradient>')
        body.insert(0, f'<rect class="fx-vig" x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#fx-vg)"/>')
        body.append(embers(x0, y0, w, h))
    body.append(f'<rect class="fx-edge" x="{x0 + 1:.1f}" y="{y0 + 1:.1f}" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="6"/>')
    css.append("@media (prefers-reduced-motion:reduce){.fx *,.fx-zoom,.fx-ghost{animation:none!important}}")
    return (f'<g {MARK} aria-hidden="true"><defs>{"".join(parts)}<style>{"".join(css)}</style></defs>'
            + "".join(body) + "</g>")


def add_fx(svg, photo=False):
    """Return svg with the effect layer appended; unchanged if it already has one."""
    if MARK in svg:
        return svg
    end = svg.rfind("</svg>")
    if end < 0:
        raise ValueError("no closing </svg>")
    x0, y0, w, h = size(svg)
    return svg[:end] + layer(x0, y0, w, h, photo) + "\n" + svg[end:]


IMAGE_CSS = (".fx-zoom{transform-box:fill-box;transform-origin:center;animation:fx-zoom 18s ease-in-out infinite alternate}"
             "@keyframes fx-zoom{from{transform:scale(1)}to{transform:scale(1.07)}}"
             ".fx-ghost{opacity:0;animation:fx-ghost 5s steps(1) infinite}"
             "@keyframes fx-ghost{0%,86%,100%{opacity:0;transform:translateX(0)}88%{opacity:.55;transform:translateX(-7px)}"
             "91%{opacity:.4;transform:translateX(5px)}94%{opacity:.5;transform:translateX(-3px)}}")


def image_svg(data_uri, w, h, title, desc, photo=True, glitch=False):
    """An image wrapped in an SVG frame with the effect layer: the README shows this instead."""
    from xml.sax.saxutils import escape
    zoom = ' class="fx-zoom"' if photo else ""
    ghost = ""
    if glitch:
        ghost = ('<filter id="fx-red"><feColorMatrix values="1 0 0 0 .25  0 0 0 0 0  0 0 0 0 .02  0 0 0 1 0"/></filter>'
                 f'<use href="#fx-img" class="fx-ghost" filter="url(#fx-red)"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
           f'aria-label="{escape(desc)}">\n<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n'
           f'<defs><clipPath id="fx-clip"><rect width="{w}" height="{h}" rx="6"/></clipPath><style>{IMAGE_CSS}</style></defs>\n'
           f'<g clip-path="url(#fx-clip)"><image id="fx-img"{zoom} width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
           f'href="{data_uri}"/>{ghost}</g>\n</svg>\n')
    return add_fx(svg, photo=photo)


def selftest():
    import xml.etree.ElementTree as ET
    base = '<svg xmlns="http://www.w3.org/2000/svg"\n width="340" height="200" viewBox="0 0 340 200"><rect/></svg>'
    once = add_fx(base)
    assert add_fx(once) == once, "add_fx is not idempotent"
    assert once.count(MARK) == 1
    ET.fromstring(once)
    assert size('<svg width="80" height="40"></svg>') == (0, 0, 80, 40)
    img = image_svg("data:image/gif;base64,R0lGODlhAQABAAAAACw=", 100, 50, "t", "d & e", glitch=True)
    ET.fromstring(img)
    assert "fx-ember" in img and "fx-ghost" in img and "fx-zoom" in img
    try:
        add_fx("<svg>")
    except ValueError:
        pass
    else:
        raise AssertionError("missing </svg> not rejected")
    print("fx.py: selftest ok")


def main(argv):
    if argv[1:] == ["--selftest"]:
        return selftest()
    if len(argv) < 2:
        sys.exit("fx.py: usage: fx.py <file.svg>... | --selftest")
    for name in argv[1:]:
        p = pathlib.Path(name)
        try:
            svg = p.read_text()
            out = add_fx(svg)
        except (OSError, ValueError) as e:
            sys.exit(f"fx.py: {p}: {e}")
        if out == svg:
            print(f"fx.py: {p}: already has the effect layer")
            continue
        try:
            p.write_text(out)
        except OSError as e:
            sys.exit(f"fx.py: cannot write {p}: {e}")
        print(f"fx.py: {p}: effect layer added")


if __name__ == "__main__":
    main(sys.argv)
