"""Build the red/black Inventory card (tools.svg) and its phone version (tools-narrow.svg) from simple-icons logos.

Usage: python3 scripts/build_inventory_card.py assets/cards
Reads the embedded @font-face block from hero.svg; fetches each logo from the pinned
simple-icons release on jsDelivr. Tools without a logo there get a monogram.
"""
import re
import sys
import pathlib
import urllib.request
from xml.sax.saxutils import escape

from fx import card_backdrop, sweep, fit_to_frame

SIMPLE_ICONS = "16.37.0"
TOOLS = [("kotlin", "Kotlin", "MOBILE"), ("jetpackcompose", "Jetpack Compose", "MOBILE"), ("android", "Android", "MOBILE"),
         ("typescript", "TypeScript", "WEB"), ("react", "React", "WEB"), ("nextdotjs", "Next.js", "WEB"),
         ("python", "Python", "SYSTEMS"), ("rust", "Rust", "SYSTEMS"), ("sqlite", "SQLite", "DATA"),
         ("playwright", "Playwright", "QA"), ("selenium", "Selenium", "QA"), ("appium", "Appium", "QA"),
         ("postman", "Postman", "API"), ("firebase", "Firebase", "CLOUD"), ("cloudflare", "Cloudflare", "EDGE"),
         ("githubactions", "GitHub Actions", "CI"), ("git", "Git", "VCS")]
MONOGRAM = {"playwright": "PW"}  # not in simple-icons
RED, RED2, MUTED, TEXT, PINK = "#ff2e4d", "#ff6b7d", "#a8828a", "#fff1f2", "#ffb3bc"


def icon_path(slug):
    if slug in MONOGRAM:
        return None
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@{SIMPLE_ICONS}/icons/{slug}.svg"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            m = re.search(r'<path d="([^"]+)"', r.read().decode())
    except OSError as e:
        sys.exit(f"build_inventory_card.py: cannot fetch {url}: {e}")
    if not m:
        sys.exit(f"build_inventory_card.py: no path in {url}")
    return m.group(1)


def main():
    if len(sys.argv) < 2:
        sys.exit("build_inventory_card.py: usage: build_inventory_card.py <cards-dir>")
    cards = pathlib.Path(sys.argv[1])
    hero = cards / "hero.svg"
    if not hero.is_file():
        sys.exit(f"build_inventory_card.py: no such file: {hero}")
    fonts = re.search(r"@font-face\{font-family:'SLOrb'.*?\n", hero.read_text(), re.S).group(0)
    paths = {slug: icon_path(slug) for slug, _, _ in TOOLS}
    # wide: 6 columns in the 1200 panel; narrow (phone, picked by <picture> in the README): 3 in a 480 panel
    (cards / "tools.svg").write_text(card(fonts, paths, 1200, 6, 182, 14))
    (cards / "tools-narrow.svg").write_text(card(fonts, paths, 480, 3, 141, 12))
    print("built tools.svg, tools-narrow.svg")


def card(fonts, paths, pw, cols, tw, gx):
    th, gy, y0 = 118, gx, 88
    x0 = 40 + (pw - (cols * tw + (cols - 1) * gx)) // 2  # grid centred in the panel
    r_edge, cw = 40 + pw, 80 + pw
    rows = -(-len(TOOLS) // cols)
    H = y0 + rows * th + (rows - 1) * gy + 44
    tiles = []
    for i, (slug, name, tag) in enumerate(TOOLS):
        r, c = divmod(i, cols)
        x, y = x0 + c * (tw + gx), y0 + r * (th + gy)
        d = 0.25 + c * 0.12 + r * 0.18
        path = paths[slug]
        if path:
            icon = f'<g transform="translate({x+tw/2-18},{y+20}) scale(1.5)"><path d="{path}" fill="{RED}" filter="url(#glow)"/></g>'
        else:
            icon = (f'<rect x="{x+tw/2-18}" y="{y+20}" width="36" height="36" rx="6" fill="none" stroke="{RED}" stroke-width="2.5"/>'
                    f'<text x="{x+tw/2}" y="{y+44}" class="sans" font-size="15" font-weight="900" fill="{RED}" text-anchor="middle">{MONOGRAM[slug]}</text>')
        tiles.append(f'<g class="tile" style="animation-delay:{d:.2f}s"><rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="6" fill="{RED}" fill-opacity=".06" stroke="{RED}" stroke-opacity=".5"/>{icon}'
                     f'<text x="{x+tw/2}" y="{y+82}" class="mono" font-size="15" fill="{TEXT}" text-anchor="middle">{escape(name)}</text>'
                     f'<text x="{x+tw/2}" y="{y+102}" class="mono" font-size="10" fill="{RED2}" text-anchor="middle" letter-spacing="2">{tag}</text></g>')
    names = ", ".join(n for _, n, _ in TOOLS)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {H}" width="{cw}" height="{H}" role="img" aria-label="Inventory: {names}">
<title>Inventory — Tools</title>
<desc>Solo Leveling style inventory window with {len(TOOLS)} tools: {names}.</desc>
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a0508" stop-opacity=".96"/><stop offset="1" stop-color="#0d0204" stop-opacity=".96"/></linearGradient>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="fglow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
{fonts}.mono{{font-family:'SLMono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}}
.sans{{font-family:'SLOrb','Segoe UI','Helvetica Neue',Arial,sans-serif}}
.frame{{fill:none;stroke:{RED};stroke-width:2;animation:pulse 3s ease-in-out infinite}}
.corner{{fill:none;stroke:{PINK};stroke-width:4}}
.tile{{opacity:.15;animation:unlock .4s ease forwards}}
@keyframes pulse{{0%,100%{{stroke-opacity:.55}}50%{{stroke-opacity:1}}}}
@keyframes unlock{{to{{opacity:1}}}}
</style>
</defs>
<rect width="{cw}" height="{H}" fill="#050102"/>
<rect x="40" y="20" width="{pw}" height="{H-40}" rx="6" fill="url(#panel)"/>
<rect class="frame" x="40" y="20" width="{pw}" height="{H-40}" rx="6" filter="url(#fglow)"/>
<path class="corner" d="M40 52V20h32M{r_edge - 32} 20h32v32M{r_edge} {H-52}v32h-32M72 {H-20}H40v-32"/>
<rect x="40" y="20" width="{pw}" height="44" fill="{RED}" fill-opacity=".08"/>
<text x="76" y="49" class="mono" font-size="16" fill="{RED2}" letter-spacing="3">⟨ INVENTORY ⟩</text>
<text x="{r_edge - 36}" y="49" class="mono" font-size="14" fill="{MUTED}" text-anchor="end" letter-spacing="2">{len(TOOLS)} ITEMS EQUIPPED</text>
<line x1="40" y1="64" x2="{r_edge}" y2="64" stroke="{RED}" stroke-opacity=".5"/>
{chr(10).join(tiles)}
</svg>
'''
    return fit_to_frame(sweep(card_backdrop("tools", svg)))


if __name__ == "__main__":
    main()
