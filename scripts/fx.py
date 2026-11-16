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
import base64
import functools
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


def embers(x0, y0, w, h, n=14, cls="fx-ember"):
    # fixed spread rather than random, so a rebuild gives a byte-identical file
    dots = []
    for i in range(n):
        x = x0 + w * ((i * 0.618034) % 1)
        r = 1.4 + (i % 3) * 0.8
        dur = 6 + (i * 7 % 5)
        delay = -(i * 1.3 % dur)
        fill = EMBER if i % 3 else GLOW
        dots.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y0 + h + 6:.1f}" r="{r:.1f}" fill="{fill}" '
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


BG_MARK = 'class="bg"'
PANEL = re.compile(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="6" fill="url\(#panel\)"/>')
IMG = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"
# Which picture sits behind which card (assets/img/<name>.jpg). These pictures appear only
# inside cards, so build_image_cards.py skips them.
BACKDROPS = {"log": "red-gate", "profile": "igris-duel", "tools": "red-king", "skills": "red-throne"}
GRID_IMAGE, TROPHY_IMAGE = "red-cerberus", "red-army"
CARD_ONLY = set(BACKDROPS.values()) | {GRID_IMAGE, TROPHY_IMAGE}
MIME = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif"}


@functools.lru_cache(maxsize=None)
def data_uri(path):
    """data: URI for an image file, typed from its extension."""
    p = pathlib.Path(path)
    kind = MIME.get(p.suffix.lower())
    if not kind:
        raise ValueError(f"{p}: unsupported image type {p.suffix!r}")
    return f"data:image/{kind};base64," + base64.b64encode(p.read_bytes()).decode()


def card_backdrop(name, svg):
    """backdrop() with the picture BACKDROPS assigns to card `name`."""
    return backdrop(svg, data_uri(IMG / (BACKDROPS[name] + ".jpg")))


# The standalone photos' motion (slow zoom, pulsing red vignette, rising embers) for a picture
# behind a card. Own class and id names, so it never clashes with add_fx() on the same card.
BG_CSS = (".bg-zoom{transform-box:fill-box;transform-origin:center;animation:bg-zoom 18s ease-in-out infinite alternate}"
          "@keyframes bg-zoom{from{transform:scale(1)}to{transform:scale(1.07)}}"
          ".bg-vig{animation:bg-vig 4s ease-in-out infinite}@keyframes bg-vig{0%,100%{opacity:.55}50%{opacity:.95}}"
          ".bg-ember{opacity:0;animation:bg-rise 7s linear infinite}"
          "@media (prefers-reduced-motion:reduce){.bg-zoom,.bg-vig,.bg-ember{animation:none!important}}")


def picture_layer(box, x, y, w, h, opacity, uri, base=""):
    """The clipped, moving picture: box is the card area as (x, y, w, h); x,y,w,h place the image."""
    bx, by, bw, bh = (float(v) for v in box[:4])
    rise = -(bh + 20)
    css = BG_CSS + ("@keyframes bg-rise{0%%{transform:translateY(0);opacity:0}15%%{opacity:.9}85%%{opacity:.6}"
                    "100%%{transform:translateY(%.0fpx);opacity:0}}" % rise)
    shape = f'x="{bx:g}" y="{by:g}" width="{bw:g}" height="{bh:g}" rx="{box[4]}"'
    return (f'<g {BG_MARK} aria-hidden="true" clip-path="url(#bg-clip)"><defs><clipPath id="bg-clip"><rect {shape}/></clipPath>'
            '<radialGradient id="bg-vg" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#050102" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#3a0008" stop-opacity=".85"/></radialGradient><style>{css}</style></defs>{base}'
            f'<image class="bg-zoom" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" opacity="{opacity}" href="{uri}"/>'
            f'<rect class="bg-vig" {shape} fill="url(#bg-vg)"/>{embers(bx, by, bw, bh, cls="bg-ember")}</g>')


def backdrop(svg, data_uri, opacity=0.32):
    """Return svg with the image laid behind its text, just above the card panel; unchanged if it has one."""
    if BG_MARK in svg:
        return svg
    m = PANEL.search(svg)
    if not m:
        raise ValueError('no <rect ... fill="url(#panel)"/> to lay the image on')
    x, y, w, h = m.groups()
    layer = picture_layer((x, y, w, h, 6), x, y, w, h, opacity, data_uri)
    return svg[:m.end()] + layer + svg[m.end():]


def underlay(svg, uri, x, y, w, h, opacity=0.3, after=None, base=None, inset=1.5, rx=5):
    """Return svg with the image placed at x,y,w,h (card units) behind everything drawn after
    the first match of `after` (the root tag when None); unchanged if it already has one.
    A negative x/y with a larger w/h shows one tile of a picture spread over several cards.
    The image is clipped to the card's rounded shape, `inset` inside the edge so the border
    stays on top; `base` paints a solid colour under it for cards with no background."""
    if BG_MARK in svg:
        return svg
    m = re.search(after, svg) if after else re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise ValueError(f"no anchor for the background: {after or '<svg>'}")
    x0, y0, cw, ch = size(svg)
    box = (x0 + inset, y0 + inset, cw - 2 * inset, ch - 2 * inset, rx)
    fill = f'<rect x="{box[0]:g}" y="{box[1]:g}" width="{box[2]:g}" height="{box[3]:g}" fill="{base}"/>' if base else ""
    return svg[:m.end()] + picture_layer(box, x, y, w, h, opacity, uri, fill) + svg[m.end():]


SWEEP_MARK = 'class="fx-sweep"'
FRAME = re.compile(r'<rect class="frame" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="6"[^>]*/>')


def sweep(svg):
    """Return svg with the red light band sweeping across its framed window, on top of the
    content but inside the frame (add_fx's beam spans the whole SVG, margins included).
    Unchanged if it already has one."""
    if SWEEP_MARK in svg:
        return svg
    m = FRAME.search(svg)
    if not m:
        raise ValueError('no <rect class="frame" ... rx="6"/> to sweep across')
    end = svg.rfind("</svg>")
    if end < 0:
        raise ValueError("no closing </svg>")
    x, y, w, h = (float(v) for v in m.groups())
    band = max(w * 0.18, 60)
    css = (".fx-sweep{animation:fx-sweep 7s cubic-bezier(.4,0,.6,1) infinite}"
           "@keyframes fx-sweep{0%%{transform:translateX(%.0fpx)}55%%,100%%{transform:translateX(%.0fpx)}}" % (-band, w + band)
           + "@media (prefers-reduced-motion:reduce){.fx-sweep{animation:none!important}}")
    layer = (f'<g aria-hidden="true" clip-path="url(#fx-sweep-clip)"><defs><clipPath id="fx-sweep-clip">'
             f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="6"/></clipPath>'
             f'<linearGradient id="fx-sweep-band" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{RED}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{RED}" stop-opacity=".22"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>'
             f'<style>{css}</style></defs><rect {SWEEP_MARK} x="{x:g}" y="{y:g}" width="{band:.1f}" height="{h:g}" fill="url(#fx-sweep-band)"/></g>')
    return svg[:end] + layer + "\n" + svg[end:]


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
    card = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 300"><rect x="40" y="20" width="1200" height="260" rx="6" fill="url(#panel)"/><text>t</text></svg>'
    bg = backdrop(card, "data:image/gif;base64,R0lGODlhAQABAAAAACw=")
    assert backdrop(bg, "x") == bg, "backdrop is not idempotent"
    framed = card.replace("<text>", '<rect class="frame" x="40" y="20" width="1200" height="260" rx="6" filter="url(#glow)"/><text>')
    swept = sweep(framed)
    assert sweep(swept) == swept and swept.count(SWEEP_MARK) == 1, "sweep is not idempotent"
    assert swept.index(SWEEP_MARK) > swept.index("<text>") and 'x="40" y="20" width="1200" height="260"' in swept, "sweep not on top, inside the frame"
    ET.fromstring(swept)
    try:
        sweep(card)
    except ValueError:
        pass
    else:
        raise AssertionError("card without a frame not rejected")
    assert all(c in bg for c in ('class="bg-zoom"', 'class="bg-vig"', 'class="bg-ember"', "prefers-reduced-motion")), "backdrop has no motion"
    assert bg.index("<image") < bg.index("<text"), "backdrop is not behind the text"
    ET.fromstring(bg)
    try:
        backdrop("<svg></svg>", "x")
    except ValueError:
        pass
    else:
        raise AssertionError("card without a panel not rejected")
    chart = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 200"><rect id="bgr"></rect><text>t</text></svg>'
    under = underlay(chart, "x", -340, 0, 680, 400, after=r'<rect id="bgr"></rect>')
    assert under.index("</rect><g " + BG_MARK) > 0 and under.index("<image") < under.index("<text"), "underlay misplaced"
    assert 'clip-path="url(#bg-clip)"' in under and 'width="337"' in under, "underlay not clipped inside the border"
    assert underlay(under, "x", 0, 0, 1, 1) == under, "underlay is not idempotent"
    ET.fromstring(under)
    based = underlay(chart, "x", 0, 0, 340, 200, base="#050102")
    assert based.index('fill="#050102"') < based.index("<image"), "base colour not under the image"
    ET.fromstring(based)
    assert data_uri(IMG / (GRID_IMAGE + ".jpg")).startswith("data:image/jpeg;base64,")
    try:
        data_uri(pathlib.Path(__file__))
    except ValueError:
        pass
    else:
        raise AssertionError("non-image file not rejected")
    print("fx.py: selftest ok")


def main(argv):
    if argv[1:] == ["--selftest"]:
        return selftest()
    if argv[1:2] == ["--backdrop"]:
        return main_backdrop(argv[2:])
    if argv[1:2] == ["--sweep"]:
        return main_sweep(argv[2:])
    if len(argv) < 2:
        sys.exit("fx.py: usage: fx.py <file.svg>... | --backdrop <card.svg>... | --sweep <card.svg>... | --selftest")
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


def main_backdrop(args):
    # For cards with no build script (skills.svg); the built cards get theirs from the build.
    if not args:
        sys.exit("fx.py: usage: fx.py --backdrop <card.svg>...  (picture from BACKDROPS)")
    for name in args:
        card = pathlib.Path(name)
        if card.stem not in BACKDROPS:
            sys.exit(f"fx.py: {card}: no picture assigned in BACKDROPS")
        try:
            svg = card.read_text()
            out = card_backdrop(card.stem, svg)
        except (OSError, ValueError) as e:
            sys.exit(f"fx.py: {card}: {e}")
        if out == svg:
            print(f"fx.py: {card}: already has a backdrop")
            continue
        try:
            card.write_text(out)
        except OSError as e:
            sys.exit(f"fx.py: cannot write {card}: {e}")
        print(f"fx.py: {card}: backdrop {BACKDROPS[card.stem]} added")


def main_sweep(args):
    # For cards with no build script (hero, quest, status, join); the built cards get theirs from the build.
    if not args:
        sys.exit("fx.py: usage: fx.py --sweep <card.svg>...")
    for name in args:
        card = pathlib.Path(name)
        try:
            svg = card.read_text()
            out = sweep(svg)
        except (OSError, ValueError) as e:
            sys.exit(f"fx.py: {card}: {e}")
        if out == svg:
            print(f"fx.py: {card}: already has the sweep")
            continue
        try:
            card.write_text(out)
        except OSError as e:
            sys.exit(f"fx.py: cannot write {card}: {e}")
        print(f"fx.py: {card}: sweep added")


if __name__ == "__main__":
    main(sys.argv)
