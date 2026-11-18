"""Build the four text cards (player log, profile, record, quote) in the red/black System style,
each with a phone version, plus phone versions of the hand-made hero, quest, skills, status and join cards.

Usage: python3 scripts/build_text_cards.py assets/cards
Reads the embedded @font-face block from hero.svg so every card carries the same fonts.
"""
import sys, re, textwrap, pathlib
from xml.sax.saxutils import escape

from fx import BACKDROPS, IMG, JOIN_IMAGE, add_embers, backdrop, card_backdrop, data_uri, sweep, fit_to_frame

if len(sys.argv) < 2:
    sys.exit("build_text_cards.py: usage: build_text_cards.py <cards-dir>")
cards = pathlib.Path(sys.argv[1])
hero = cards / "hero.svg"
if not hero.is_file():
    sys.exit(f"build_text_cards.py: no such file: {hero}")
fonts = re.search(r"@font-face\{font-family:'SLOrb'.*?\n", hero.read_text(), re.S)
if not fonts:
    sys.exit("build_text_cards.py: no embedded fonts in hero.svg")
fonts = fonts.group(0)

RED, RED2, PINK, MUTED, TEXT, SOFT = "#ff2e4d", "#ff6b7d", "#ffb3bc", "#a8828a", "#fff1f2", "#f5e9eb"
MONO_PX = 8.1  # Share Tech Mono advance at 15px


WIDE, NARROW = 1200, 480  # panel widths; a phone shows the narrow one at ~358px, so 15px text stays legible
NX = 56                   # text x inside a narrow panel (the wide cards use 76)


def frame(name, h, label, right, body, desc, extra_css="", pw=WIDE):
    """One System window; a narrow one keeps the right-hand header label only when it clears the
    left label (mono advance 0.54 em plus letter-spacing: 11.6px a char at 16px, 9.56px at 14px)."""
    r, cw = 40 + pw, 80 + pw
    fits = pw == WIDE or 76 + (len(label) + 4) * 11.6 + 24 < r - 36 - len(right) * 9.56
    head = (f'<text x="{r - 36}" y="49" class="mono" font-size="14" fill="{MUTED}" text-anchor="end" letter-spacing="2">{escape(right)}</text>\n'
            if right and fits else "")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {h}" width="{cw}" height="{h}" role="img" aria-label="{escape(desc)}">
<title>{escape(label.title())}</title>
<desc>{escape(desc)}</desc>
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a0508" stop-opacity=".96"/><stop offset="1" stop-color="#0d0204" stop-opacity=".96"/></linearGradient>
<radialGradient id="ember" cx=".85" cy=".2" r=".6"><stop offset="0" stop-color="#8b0000" stop-opacity=".35"/><stop offset="1" stop-color="#8b0000" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
{fonts}.mono{{font-family:'SLMono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}}
.sans{{font-family:'SLOrb','Segoe UI','Helvetica Neue',Arial,sans-serif}}
.frame{{fill:none;stroke:{RED};stroke-width:2;animation:pulse 3s ease-in-out infinite}}
.corner{{fill:none;stroke:{PINK};stroke-width:4}}
.row{{opacity:0;animation:in .6s ease forwards}}
.scan{{animation:scan 5s linear infinite}}
@keyframes pulse{{0%,100%{{stroke-opacity:.55}}50%{{stroke-opacity:1}}}}
@keyframes in{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({h-60}px)}}}}
{extra_css}</style>
</defs>
<rect width="{cw}" height="{h}" fill="#050102"/>
<rect x="40" y="20" width="{pw}" height="{h-40}" rx="6" fill="url(#panel)"/>
<rect x="40" y="20" width="{pw}" height="{h-40}" rx="6" fill="url(#ember)"/>
<rect class="scan" x="42" y="66" width="{pw - 4}" height="2" fill="{RED2}" opacity=".12"/>
<rect class="frame" x="40" y="20" width="{pw}" height="{h-40}" rx="6" filter="url(#glow)"/>
<path class="corner" d="M40 52V20h32M{r - 32} 20h32v32M{r} {h-52}v32h-32M72 {h-20}H40v-32"/>
<rect x="40" y="20" width="{pw}" height="44" fill="{RED}" fill-opacity=".08"/>
<text x="76" y="49" class="mono" font-size="16" fill="{RED2}" letter-spacing="3">⟨ {escape(label)} ⟩</text>
{head}<line x1="40" y1="64" x2="{r}" y2="64" stroke="{RED}" stroke-opacity=".5"/>
{body}
</svg>
'''
    return fit_to_frame(sweep(card_backdrop(name, svg) if name in BACKDROPS else svg))


def para(text, x, y, width_px, size=15, fill=SOFT, lh=24, delay=0.0):
    """Wrap one paragraph into <text> lines; returns (svg, next_y)."""
    cols = int(width_px / (MONO_PX * size / 15))
    out = []
    for i, line in enumerate(textwrap.wrap(text, cols)):
        out.append(f'<text class="mono row" x="{x}" y="{y}" font-size="{size}" fill="{fill}" style="animation-delay:{delay + i*0.05:.2f}s">{escape(line)}</text>')
        y += lh
    return "\n".join(out), y


# 1. Player log (the emoji lines, verbatim)
log = [("CURRENT QUEST", "I'm currently building AI-agent tooling and Android apps under SudarshanTechLabs"),
       ("PARTY INVITE", "I'm open to collaborate on QA automation, AI agents and developer tooling"),
       ("TRAINING", "I'm currently exploring Rust and Three.js"),
       ("ASK ME", "Ask me about test automation, release quality and MCP servers"),
       ("FUN FACT", "13+ years in QA, so I test my own code before it ships")]
rows, y = [], 104
for i, (tag, line) in enumerate(log):
    d = 0.3 + i * 0.25
    rows.append(f'<g class="row" style="animation-delay:{d:.2f}s"><text x="76" y="{y}" class="mono" font-size="13" fill="{RED2}" letter-spacing="2">[{tag}]</text>'
                f'<text x="250" y="{y}" class="mono" font-size="17" fill="{TEXT}">{escape(line)}</text></g>')
    y += 40
h = y + 24
log_desc = "Player log: currently building AI-agent tooling and Android apps; open to collaborate on QA automation, AI agents and developer tooling; exploring Rust and Three.js; ask about test automation, release quality and MCP servers; 13+ years in QA."
cards.joinpath("log.svg").write_text(frame("log", h, "PLAYER LOG", "5 ENTRIES", "\n".join(rows), log_desc))

# Narrow: the tag above its line, the line wrapped to the panel
inner = NARROW - 2 * (NX - 40)
rows, y = [], 98
for i, (tag, line) in enumerate(log):
    d = 0.3 + i * 0.25
    g = [f'<g class="row" style="animation-delay:{d:.2f}s"><text x="{NX}" y="{y}" class="mono" font-size="12" fill="{RED2}" letter-spacing="2">[{tag}]</text>']
    for ln in textwrap.wrap(line, int(inner / MONO_PX)):
        y += 22
        g.append(f'<text x="{NX}" y="{y}" class="mono" font-size="15" fill="{TEXT}">{escape(ln)}</text>')
    rows.append("".join(g) + "</g>")
    y += 34
cards.joinpath("log-narrow.svg").write_text(frame("log", y + 6, "PLAYER LOG", "", "\n".join(rows), log_desc, pw=NARROW))

# 2. Player profile (About + Background, minus the paragraph that repeated "13+ years")
paras = [
 "I'm Sudarshan Kishor Chaudhari, a Senior Quality Engineer, Test Automation specialist, and AI systems builder based in Bangkok, Thailand. Since 2021 I have worked at ScreenCloud as a Senior Software Automation Test Engineer and Software Developer.",
 "1st Place, World's Best Tester 2026 (Thailand Qualifier): competed solo and scored 116.9 / 130 against 65 teams, advancing to the Global Final. Certified Software Tester (CSTE).",
 "I have 13+ years of experience in software quality engineering, working across SaaS, fintech, gaming, web, mobile, cloud, and digital signage platforms. My background combines hands-on test automation with QA leadership, test strategy, CI/CD, release quality, production investigation, and cross-platform validation.",
 "Alongside my professional QA career, I run SudarshanTechLabs, my independent engineering and product lab where I design, build, test, and ship software across Android, web, AI, cybersecurity, developer tooling, and cross-platform applications.",
 "My work sits at the intersection of quality engineering, automation, AI, and software development. I approach products with a QA mindset from the beginning: understanding failure modes, designing for testability, automating repetitive work, and building release confidence into the engineering process.",
 "Through SudarshanTechLabs, I also build products and tools from idea to production, covering architecture, development, testing, CI/CD, release automation, monitoring, and ongoing maintenance."]
parts, y = [f'<text x="76" y="110" class="sans" font-size="28" font-weight="900" fill="{TEXT}" letter-spacing="2" filter="url(#glow)">SUDARSHAN KISHOR CHAUDHARI</text>',
            f'<text x="76" y="138" class="mono" font-size="14" fill="{RED2}" letter-spacing="3">SENIOR QUALITY ENGINEER · TEST AUTOMATION · AI SYSTEMS · BANGKOK</text>'], 178
for i, ptxt in enumerate(paras):
    s, y = para(ptxt, 76, y, 1128, delay=0.3 + i * 0.2)
    parts.append(s); y += 12
h = y + 14
cards.joinpath("profile.svg").write_text(frame("profile", h, "PLAYER PROFILE", "CLASS: QUALITY ENGINEER", "\n".join(parts),
    "Player profile: " + " ".join(paras)))

parts, y = [f'<text x="{NX}" y="104" class="sans" font-size="20" font-weight="900" fill="{TEXT}" letter-spacing="1" filter="url(#glow)">SUDARSHAN KISHOR</text>',
            f'<text x="{NX}" y="130" class="sans" font-size="20" font-weight="900" fill="{TEXT}" letter-spacing="1" filter="url(#glow)">CHAUDHARI</text>'], 156
for ln in ("SENIOR QUALITY ENGINEER", "TEST AUTOMATION · AI SYSTEMS · BANGKOK"):
    parts.append(f'<text x="{NX}" y="{y}" class="mono" font-size="12" fill="{RED2}" letter-spacing="2">{ln}</text>')
    y += 20
y += 16
for i, ptxt in enumerate(paras):
    s, y = para(ptxt, NX, y, inner, lh=22, delay=0.3 + i * 0.2)
    parts.append(s); y += 12
cards.joinpath("profile-narrow.svg").write_text(frame("profile", y + 14, "PLAYER PROFILE", "", "\n".join(parts),
    "Player profile: " + " ".join(paras), pw=NARROW))

# 3. Dungeon record (no counters: the Repositories card carries the live counts)
record = ("Projects across Android, iOS, macOS, web, Rust, AI systems, QA, cybersecurity, and developer tooling.",
          "The public repositories provide reviewable examples. The private portfolio includes production applications, internal automation, experiments, and category catalogs maintained under SudarshanTechLabs.")
record_desc = "Dungeon record: projects across Android, iOS, macOS, web, Rust, AI systems, QA, cybersecurity and developer tooling; the public repositories provide reviewable examples, and the private portfolio includes production applications, internal automation, experiments and category catalogs maintained under SudarshanTechLabs."
for pw, x, width, y0, fname in ((WIDE, 76, 1128, 104, "record.svg"), (NARROW, NX, inner, 100, "record-narrow.svg")):
    lh = 24 if pw == WIDE else 22
    s1, y = para(record[0], x, y0, width, fill=TEXT, lh=lh, delay=0.3)
    s2, y = para(record[1], x, y + 10, width, fill=MUTED, lh=lh, delay=0.5)
    cards.joinpath(fname).write_text(add_embers(frame("record", y + 14, "DUNGEON RECORD", "CURRENT FOOTPRINT", s1 + "\n" + s2, record_desc, pw=pw)))

# 4. System message: six dev and QA quotes, one every 5 s
quotes = [("Program testing can be used to show the presence of bugs, but never to show their absence.", "Edsger W. Dijkstra"),
          ("First, solve the problem. Then, write the code.", "John Johnson"),
          ("Quality is never an accident; it is always the result of intelligent effort.", "John Ruskin"),
          ("Make it work, make it right, make it fast.", "Kent Beck"),
          ("Talk is cheap. Show me the code.", "Linus Torvalds"),
          ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra")]
n, per = len(quotes), 5
span = 100 / n
css = (f".q{{opacity:0;animation:q {n*per}s infinite}}\n"
       f"@keyframes q{{0%{{opacity:0;transform:translateY(8px)}}{span*0.08:.2f}%,{span*0.88:.2f}%{{opacity:1;transform:translateY(0)}}{span:.2f}%,100%{{opacity:0;transform:translateY(-6px)}}}}\n"
       ".tick{animation:tick 1s steps(1) infinite}@keyframes tick{50%{opacity:0}}\n")
quote_desc = "System message cycling six quotes: " + " ".join(f"“{q}” — {w}." for q, w in quotes)
# wide: 58 columns of 26px text, centred; narrow: 24 columns of 20px, up to five lines
for pw, x0, cx, cols, size, lh, h, fname in ((WIDE, 76, 640, 58, 26, 38, 300, "quote.svg"),
                                              (NARROW, NX, 280, 24, 20, 28, 330, "quote-narrow.svg")):
    parts = [f'<text x="{x0}" y="104" class="mono" font-size="14" fill="{RED2}" letter-spacing="3">[ SYSTEM MESSAGE ]</text>',
             f'<rect class="tick" x="{x0 + 174}" y="91" width="9" height="16" fill="{RED2}"/>']
    for i, (q, who) in enumerate(quotes):
        lines = textwrap.wrap(q, cols)
        g = [f'<g class="q" style="animation-delay:{i*per}s">']
        yy = (160 if len(lines) == 1 else 146) if pw == WIDE else 206 - len(lines) * lh // 2
        for ln in lines:
            g.append(f'<text x="{cx}" y="{yy}" class="sans" font-size="{size}" font-weight="700" fill="{TEXT}" text-anchor="middle" filter="url(#glow)">{escape(ln)}</text>')
            yy += lh
        g.append(f'<text x="{cx}" y="{yy+14}" class="mono" font-size="{16 if pw == WIDE else 14}" fill="{RED2}" text-anchor="middle" letter-spacing="2">— {escape(who)}</text></g>')
        parts.append("".join(g))
    cards.joinpath(fname).write_text(add_embers(frame("quote", h, "SYSTEM", f"{n} MESSAGES · CYCLING", "\n".join(parts), quote_desc, css, pw=pw)))
print("built log, profile, record, quote")

# 5. Phone versions of the hand-made cards (hero, quest, skills, status, join). The wide cards have no
# build script, so their text is kept in step here. Pictures are read from the wide SVGs, except
# join's backdrop, which is fx.JOIN_IMAGE.
# To keep phones light, the decorative Igris flipbook (its first frame stays as the backdrop) and the
# skills side art are left out.


def pictures(card, pattern):
    """The data: URIs of every <image> in assets/cards/<card>.svg whose tag matches pattern."""
    svg = (cards / f"{card}.svg").read_text()
    uris = [m.group(1) for m in re.finditer(r'<image\b[^>]*?' + pattern + r'[^>]*?href="(data:[^"]+)"', svg)]
    if not uris:
        sys.exit(f"build_text_cards.py: no picture matching {pattern!r} in {card}.svg")
    return uris


ROW_CSS = ".fade{opacity:0;animation:fade .8s ease forwards}@keyframes fade{to{opacity:1}}\n"

# Hero: the awakening line, the portrait with ARISE, the name, the cycling title, three chips
hero_bg = pictures("hero", r'x="0" y="0" width="1280"')[0]
portrait = pictures("hero", r'x="958" y="92"')  # base picture first, then the flipbook frames
cx, py = 40 + NARROW // 2, 116
titles = ["Senior Quality Engineer", "Test Automation Specialist", "AI Systems Builder", "Android Developer"]
body = [f'<text x="{NX}" y="100" class="mono row" font-size="15" fill="{PINK}" style="animation-delay:.2s">A new Player has awakened.</text>',
        '<defs><linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff1f2"/><stop offset=".5" stop-color="#ff6b7d"/>'
        '<stop offset="1" stop-color="#ff8a3d"/></linearGradient>'
        f'<clipPath id="charclip"><rect x="{cx - 100}" y="{py + 4}" width="200" height="200" rx="6"/></clipPath>'
        '<linearGradient id="charfade" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#0d0204" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#0d0204" stop-opacity=".95"/></linearGradient></defs>',
        f'<g class="fade" style="animation-delay:.4s"><rect x="{cx - 104}" y="{py}" width="208" height="208" rx="8" fill="#0d0204"/>'
        f'<g clip-path="url(#charclip)"><image x="{cx - 100}" y="{py + 4}" width="200" height="200" preserveAspectRatio="xMidYMid slice" href="{portrait[0]}"/>']
for i, uri in enumerate(portrait[1:]):
    body.append(f'<image class="fr" x="{cx - 100}" y="{py + 4}" width="200" height="200" preserveAspectRatio="xMidYMid slice" style="animation-delay:{i * 0.1:.2f}s" href="{uri}"/>')
body.append(f'</g><rect x="{cx - 100}" y="{py + 4}" width="200" height="200" rx="6" fill="url(#charfade)"/>'
            f'<rect class="frame" x="{cx - 104}" y="{py}" width="208" height="208" rx="8" filter="url(#glow)"/>'
            f'<text x="{cx}" y="{py + 190}" class="sans arise" font-size="28" font-weight="900" fill="#ffd0b5" text-anchor="middle" letter-spacing="7" filter="url(#glow)">ARISE</text></g>')
y = py + 252
for word in ("SUDARSHAN", "CHAUDHARI"):
    body.append(f'<text x="{NX}" y="{y}" class="sans fade" font-size="34" font-weight="900" fill="url(#name)" letter-spacing="2" filter="url(#glow)" style="animation-delay:1s">{word}</text>')
    y += 40
body.append(f'<text x="{NX}" y="{y}" class="mono" font-size="16" fill="{MUTED}">TITLE ›</text>')
body += [f'<text x="{NX + 78}" y="{y}" class="mono title" font-size="16" fill="{TEXT}" style="animation-delay:{i * 3}s">{t}</text>' for i, t in enumerate(titles)]
y += 26
chips = [[("CLASS", "Quality Engineer", 230), ("EXP", "13+ yrs", 134)], [("GUILD", "SudarshanTechLabs", 250)]]
for row in chips:
    x = NX
    for label, value, w in row:
        # dark chip under the red tint, so the label reads over the light parts of the backdrop
        body.append(f'<g class="mono fade" font-size="14" style="animation-delay:1.4s"><rect x="{x}" y="{y}" width="{w}" height="36" rx="4" fill="#140306" fill-opacity=".82"/>'
                    f'<rect x="{x}" y="{y}" width="{w}" height="36" rx="4" fill="{RED}" fill-opacity=".08" stroke="{RED}" stroke-opacity=".45"/>'
                    f'<text x="{x + 14}" y="{y + 23}" fill="{MUTED}">{label} <tspan fill="{TEXT}">{escape(value)}</tspan></text></g>')
        x += w + 14
    y += 48
for ln in ("Bangkok, TH · Android · QA Automation", "AI Agents · Developer Tooling"):
    y += 6
    body.append(f'<text x="{NX}" y="{y + 10}" class="mono fade" font-size="14" fill="{MUTED}" style="animation-delay:1.8s">{ln}</text>')
    y += 16
hero_css = (ROW_CSS + ".title{opacity:0;animation:cycle 12s infinite}@keyframes cycle{0%{opacity:0}3%,22%{opacity:1}25%,100%{opacity:0}}\n"
            ".arise{animation:arise 2.4s ease-in-out infinite}@keyframes arise{0%,100%{opacity:.55}50%{opacity:1}}\n"
            ".fr{opacity:0;animation:fr 1.90s step-end infinite}@keyframes fr{0%{opacity:1}5.263%,100%{opacity:0}}\n")
hero_desc = "System window: a new player has awakened — Sudarshan Chaudhari, Senior Quality Engineer, Test Automation Specialist, AI Systems Builder, Android Developer."
cards.joinpath("hero-narrow.svg").write_text(
    backdrop(frame("hero", y + 44, "SYSTEM", "NOTIFICATION", "\n".join(body), hero_desc, hero_css, pw=NARROW), hero_bg, opacity=0.4))

# Quest: the four goals, each ticking to complete, and the warning
goals = ["Android products — Kotlin · Jetpack Compose · MVVM · Clean Architecture",
         "AI-agent memory, orchestration, evaluation and repo intelligence",
         "QA, security, release and developer-productivity tooling",
         "Local-first utilities that keep developers in control of their data"]
body = [f'<text x="{cx}" y="{98 + i * 26}" class="sans" font-size="18" font-weight="800" fill="{TEXT}" text-anchor="middle" letter-spacing="1" filter="url(#glow)">{escape(t)}</text>'
        for i, t in enumerate(("[DAILY QUEST: BUILD & SHIP]", "HAS ARRIVED"))]
body.append(f'<text x="{NX}" y="154" class="mono" font-size="13" fill="{MUTED}" letter-spacing="2">GOALS</text>')
y = 172
for i, goal in enumerate(goals):
    d = 0.4 + i * 0.4
    g = [f'<g class="row" style="animation-delay:{d:.1f}s"><rect x="{NX}" y="{y}" width="20" height="20" rx="3" fill="none" stroke="{RED}"/>'
         f'<path class="tick" d="M{NX + 4} {y + 10}l5 5 9-11" fill="none" stroke="{RED2}" stroke-width="3" style="animation-delay:{d + 0.6:.1f}s"/>']
    lines = textwrap.wrap(goal.replace(" · ", "\u00a0· "), int((inner - 34) / MONO_PX))  # no-break space: a line never starts with ·
    for j, ln in enumerate(lines):
        g.append(f'<text x="{NX + 34}" y="{y + 15 + j * 22}" class="mono" font-size="15" fill="{TEXT}">{escape(ln)}</text>')
    y += 15 + (len(lines) - 1) * 22 + 22
    g.append(f'<text x="{40 + NARROW - 16}" y="{y}" class="mono done" font-size="13" fill="{RED2}" text-anchor="end" style="animation-delay:{d + 0.9:.1f}s">[COMPLETE]</text></g>')
    body.append("".join(g))
    y += 16
for ln in ("WARNING: Shipping without tests will", "result in an appropriate penalty."):
    y += 20
    body.append(f'<text x="{cx}" y="{y}" class="mono warn" font-size="13" fill="#ffb020" text-anchor="middle">{ln}</text>')
quest_css = (".tick{stroke-dasharray:30;stroke-dashoffset:30;animation:tick .4s ease forwards}@keyframes tick{to{stroke-dashoffset:0}}\n"
             ".done{opacity:0;animation:in .3s ease forwards}\n.warn{animation:warn 2s ease-in-out infinite}@keyframes warn{0%,100%{opacity:.6}50%{opacity:1}}\n")
quest_desc = "Daily quest: Android products, AI-agent systems, QA and release tooling, local-first utilities."
cards.joinpath("quest-narrow.svg").write_text(
    backdrop(frame("quest", y + 38, "QUEST INFO", "", "\n".join(body), quest_desc, quest_css, pw=NARROW),
             pictures("quest", r'class="side"')[0], opacity=0.3))

# Skills: the six skill trees, one per row
trees = [("QA AUTOMATION", "End-to-end, API and device testing", "Release gates · risk-based QA"),
         ("MOBILE", "Android apps on Google Play", "Automated build and publish"),
         ("AI SYSTEMS", "Multi-agent orchestration", "MCP servers · agent memory"),
         ("WEB PLATFORMS", "Full-stack apps and REST APIs", "Edge-hosted, local-first tools"),
         ("DEVTOOLS", "CLIs and multi-repo tooling", "Release and build automation"),
         ("SECURITY", "Auditing and threat detection", "Log analysis · observability")]
body, y = [], 84
for i, (name, line1, line2) in enumerate(trees):
    body.append(f'<g class="chip" style="animation-delay:{0.35 + i * 0.3:.2f}s"><rect x="{NX}" y="{y}" width="{inner}" height="104" rx="5"/>'
                f'<text x="{NX + 16}" y="{y + 24}" class="mono tag">SKILL TREE {i + 1:02d}</text>'
                f'<text x="{NX + 16}" y="{y + 52}" class="sans" font-size="18" font-weight="900" letter-spacing="1">{name}</text>'
                f'<text x="{NX + 16}" y="{y + 74}" class="mono" font-size="14" fill="{SOFT}">{escape(line1)}</text>'
                f'<text x="{NX + 16}" y="{y + 94}" class="mono" font-size="14" fill="{MUTED}">{escape(line2)}</text></g>')
    y += 116
skills_css = (".chip{opacity:.15;animation:unlock .35s ease forwards}@keyframes unlock{to{opacity:1}}\n"
              f".chip rect{{fill:{RED};fill-opacity:.08;stroke:{RED};stroke-opacity:.6}}.chip text{{fill:{TEXT}}}"
              f".chip .tag{{fill:{RED2};font-size:11px;letter-spacing:2px}}\n")
cards.joinpath("skills-narrow.svg").write_text(frame("skills", y + 22, "SKILLS", "6 / 6 SKILL TREES UNLOCKED", "\n".join(body),
    "Skills window: six skill areas — QA automation, mobile, AI systems, web platforms, developer tooling, security.", skills_css, pw=NARROW))

# Status: the ID card, the seven abilities, public repositories by language
abilities = ["⚙ Quality Engineering & Test Automation", "◈ AI Systems & Automation", "▣ Mobile & Cross-Platform Applications",
             "◎ Web Applications & Platforms", "⌘ Developer Tooling & CLI Engineering", "◆ Cybersecurity & Observability",
             "▤ Digital Signage & Device Platforms"]
langs = [("HTML", 44, RED), ("TypeScript", 42, "#b3122e"), ("Python", 34, "#ff8a3d"), ("JavaScript", 23, RED2),
         ("CSS", 11, "#7a1424"), ("Rust", 8, PINK), ("Shell", 5, RED)]
photo = pictures("status", r'clip-path="url\(#photo\)"')[0]
ix = cx - 150  # ID card, 300 wide, centred
body = ['<defs><linearGradient id="card" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0a10"/><stop offset="1" stop-color="#12040a"/></linearGradient>'
        '<linearGradient id="rank" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff8a3d"/><stop offset="1" stop-color="#ff6b7d"/></linearGradient>'
        f'<clipPath id="photo"><circle cx="{cx}" cy="186" r="46"/></clipPath></defs>',
        f'<line x1="{cx}" y1="64" x2="{cx}" y2="90" stroke="{RED}" stroke-width="2"/>',
        f'<g class="swing"><rect x="{cx - 20}" y="82" width="40" height="14" rx="3" fill="{RED}" fill-opacity=".5"/>'
        f'<rect x="{ix}" y="94" width="300" height="300" rx="10" fill="url(#card)" stroke="{RED}" stroke-width="2" filter="url(#glow)"/>'
        f'<text x="{cx}" y="126" class="mono" font-size="12" fill="{RED2}" text-anchor="middle" letter-spacing="4">HUNTER ASSOCIATION</text>'
        f'<image x="{cx - 46}" y="140" width="92" height="92" clip-path="url(#photo)" preserveAspectRatio="xMidYMid slice" href="{photo}"/>'
        f'<circle cx="{cx}" cy="186" r="46" fill="none" stroke="url(#rank)" stroke-width="3"/>'
        f'<circle cx="{cx + 42}" cy="222" r="16" fill="#0d0204" stroke="url(#rank)" stroke-width="2"/>'
        f'<text x="{cx + 42}" y="229" class="sans" font-size="19" font-weight="900" fill="url(#rank)" text-anchor="middle">S</text>'
        f'<text x="{cx}" y="258" class="sans" font-size="21" font-weight="800" fill="{TEXT}" text-anchor="middle">SUDARSHAN</text>'
        f'<text x="{cx}" y="283" class="sans" font-size="21" font-weight="800" fill="{TEXT}" text-anchor="middle">CHAUDHARI</text>'
        + "".join(f'<text x="{ix + 22}" y="{316 + i * 22}" class="mono" font-size="13" fill="{MUTED}">{k}</text>'
                  f'<text x="{ix + 278}" y="{316 + i * 22}" class="mono" font-size="13" fill="{TEXT}" text-anchor="end">{v}</text>'
                  for i, (k, v) in enumerate((("JOB", "Quality Engineer"), ("GUILD", "SudarshanTechLabs"), ("BASE", "Bangkok, Thailand"), ("EXP", "13+ years"))))
        + '</g>',
        f'<text x="{NX}" y="432" class="mono" font-size="13" fill="{MUTED}" letter-spacing="2">ABILITIES</text>',
        f'<text x="{NX + inner}" y="432" class="mono" font-size="11" fill="#ff8a9b" text-anchor="end" letter-spacing="2">SHADOW SOLDIER · IGRIS</text>']
y = 462
for i, a in enumerate(abilities):
    body.append(f'<g class="row" style="animation-delay:{0.3 + i * 0.2:.1f}s"><text x="{NX}" y="{y}" class="mono" font-size="15" fill="{TEXT}">{escape(a)}</text>'
                f'<rect class="bar" x="{NX}" y="{y + 9}" width="{inner}" height="3" fill="{"#ff8a3d" if i == 6 else RED}" style="animation-delay:{0.5 + i * 0.2:.1f}s"/></g>')
    y += 38
y += 14
body.append(f'<line x1="40" y1="{y - 22}" x2="{40 + NARROW}" y2="{y - 22}" stroke="{RED}" stroke-opacity=".35"/>'
            f'<text x="{NX}" y="{y + 4}" class="mono" font-size="13" fill="{MUTED}" letter-spacing="2">PUBLIC REPOSITORIES BY LANGUAGE</text>'
            f'<text x="{NX}" y="{y + 24}" class="mono" font-size="11" fill="#7a5a60" letter-spacing="1">snapshot 2026-11-12 · live counts on the Repositories card</text>')
y += 52
bar_w = inner - 150
for i, (lang, count, colour) in enumerate(langs):
    w = round(bar_w * count / langs[0][1])
    body.append(f'<text x="{NX}" y="{y + 11}" class="mono" font-size="14" fill="{TEXT}">{lang}</text>'
                f'<rect x="{NX + 110}" y="{y}" width="{bar_w}" height="12" rx="3" fill="{RED}" fill-opacity=".07"/>'
                f'<rect class="bar" x="{NX + 110}" y="{y}" width="{w}" height="12" rx="3" fill="{colour}" style="animation-delay:{0.3 + i * 0.12:.2f}s"/>'
                f'<text x="{NX + inner}" y="{y + 11}" class="mono" font-size="14" fill="{RED2}" text-anchor="end">{count}</text>')
    y += 28
status_css = (f".swing{{transform-origin:{cx}px 70px;animation:swing 4s ease-in-out infinite}}"
              "@keyframes swing{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(2.5deg)}}\n"
              ".bar{transform-origin:left;transform:scaleX(0);transform-box:fill-box;animation:fill 1.2s ease forwards}@keyframes fill{to{transform:scaleX(1)}}\n")
cards.joinpath("status-narrow.svg").write_text(
    backdrop(frame("status", y + 22, "STATUS", "", "\n".join(body),
                   "Status window: player ID card, seven abilities and public repositories by language.", status_css, pw=NARROW),
             pictures("status", r'x="450" y="66"')[0], opacity=0.22))

# Join: the invitation, its two lines of text and the YES / NO buttons, over the shadow army
lines = [(100, "mono fade", 15, PINK, ".3s", "You have received an invitation."),
         (150, "sans fade", 28, TEXT, ".7s", "JOIN THE"), (184, "sans fade", 28, TEXT, ".7s", "SHADOW ARMY?"),
         (228, "mono fade", 14, MUTED, "1s", "Collaborate · Hire · Talk QA, Android or AI agents")]
heading = ' font-weight="900" letter-spacing="3" filter="url(#glow)"'
body = [f'<text x="{cx}" y="{y}" class="{cls}" font-size="{size}"{heading if cls.startswith("sans") else ""} '
        f'fill="{fill}" text-anchor="middle" style="animation-delay:{d}">{escape(t)}</text>' for y, cls, size, fill, d, t in lines]
body.append(f'<g class="mono" font-size="18" text-anchor="middle">'
            f'<rect class="yes" x="{cx - 140}" y="266" width="128" height="44" rx="4" fill="{RED}" stroke="{RED2}" stroke-width="2"/>'
            f'<text x="{cx - 76}" y="294" fill="{TEXT}" font-weight="700">YES</text>'
            f'<rect x="{cx + 12}" y="266" width="128" height="44" rx="4" fill="{RED}" fill-opacity=".05" stroke="{RED}" stroke-opacity=".4"/>'
            f'<text x="{cx + 76}" y="294" fill="#7a5a60">NO</text></g>')
join_css = ROW_CSS + ".yes{animation:yes 1.6s ease-in-out infinite}@keyframes yes{0%,100%{fill-opacity:.15}50%{fill-opacity:.45}}\n"
cards.joinpath("join-narrow.svg").write_text(
    backdrop(frame("join", 352, "SYSTEM", "", "\n".join(body), "System invitation: join the shadow army — let's connect.", join_css, pw=NARROW),
             data_uri(IMG / (JOIN_IMAGE + ".jpg")), opacity=0.35))
print("built hero, quest, skills, status, join phone versions")
