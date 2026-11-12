"""Wrap the README photos and GIFs in SVG frames with the System effect layer.

    python3 scripts/build_image_cards.py

Writes <name>.svg next to each source in assets/img and assets/gifs; the README shows the
SVG and the source stays as the build input. Photos get the slow zoom, red vignette and
embers; GIFs move already, so they get only the frame pulse and the light sweep (a zoom
would blur the pixel art). GLITCH images also get the red ghost jump.
"""
import base64
import pathlib
import struct
import sys

from fx import image_svg

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLITCH = {"red-grin", "arise"}
TEXT = {  # title, description: kept in step with the README alt text
    "red-throne": ("Red throne", "Shadow monarch before a throne of skulls under a red moon"),
    "igris-duel": ("Igris duel", "Jinwoo clashing blades with Igris, the red knight"),
    "red-army": ("Red army", "Shadow soldiers with glowing eyes in red fire"),
    "red-cerberus": ("Red cerberus", "A hooded hunter facing a three-headed hellhound in a sea of fire"),
    "red-gate": ("Red gate", "A red gate swirling open in an abandoned warehouse"),
    "red-grin": ("Red grin", "Grinning statue of God, glowing red"),
    "red-king": ("Red king", "Demon king on his throne before a red army"),
    "arise": ("Arise", "Arise"),
    "mario": ("Pixel coder", "Pixel-art coder at a desk"),
    "deadline": ("Deadline", "Grim reaper chasing a coder along a deadline progress bar"),
    "girl": ("Lo-fi coder", "Lo-fi coder on a balcony at night"),
    "dini": ("Pixel dinosaur", "Pixel dinosaur running"),
}


def dimensions(data, kind):
    if kind == "gif":
        if data[:6] not in (b"GIF87a", b"GIF89a"):
            raise ValueError("not a GIF")
        return struct.unpack("<HH", data[6:10])
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG")
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            raise ValueError(f"bad JPEG marker at byte {i}")
        marker, seg = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):  # start of frame
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + seg
    raise ValueError("no JPEG frame header")


def main():
    sources = sorted((ROOT / "assets/img").glob("*.jpg")) + sorted((ROOT / "assets/gifs").glob("*.gif"))
    missing = [p.stem for p in sources if p.stem not in TEXT]
    if missing:
        sys.exit("build_image_cards.py: no title/description for: " + ", ".join(missing))
    for src in sources:
        kind = "gif" if src.suffix == ".gif" else "jpeg"
        try:
            data = src.read_bytes()
            w, h = dimensions(data, kind)
        except (OSError, ValueError, struct.error) as e:
            sys.exit(f"build_image_cards.py: {src}: {e}")
        uri = f"data:image/{kind};base64," + base64.b64encode(data).decode()
        title, desc = TEXT[src.stem]
        svg = image_svg(uri, w, h, title, desc, photo=kind == "jpeg", glitch=src.stem in GLITCH)
        out = src.with_suffix(".svg")
        try:
            out.write_text(svg)
        except OSError as e:
            sys.exit(f"build_image_cards.py: cannot write {out}: {e}")
        print(f"  {out.relative_to(ROOT)}  {w}x{h}  {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
