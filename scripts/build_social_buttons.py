"""Build the eight Socials buttons, all the same size, in the red/black System style.

Usage: python3 scripts/build_social_buttons.py assets/social
The shields.io badges they replace were 52 to 123px wide and cannot be scaled to one size.
Logos come from the same pinned simple-icons release as the Inventory card; LinkedIn is not
in simple-icons, so it gets a monogram.
"""
import pathlib
import sys
from xml.sax.saxutils import escape

from build_inventory_card import icon_path
from fx import sweep

W, H = 240, 56
RED, PANEL, TEXT = "#ff2e4d", "#140306", "#fff1f2"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
# file name, label, simple-icons slug (None = monogram)
BUTTONS = [("website", "Website", "googlechrome"), ("linkedin", "LinkedIn", None),
           ("github", "GitHub", "github"), ("instagram", "Instagram", "instagram"),
           ("x", "X", "x"), ("threads", "Threads", "threads"),
           ("email", "Email", "gmail"), ("kofi", "Ko-fi", "kofi")]


def button(label, path):
    if path:
        icon = f'<g transform="translate(22,16)"><path d="{path}" fill="{RED}"/></g>'
    else:
        icon = (f'<rect x="22" y="16" width="24" height="24" rx="4" fill="{RED}"/>'
                f'<text x="34" y="33.5" font-family="{SANS}" font-size="13" font-weight="800" fill="{PANEL}" text-anchor="middle">in</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(label)}">
<title>{escape(label)}</title>
<defs><style>.frame{{fill:{PANEL};stroke:{RED};stroke-width:2;animation:pulse 3s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{stroke-opacity:.55}}50%{{stroke-opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.frame{{animation:none}}}}</style></defs>
<rect class="frame" x="1" y="1" width="{W - 2}" height="{H - 2}" rx="6"/>
{icon}
<text x="60" y="35" font-family="{SANS}" font-size="17" font-weight="700" fill="{TEXT}" letter-spacing="1.5">{escape(label.upper())}</text>
</svg>
'''


def main():
    if len(sys.argv) < 2:
        sys.exit("build_social_buttons.py: usage: build_social_buttons.py <out-dir>")
    out = pathlib.Path(sys.argv[1])
    try:
        out.mkdir(parents=True, exist_ok=True)
        for name, label, slug in BUTTONS:
            (out / f"{name}.svg").write_text(sweep(button(label, icon_path(slug) if slug else None)))
    except OSError as e:
        sys.exit(f"build_social_buttons.py: {e}")
    print(f"built {len(BUTTONS)} buttons in {out}")


if __name__ == "__main__":
    main()
