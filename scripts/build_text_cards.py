"""Build the four text cards (player log, profile, record, quote) in the red/black System style.

Usage: python3 scripts/build_text_cards.py assets/cards
Reads the embedded @font-face block from hero.svg so every card carries the same fonts.
"""
import sys, re, textwrap, pathlib
from xml.sax.saxutils import escape

cards = pathlib.Path(sys.argv[1])
fonts = re.search(r"@font-face\{font-family:'SLOrb'.*?\n", cards.joinpath("hero.svg").read_text(), re.S).group(0)

RED, RED2, PINK, MUTED, TEXT, SOFT = "#ff2e4d", "#ff6b7d", "#ffb3bc", "#a8828a", "#fff1f2", "#e8c9cd"
MONO_PX = 8.1  # Share Tech Mono advance at 15px


def frame(name, h, label, right, body, desc, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 {h}" width="1280" height="{h}" role="img" aria-label="{escape(desc)}">
<title>{escape(label.title())}</title>
<desc>{escape(desc)}</desc>
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a0508" stop-opacity=".96"/><stop offset="1" stop-color="#0d0204" stop-opacity=".96"/></linearGradient>
<radialGradient id="ember" cx=".85" cy=".2" r=".6"><stop offset="0" stop-color="#8b0000" stop-opacity=".35"/><stop offset="1" stop-color="#8b0000" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
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
<rect width="1280" height="{h}" fill="#050102"/>
<rect x="40" y="20" width="1200" height="{h-40}" rx="6" fill="url(#panel)"/>
<rect x="40" y="20" width="1200" height="{h-40}" rx="6" fill="url(#ember)"/>
<rect class="scan" x="42" y="66" width="1196" height="2" fill="{RED2}" opacity=".12"/>
<rect class="frame" x="40" y="20" width="1200" height="{h-40}" rx="6" filter="url(#glow)"/>
<path class="corner" d="M40 52V20h32M1208 20h32v32M1240 {h-52}v32h-32M72 {h-20}H40v-32"/>
<rect x="40" y="20" width="1200" height="44" fill="{RED}" fill-opacity=".08"/>
<text x="76" y="49" class="mono" font-size="16" fill="{RED2}" letter-spacing="3">⟨ {escape(label)} ⟩</text>
<text x="1204" y="49" class="mono" font-size="14" fill="{MUTED}" text-anchor="end" letter-spacing="2">{escape(right)}</text>
<line x1="40" y1="64" x2="1240" y2="64" stroke="{RED}" stroke-opacity=".5"/>
{body}
</svg>
'''


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
cards.joinpath("log.svg").write_text(frame("log", h, "PLAYER LOG", "5 ENTRIES", "\n".join(rows),
    "Player log: currently building AI-agent tooling and Android apps; open to collaborate on QA automation, AI agents and developer tooling; exploring Rust and Three.js; ask about test automation, release quality and MCP servers; 13+ years in QA."))

# 2. Player profile (About + Background, verbatim)
paras = [
 "I'm Sudarshan Kishor Chaudhari, a Senior Quality Engineer, Test Automation specialist, and AI systems builder based in Bangkok, Thailand.",
 "I have 13+ years of experience in software quality engineering, working across SaaS, fintech, gaming, web, mobile, cloud, and digital signage platforms. My background combines hands-on test automation with QA leadership, test strategy, CI/CD, release quality, production investigation, and cross-platform validation.",
 "Alongside my professional QA career, I run SudarshanTechLabs, my independent engineering and product lab where I design, build, test, and ship software across Android, web, AI, cybersecurity, developer tooling, and cross-platform applications.",
 "I bring more than 13 years of software-testing and engineering experience to product development. That QA foundation shapes how I build: observable behavior, explicit failure handling, repeatable verification, privacy-aware design, and release discipline are part of the product—not afterthoughts.",
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

# 3. Dungeon record (Current footprint, verbatim numbers from the README)
stats = [("411", "REPOSITORIES"), ("172", "PUBLIC"), ("239", "PRIVATE"), ("1", "FORK")]
parts = []
for i, (num, lab) in enumerate(stats):
    x = 76 + i * 290
    parts.append(f'<g class="row" style="animation-delay:{0.3+i*0.15:.2f}s"><rect x="{x}" y="88" width="266" height="110" rx="5" fill="{RED}" fill-opacity=".07" stroke="{RED}" stroke-opacity=".55"/>'
                 f'<text x="{x+133}" y="152" class="sans" font-size="46" font-weight="900" fill="{TEXT}" text-anchor="middle" filter="url(#glow)">{num}</text>'
                 f'<text x="{x+133}" y="182" class="mono" font-size="13" fill="{RED2}" text-anchor="middle" letter-spacing="3">{lab}</text></g>')
s1, y = para("Projects across Android, iOS, macOS, web, Rust, AI systems, QA, cybersecurity, and developer tooling.", 76, 236, 1128, fill=TEXT, delay=1.0)
s2, y = para("The public repositories provide reviewable examples. The private portfolio includes production applications, internal automation, experiments, and category catalogs maintained under SudarshanTechLabs.", 76, y + 10, 1128, fill=MUTED, delay=1.2)
h = y + 14
cards.joinpath("record.svg").write_text(frame("record", h, "DUNGEON RECORD", "CURRENT FOOTPRINT", "\n".join(parts) + "\n" + s1 + "\n" + s2,
    "Dungeon record: 411 repositories, 172 public and 239 private, 1 fork; projects across Android, iOS, macOS, web, Rust, AI systems, QA, cybersecurity and developer tooling."))

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
parts = [f'<text x="76" y="104" class="mono" font-size="14" fill="{RED2}" letter-spacing="3">[ SYSTEM MESSAGE ]</text>',
         f'<rect class="tick" x="250" y="91" width="9" height="16" fill="{RED2}"/>']
for i, (q, who) in enumerate(quotes):
    lines = textwrap.wrap(q, 58)
    g = [f'<g class="q" style="animation-delay:{i*per}s">']
    yy = 160 if len(lines) == 1 else 146
    for ln in lines:
        g.append(f'<text x="640" y="{yy}" class="sans" font-size="26" font-weight="700" fill="{TEXT}" text-anchor="middle" filter="url(#glow)">{escape(ln)}</text>')
        yy += 38
    g.append(f'<text x="640" y="{yy+14}" class="mono" font-size="16" fill="{RED2}" text-anchor="middle" letter-spacing="2">— {escape(who)}</text></g>')
    parts.append("".join(g))
cards.joinpath("quote.svg").write_text(frame("quote", 300, "SYSTEM", f"{n} MESSAGES · CYCLING", "\n".join(parts),
    "System message cycling six quotes: " + " ".join(f"“{q}” — {w}." for q, w in quotes), css))
print("built log, profile, record, quote")
