"""Generate the red/black stats charts for the profile README: recoloured summary cards,
a Repos card and a Weekly Contributions chart.

Run daily by .github/workflows/profile-3d.yml. Standard library only.

    python3 scripts/profile_cards.py <github-user> <out-dir>

Env:
  GITHUB_TOKEN        optional, raises the REST rate limit for the public repo count
  REPO_COUNT_TOKEN    optional PAT that can see the user's private repos; when set,
                      the private count is live instead of PRIVATE_REPOS
  PRIVATE_REPOS       fallback private repo count (default 239, from the README)
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from collections import OrderedDict
from xml.sax.saxutils import escape

RED, RED2, MUTED, TEXT, BG, PANEL = "#ff2e4d", "#ff6b7d", "#a8828a", "#fff1f2", "#050102", "#140306"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"


def fetch(url, token=None, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "profile-cards"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def public_repo_count(user):
    return json.loads(fetch(f"https://api.github.com/users/{user}", os.environ.get("GITHUB_TOKEN")))["public_repos"]


def private_repo_count():
    token = os.environ.get("REPO_COUNT_TOKEN")
    if not token:
        return int(os.environ.get("PRIVATE_REPOS", "239")), False
    n, page = 0, 1
    while True:
        batch = json.loads(fetch(f"https://api.github.com/user/repos?visibility=private&affiliation=owner&per_page=100&page={page}", token))
        n += len(batch)
        if len(batch) < 100:
            return n, True
        page += 1


def daily_contributions(user):
    """Parse the public contributions calendar: {date: count} for the last year."""
    page = fetch(f"https://github.com/users/{user}/contributions", accept="text/html")
    dates = dict(re.findall(r'data-date="(\d{4}-\d\d-\d\d)"[^>]*id="(contribution-day-component-[\d-]+)"', page))
    ids = {v: k for k, v in dates.items()}
    counts = {}
    for cid, label in re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]+)</tool-tip>', page):
        m = re.match(r"(\d[\d,]*) contribution", label)
        counts[ids[cid]] = int(m.group(1).replace(",", "")) if m else 0
    assert len(counts) >= 300, f"only parsed {len(counts)} days, page format changed?"
    return dict(sorted(counts.items()))


def weekly(days):
    weeks = OrderedDict()
    for d, n in days.items():
        day = dt.date.fromisoformat(d)
        start = day - dt.timedelta(days=(day.weekday() + 1) % 7)  # weeks start on Sunday, like GitHub
        weeks[start] = weeks.get(start, 0) + n
    return weeks


def repos_svg(public, private, live):
    total = public + private
    cells = [("PUBLIC", public), ("PRIVATE", private), ("TOTAL", total)]
    body = []
    for i, (lab, n) in enumerate(cells):
        x = 20 + i * 104
        hi = lab == "TOTAL"
        body.append(f'<rect x="{x}" y="62" width="96" height="96" rx="6" fill="{RED if hi else PANEL}" fill-opacity="{.16 if hi else 1}" stroke="{RED}" stroke-opacity=".6"/>'
                    f'<text x="{x+48}" y="118" font-family="{SANS}" font-size="30" font-weight="800" fill="{TEXT}" text-anchor="middle">{n}</text>'
                    f'<text x="{x+48}" y="142" font-family="{MONO}" font-size="11" fill="{RED2}" text-anchor="middle" letter-spacing="1.5">{lab}</text>')
    note = "live" if live else "private count as stated"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="200" viewBox="0 0 340 200" role="img" aria-label="Repositories: {public} public, {private} private, {total} total">
<title>Repositories</title>
<rect x=".5" y=".5" width="339" height="199" rx="6" fill="{BG}" stroke="{RED}" stroke-opacity=".7"/>
<text x="20" y="38" font-family="{SANS}" font-size="18" font-weight="700" fill="{RED}">Repositories</text>
{"".join(body)}
<text x="20" y="184" font-family="{MONO}" font-size="10" fill="{MUTED}">updated {dt.date.today().isoformat()} · {note}</text>
</svg>
'''


def weekly_svg(weeks):
    items = list(weeks.items())[-52:]
    w, h, left, right, top, bottom = 1000, 280, 56, 20, 56, 44
    pw, ph = w - left - right, h - top - bottom
    peak = max(n for _, n in items) or 1
    step = 10 ** max(len(str(peak)) - 1, 0)
    ymax = ((peak + step - 1) // step) * step
    bw = pw / len(items)
    bars, labels, last_month = [], [], None
    for i, (start, n) in enumerate(items):
        bh = ph * n / ymax
        x = left + i * bw
        bars.append(f'<rect x="{x+1.5:.1f}" y="{top+ph-bh:.1f}" width="{bw-3:.1f}" height="{bh:.1f}" rx="2" fill="{RED}" fill-opacity="{.45 + .55*n/peak:.2f}"><title>Week of {start:%d %b %Y}: {n} contributions</title></rect>')
        if start.month != last_month:
            labels.append(f'<text x="{x:.1f}" y="{h-18}" font-family="{MONO}" font-size="11" fill="{MUTED}">{start:%b}</text>')
            last_month = start.month
    grid = []
    for k in range(5):
        v = ymax * k // 4
        y = top + ph - ph * k / 4
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w-right}" y2="{y:.1f}" stroke="{RED}" stroke-opacity=".12"/>'
                    f'<text x="{left-8}" y="{y+4:.1f}" font-family="{MONO}" font-size="11" fill="{MUTED}" text-anchor="end">{v}</text>')
    total = sum(n for _, n in items)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Contributions per week, last 52 weeks: {total} total, peak {peak} in one week">
<title>Contributions per week</title>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="6" fill="{BG}" stroke="{RED}" stroke-opacity=".7"/>
<text x="20" y="34" font-family="{SANS}" font-size="18" font-weight="700" fill="{RED}">Contributions per week</text>
<text x="{w-20}" y="34" font-family="{MONO}" font-size="12" fill="{MUTED}" text-anchor="end">last 52 weeks · {total:,} total · peak {peak}/week · updated {dt.date.today().isoformat()}</text>
{"".join(grid)}
{"".join(bars)}
{"".join(labels)}
</svg>
'''


SUMMARY_CARDS = ["stats", "most-commit-language", "repos-per-language", "profile-details"]
# github_dark theme colours -> red/black; language colours are left alone
RECOLOUR = {"#0d1117": BG, "#2e343b": RED, "#0366d6": RED, "#8b949e": RED, "#77909c": RED2, "#40c463": RED}


def summary_cards(user, out):
    for name in SUMMARY_CARDS:
        svg = fetch(f"https://github-profile-summary-cards.vercel.app/api/cards/{name}?username={user}&theme=github_dark", accept="image/svg+xml")
        assert svg.lstrip().startswith("<svg"), f"{name}: not an SVG"
        for old, new in RECOLOUR.items():
            svg = re.sub(re.escape(old), new, svg, flags=re.I)
        with open(os.path.join(out, f"{name}.svg"), "w") as f:
            f.write(svg)


# darkhub trophy theme -> red/black
TROPHY_RECOLOUR = {"#0d1117": BG, "#ff79c6": RED, "#ffb86c": "#ff8a3d", "#8be9fd": RED2, "#6272a4": "#7a2a35",
                   "#388bfd": RED, "#178600": RED2, "#8b949e": MUTED, "#ff5555": RED}


def trophies(user, out):
    svg = fetch(f"https://github-trophies.vercel.app/?username={user}&theme=darkhub&no-frame=true&margin-w=6&column=6", accept="image/svg+xml")
    assert "<svg" in svg[:200], "trophies: not an SVG"
    for old, new in TROPHY_RECOLOUR.items():
        svg = re.sub(re.escape(old), new, svg, flags=re.I)
    with open(os.path.join(out, "trophies.svg"), "w") as f:
        f.write(svg)


def main():
    user, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    summary_cards(user, out)
    trophies(user, out)
    private, live = private_repo_count()
    with open(os.path.join(out, "repos.svg"), "w") as f:
        f.write(repos_svg(public_repo_count(user), private, live))
    with open(os.path.join(out, "weekly.svg"), "w") as f:
        f.write(weekly_svg(weekly(daily_contributions(user))))
    print("wrote summary cards, repos.svg and weekly.svg")


if __name__ == "__main__":
    main()
