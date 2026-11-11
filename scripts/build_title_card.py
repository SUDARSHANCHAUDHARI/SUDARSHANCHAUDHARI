"""Build the animated red Solo Leveling title banner (title.svg).

Usage: python3 scripts/build_title_card.py <red-logo.png> assets/cards/title.svg

The red logo PNG is made from the white-on-black title art with ffmpeg:
    ffmpeg -i solo10.png -vf "crop=1000:120:500:480,scale=1000:-2,colorchannelmixer=rr=1:rg=0:rb=0:gr=0.18:gg=0:gb=0:br=0.30:bg=0:bb=0,format=rgb24" title-red.png
"""
import base64
import pathlib
import sys


def main():
    if len(sys.argv) < 3:
        sys.exit("build_title_card.py: usage: build_title_card.py <red-logo.png> <out.svg>")
    png, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if not png.is_file():
        sys.exit(f"build_title_card.py: no such file: {png}")
    u = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 240" width="1280" height="240" role="img" aria-label="Solo Leveling">
<title>Solo Leveling</title>
<desc>The Solo Leveling title in red on black, with a slow glow pulse and a brief glitch.</desc>
<defs>
<filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff2e4d" stop-opacity="0"/><stop offset=".5" stop-color="#ff2e4d" stop-opacity=".9"/><stop offset="1" stop-color="#ff2e4d" stop-opacity="0"/></linearGradient>
<style>
.logo{{animation:pulse 4s ease-in-out infinite}}
.g{{mix-blend-mode:screen;opacity:0}}
.g1{{animation:g1 5s steps(1) infinite}}
.g2{{animation:g2 5s steps(1) infinite}}
.sweep{{animation:sweep 6s linear infinite}}
@keyframes pulse{{0%,100%{{opacity:.82}}50%{{opacity:1}}}}
@keyframes g1{{0%,90%{{opacity:0;transform:none}}91%{{opacity:.9;transform:translate(-6px,1px)}}93%{{opacity:.9;transform:translate(5px,-2px)}}95%,100%{{opacity:0;transform:none}}}}
@keyframes g2{{0%,91%{{opacity:0;transform:none}}92%{{opacity:.7;transform:translate(7px,0)}}94%{{opacity:.7;transform:translate(-4px,2px)}}96%,100%{{opacity:0;transform:none}}}}
@keyframes sweep{{from{{transform:translateX(-1280px)}}to{{transform:translateX(1280px)}}}}
</style>
</defs>
<rect width="1280" height="240" fill="#050102"/>
<image class="logo" x="140" y="60" width="1000" height="120" filter="url(#glow)" href="{u}"/>
<image class="g g1" x="140" y="60" width="1000" height="120" href="{u}"/>
<image class="g g2" x="140" y="60" width="1000" height="120" href="{u}"/>
<rect class="sweep" x="0" y="188" width="1280" height="2" fill="url(#line)"/>
</svg>
'''
    out.write_text(svg)
    print(f"built {out}")


if __name__ == "__main__":
    main()
