"""Build the S-Rank Missions header and row cards in the red/black System style.

GitHub strips inline colour from README markup, so each table row is rendered as its own
SVG and linked from the README.

    python3 scripts/build_mission_cards.py profile-3d-contrib/missions [--stars]

The cards are published to the output-3d branch by .github/workflows/profile-3d.yml, next
to the other generated charts, so the output directory is a build directory and not a
committed one. The README links them by raw URL from that branch.

Each row gets two files: a wide four-column card and a narrow stacked one. An <img> takes
its height from the viewBox aspect ratio, so one file cannot hold two layouts of different
heights; the README picks between them with <picture><source media>.

Reads the embedded @font-face block from assets/cards/hero.svg so the cards carry the same
fonts as every other card. With --stars, the stargazer count of each repo is fetched and
baked into the card; without it, whatever counts are already on disk are kept, so a card is
never silently reset to zero by a run that could not reach the API.

Env:
  GITHUB_TOKEN   optional, raises the REST rate limit for the star counts
"""
import json
import os
import pathlib
import re
import sys
import textwrap
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

from fx import add_fx

BG, NAME, DESC = "#050102", "#ff2e4d", "#fff1f2"
PILL, PILL_TEXT, BORDER = "#7a1424", "#ffb3bc", "#3a0d14"
STAR, HEAD = "#ffb3bc", "#ff6b7d"

W = 1000              # viewBox width; the README renders each card at width 100%
PAD = 22
X_NAME = PAD + 10
W_NAME = 210
X_DESC = X_NAME + W_NAME + 20
W_DESC = 480
X_PILL = X_DESC + W_DESC + 20
W_PILL = 150
X_STAR = W - PAD - 54

NAME_PX = 9.3         # SLOrb advance at 17px, measured against the other cards
MONO_PX = 8.1         # Share Tech Mono advance at 15px
DESC_SIZE = 15
LINE_H = 21

MISSIONS = [
    ("OrbiAgents", "https://github.com/SUDARSHANCHAUDHARI/OrbiAgents", "SUDARSHANCHAUDHARI/OrbiAgents",
     "Visual multi-agent workflow orchestration, execution, and replay — the largest codebase here, with 274 test files", "TypeScript"),
    ("QACraft", "https://github.com/SUDARSHANCHAUDHARI/QACraft", "SUDARSHANCHAUDHARI/QACraft",
     "Reusable QA skills and deterministic behaviour evaluations, with adapters for Codex, Claude Code, Copilot, and Gemini CLI", "HTML"),
    ("RepoMem", "https://github.com/SUDARSHANCHAUDHARI/RepoMem", "SUDARSHANCHAUDHARI/RepoMem",
     "Persistent, local-first memory for AI coding agents using SQLite and FTS5, with zero dependencies", "Python"),
    ("SaveMyTerminal", "https://github.com/SUDARSHANCHAUDHARI/SaveMyTerminal", "SUDARSHANCHAUDHARI/SaveMyTerminal",
     "Local, privacy-safe observability for terminal-based AI agents — published on crates.io", "Rust"),
    ("TemporalThread", "https://github.com/SUDARSHANCHAUDHARI/TemporalThread", "SUDARSHANCHAUDHARI/TemporalThread",
     "Local-first MCP server that gives AI agents a persistent sense of time, with no network port and no telemetry", "TypeScript"),
    ("RepoGuardAI", "https://github.com/SUDARSHANCHAUDHARI/RepoGuardAI", "SUDARSHANCHAUDHARI/RepoGuardAI",
     "Agent-independent security and code auditing with deterministic scanners and structured reports", "JavaScript"),
    ("BarStripeLab", "https://github.com/SUDARSHANCHAUDHARI/BarStripeLab", "SUDARSHANCHAUDHARI/BarStripeLab",
     "Free in-browser barcode generator that shapes EAN, UPC and Code 128 codes while keeping them scannable — GS1 sizing, decode checks and exact-size SVG/PDF export (live)", "TypeScript"),
    # No repo: a hosted site, so it shows a globe rather than a star count.
    ("MyWindChimes", "https://mywindchimes.sudarshantechlabs.com", None,
     "Interactive wind chimes from seven Asian countries on handmade paper — photoreal chime tops, a physics-driven curtain of each country's script, crossfading journeys and procedural sound (live)", "Web"),
]


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def fonts_from(_unused=None):
    # Always the committed hero card, never the output directory: the cards are published
    # to the output-3d branch, so the output directory holds yesterday's copies only.
    hero = pathlib.Path(__file__).resolve().parent.parent / "assets" / "cards" / "hero.svg"
    if not hero.is_file():
        sys.exit(f"build_mission_cards.py: no such file: {hero}")
    m = re.search(r"@font-face\{font-family:'SLOrb'.*?\n", hero.read_text(), re.S)
    if not m:
        sys.exit("build_mission_cards.py: no embedded fonts in hero.svg")
    return m.group(0)


def wrap(text, width_px, size):
    cols = max(8, int(width_px / (MONO_PX * size / 15)))
    return textwrap.wrap(text, cols) or [""]


def fetch_stars(repo):
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "mission-cards"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["stargazers_count"]


def load_existing_stars(out):
    """Star counts already baked into the cards on disk, so a failed fetch keeps them."""
    found = {}
    for name, _href, repo, _desc, _lang in MISSIONS:
        if not repo:
            continue
        p = out / f"{slug(name)}.svg"
        if not p.is_file():
            continue
        m = re.search(r'data-stars="(\d+)"', p.read_text())
        if m:
            found[name] = int(m.group(1))
    return found


def star_counts(out, fetch):
    counts = load_existing_stars(out)
    if not fetch:
        return counts
    for name, _href, repo, _desc, _lang in MISSIONS:
        if not repo:
            continue
        try:
            counts[name] = fetch_stars(repo)
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
            kept = counts.get(name)
            print(f"::warning::build_mission_cards.py: {repo} stars not fetched ({e}); "
                  + (f"keeping {kept}" if kept is not None else "card will show no count"),
                  file=sys.stderr)
    return counts


def shell(h, title, desc, fonts, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(desc)}">
<title>{escape(title)}</title>
<desc>{escape(desc)}</desc>
<defs><style>
{fonts}.mono{{font-family:'SLMono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}}
.sans{{font-family:'SLOrb','Segoe UI','Helvetica Neue',Arial,sans-serif}}
</style></defs>
<rect width="{W}" height="{h}" rx="6" fill="{BG}"/>
<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="6" fill="none" stroke="{BORDER}"/>
{body}
</svg>
'''


def header_card(fonts):
    h = 46
    y = 29
    cols = [(X_NAME, "MISSION", "start"), (X_DESC, "WHAT IT IS", "start"),
            (X_PILL, "BUILT WITH", "start"), (X_STAR + 27, "★", "middle")]
    body = [f'<rect x="0" y="0" width="{W}" height="{h}" rx="6" fill="{NAME}" fill-opacity=".07"/>']
    for x, label, anchor in cols:
        body.append(f'<text x="{x}" y="{y}" class="mono" font-size="13" fill="{HEAD}" '
                    f'text-anchor="{anchor}" letter-spacing="2">{escape(label)}</text>')
    return shell(h, "S-Rank Missions", "Table header: Mission, What it is, Built with, stars.",
                 fonts, "\n".join(body))


def row_card(name, desc, lang, stars, fonts):
    lines = wrap(desc, W_DESC, DESC_SIZE)
    h = max(72, PAD * 2 + len(lines) * LINE_H)
    top = (h - len(lines) * LINE_H) / 2 + 15

    body = []
    name_lines = wrap(name, W_NAME, 17)
    ny = (h - len(name_lines) * 22) / 2 + 17
    for line in name_lines:
        body.append(f'<text x="{X_NAME}" y="{ny:.0f}" class="sans" font-size="17" '
                    f'font-weight="700" fill="{NAME}">{escape(line)}</text>')
        ny += 22

    y = top
    for line in lines:
        body.append(f'<text x="{X_DESC}" y="{y:.0f}" class="mono" font-size="{DESC_SIZE}" '
                    f'fill="{DESC}">{escape(line)}</text>')
        y += LINE_H

    pill_w = min(W_PILL, int(len(lang) * 7.6) + 24)
    pill_y = (h - 24) / 2
    body.append(f'<rect x="{X_PILL}" y="{pill_y:.0f}" width="{pill_w}" height="24" rx="12" fill="{PILL}"/>')
    body.append(f'<text x="{X_PILL + pill_w / 2:.0f}" y="{pill_y + 16:.0f}" class="mono" font-size="13" '
                f'fill="{PILL_TEXT}" text-anchor="middle">{escape(lang)}</text>')

    mid = h / 2 + 5
    if stars is None:
        body.append(f'<text x="{X_STAR + 27}" y="{mid:.0f}" class="mono" font-size="16" '
                    f'fill="{STAR}" text-anchor="middle">\U0001f310</text>')
        star_desc = "a hosted site"
    else:
        body.append(f'<text x="{X_STAR + 27}" y="{mid:.0f}" class="mono" font-size="14" '
                    f'fill="{STAR}" text-anchor="middle" data-stars="{stars}">'
                    f'★ {stars}</text>')
        star_desc = f"{stars} star{'s' if stars != 1 else ''}"

    alt = f"{name} — {desc} Built with {lang}, {star_desc}."
    return shell(h, name, alt, fonts, "\n".join(body)), alt, h


NARROW_W = 480          # a phone renders this at roughly 358px, so 15px text stays legible
NARROW_BREAK = 520      # the <source media> breakpoint the README uses


def narrow_shell(h, title, desc, fonts, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {NARROW_W} {h}" width="{NARROW_W}" height="{h}" role="img" aria-label="{escape(desc)}">
<title>{escape(title)}</title>
<desc>{escape(desc)}</desc>
<defs><style>
{fonts}.mono{{font-family:'SLMono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}}
.sans{{font-family:'SLOrb','Segoe UI','Helvetica Neue',Arial,sans-serif}}
</style></defs>
<rect width="{NARROW_W}" height="{h}" rx="6" fill="{BG}"/>
<rect x=".5" y=".5" width="{NARROW_W - 1}" height="{h - 1}" rx="6" fill="none" stroke="{BORDER}"/>
{body}
</svg>
'''


def narrow_header_card(fonts):
    """The stacked cards carry their own labels, so the narrow header is just a title bar."""
    h = 34
    body = [f'<rect x="0" y="0" width="{NARROW_W}" height="{h}" rx="6" fill="{NAME}" fill-opacity=".07"/>',
            f'<text x="16" y="22" class="mono" font-size="14" fill="{HEAD}" '
            f'letter-spacing="2">S-RANK MISSIONS</text>']
    return narrow_shell(h, "S-Rank Missions", "S-Rank Missions.", fonts, "\n".join(body)), h


def narrow_card(name, desc, lang, stars, fonts):
    """Stacked layout: name, then the description, then the pill and star on one line.

    A separate file rather than a media query inside the wide card: an <img> locks its
    height to the viewBox aspect ratio, so no rule inside one file can give a stacked
    layout the extra vertical room it needs.
    """
    pad = 16
    inner = NARROW_W - pad * 2
    lines = wrap(desc, inner, DESC_SIZE)

    y = pad + 20
    body = [f'<text x="{pad}" y="{y}" class="sans" font-size="19" font-weight="700" '
            f'fill="{NAME}">{escape(name)}</text>']
    y += 24
    for line in lines:
        body.append(f'<text x="{pad}" y="{y}" class="mono" font-size="{DESC_SIZE}" '
                    f'fill="{DESC}">{escape(line)}</text>')
        y += LINE_H
    y += 6

    pill_w = min(W_PILL, int(len(lang) * 7.6) + 24)
    body.append(f'<rect x="{pad}" y="{y}" width="{pill_w}" height="24" rx="12" fill="{PILL}"/>')
    body.append(f'<text x="{pad + pill_w / 2:.0f}" y="{y + 16}" class="mono" font-size="13" '
                f'fill="{PILL_TEXT}" text-anchor="middle">{escape(lang)}</text>')
    if stars is None:
        body.append(f'<text x="{NARROW_W - pad}" y="{y + 17}" class="mono" font-size="15" '
                    f'fill="{STAR}" text-anchor="end">\U0001f310</text>')
        star_desc = "a hosted site"
    else:
        body.append(f'<text x="{NARROW_W - pad}" y="{y + 17}" class="mono" font-size="14" '
                    f'fill="{STAR}" text-anchor="end" data-stars="{stars}">★ {stars}</text>')
        star_desc = f"{stars} star{'s' if stars != 1 else ''}"
    h = y + 24 + pad

    alt = f"{name} — {desc} Built with {lang}, {star_desc}."
    return narrow_shell(h, name, alt, fonts, "\n".join(body)), h


def main(argv):
    if len(argv) < 2:
        sys.exit("build_mission_cards.py: usage: build_mission_cards.py <missions-dir> [--stars]")
    out = pathlib.Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    fonts = fonts_from()
    counts = star_counts(out, "--stars" in argv[2:])

    out.joinpath("_header.svg").write_text(add_fx(header_card(fonts)))
    nh_svg, nh_h = narrow_header_card(fonts)
    out.joinpath("_header-narrow.svg").write_text(add_fx(nh_svg))
    written = [("_header.svg", W, 46), ("_header-narrow.svg", NARROW_W, nh_h)]
    for name, _href, repo, desc, lang in MISSIONS:
        stars = counts.get(name) if repo else None
        wide, _alt, hw = row_card(name, desc, lang, stars, fonts)
        narrow, hn = narrow_card(name, desc, lang, stars, fonts)
        fn, fn_n = f"{slug(name)}.svg", f"{slug(name)}-narrow.svg"
        out.joinpath(fn).write_text(add_fx(wide))
        out.joinpath(fn_n).write_text(add_fx(narrow))
        written += [(fn, W, hw), (fn_n, NARROW_W, hn)]

    print(f"build_mission_cards.py: wrote {len(written)} cards to {out}")
    for fn, w, h in written:
        print(f"  {fn:30s} {w}x{h}")


if __name__ == "__main__":
    main(sys.argv)
