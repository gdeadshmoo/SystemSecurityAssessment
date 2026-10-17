#!/usr/bin/env python3
"""Build a standalone deck.html from source/deck.json and source/slides/*.html.

The slide files come from a Claude Slides artifact. They use two custom tags
(<x-shape> and <x-icon>) that this script swaps for plain HTML/SVG so the
deck opens in any browser. Images are inlined so deck.html is one file.

Usage: python3 build_deck.py   (writes deck.html next to this script)
"""
import base64
import json
import mimetypes
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"

ICONS = {
    "Settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    "Link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "Lightning": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "Warning": '<path d="M12 3 2 21h20z"/><path d="M12 10v5M12 18v.5"/>',
    "Clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}


def style_of(attrs):
    m = re.search(r'style="([^"]*)"', attrs)
    return m.group(1) if m else ""


def replace_shape(m):
    attrs = m.group(1)
    kind = re.search(r'kind="([^"]*)"', attrs).group(1)
    clip = {
        "arrow-right": "polygon(0 35%,60% 35%,60% 0,100% 50%,60% 100%,60% 65%,0 65%)",
    }.get(kind, "none")
    return f'<div style="flex:none;clip-path:{clip};{style_of(attrs)}"></div>'


def replace_icon(m):
    attrs = m.group(1)
    name = re.search(r'name="([^"]*)"', attrs).group(1)
    paths = ICONS.get(name, '<circle cx="12" cy="12" r="9"/>')
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" style="{style_of(attrs)}">{paths}</svg>')


def inline_images(html):
    def sub(m):
        path = SRC / m.group(1)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode()
        return f'src="data:{mime};base64,{data}"'
    return re.sub(r'src="(images/[^"]+)"', sub, html)


def main():
    deck = json.loads((SRC / "deck.json").read_text())
    slides = []
    for sid in deck["order"]:
        html = (SRC / "slides" / f"{sid}.html").read_text()
        html = re.sub(r"<x-shape([^>]*)></x-shape>", replace_shape, html)
        html = re.sub(r"<x-icon([^>]*)></x-icon>", replace_icon, html)
        slides.append(inline_images(html))
    fonts = "\n".join(f'<link rel="stylesheet" href="{f["href"]}">'
                      for f in deck.get("faces", {}).values() if "href" in f)
    out = TEMPLATE.replace("{{TITLE}}", deck["title"]).replace("{{FONTS}}", fonts)
    out = out.replace("{{SLIDES}}", "\n".join(slides))
    (HERE / "deck.html").write_text(out)
    print(f"wrote deck.html with {len(slides)} slides")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
{{FONTS}}
<style>
  * { margin: 0; box-sizing: border-box; }
  html, body { background: #000; height: 100%; overflow: hidden; }
  ul, ol { padding-left: 1.2em; }
  table { border-collapse: collapse; width: 100%; text-align: left; }
  #stage { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: 0 0; }
  #stage > section { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden; }
  #stage > section:not(.active) { display: none !important; }
  #count { position: fixed; right: 16px; bottom: 12px; font: 14px sans-serif; color: #888; }
  @media print {
    @page { size: 1920px 1080px; margin: 0; }
    html, body { height: auto; overflow: visible; }
    #stage { position: static; transform: none !important; }
    #stage > section { position: relative; break-after: page; }
    #stage > section:not(.active) { display: flex !important; }
    #count { display: none; }
  }
</style>
</head>
<body>
<div id="stage">
{{SLIDES}}
</div>
<div id="count"></div>
<script>
  const slides = [...document.querySelectorAll('#stage > section')];
  const stage = document.getElementById('stage');
  let i = Math.max(0, slides.findIndex(s => '#' + s.id === location.hash));
  function fit() {
    const k = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `scale(${k}) translate(-50%, -50%)`;
  }
  function show(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, j) => s.classList.toggle('active', j === i));
    document.getElementById('count').textContent = `${i + 1} / ${slides.length}`;
    history.replaceState(null, '', '#' + slides[i].id);
  }
  addEventListener('keydown', e => {
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) show(i + 1);
    if (['ArrowLeft', 'PageUp'].includes(e.key)) show(i - 1);
    if (e.key === 'Home') show(0);
    if (e.key === 'End') show(slides.length - 1);
  });
  addEventListener('click', e => show(i + (e.clientX > innerWidth / 3 ? 1 : -1)));
  addEventListener('resize', fit);
  fit(); show(i);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
