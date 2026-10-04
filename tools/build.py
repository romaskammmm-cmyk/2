#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка HTML-конспекта из markdown-файла konspekt/konspekt.md.

Возможности:
  * [tt:Ч:ММ:СС] -> кликабельная ссылка на таймкод YouTube
  * картинки -> <figure> с подписью (из alt)
  * боковое оглавление, прогресс-бар, кнопка «наверх», печать/PDF-стили
"""
from __future__ import annotations

import base64
import io
import pathlib
import re
import sys

import markdown
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "konspekt" / "konspekt.md"
OUT = ROOT / "konspekt" / "index.html"
VIDEO_ID = "s4d9DKnlCpE"


def timecode_to_seconds(tc: str) -> int:
    parts = [int(p) for p in tc.split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def replace_timecodes(text: str) -> str:
    def sub(m: re.Match) -> str:
        tc = m.group(1)
        sec = timecode_to_seconds(tc)
        return (
            f'<a class="tt" target="_blank" rel="noopener" '
            f'href="https://www.youtube.com/watch?v={VIDEO_ID}&amp;t={sec}s" '
            f'title="Смотреть в видео">▶&nbsp;{tc}</a>'
        )

    return re.sub(r"\[tt:([0-9:]+)\]", sub, text)


def image_to_data_uri(path: pathlib.Path, max_width: int = 900, quality: int = 82) -> str:
    """Сжимает картинку и возвращает data:URI, чтобы HTML был самодостаточным."""
    im = Image.open(path).convert("RGB")
    if im.width > max_width:
        h = round(im.height * max_width / im.width)
        im = im.resize((max_width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def replace_images(text: str) -> str:
    """![Подпись](img/xx.jpg) -> <figure> с картинкой (base64) и подписью из alt."""

    def sub(m: re.Match) -> str:
        alt, src = m.group(1), m.group(2)
        caption = f"<figcaption>{alt}</figcaption>" if alt.strip() else ""
        uri = src
        local = SRC.parent / src
        if not src.startswith(("http://", "https://", "data:")) and local.exists():
            uri = image_to_data_uri(local)
        return (
            f'<figure class="pic"><img src="{uri}" alt="{alt}" loading="lazy" '
            f'onclick="zoom(this)">{caption}</figure>'
        )

    return re.sub(r"!\[(.*?)\]\((.*?)\)", sub, text)


def build() -> None:
    text = SRC.read_text(encoding="utf-8")
    text = replace_timecodes(text)
    text = replace_images(text)

    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists", "md_in_html", "attr_list", "nl2br"],
        extension_configs={"toc": {"toc_depth": "2-3", "anchorlink": False}},
    )
    body = md.convert(text)
    toc = md.toc

    title = "Вся химия с нуля до ЕГЭ за 12 часов"
    html = TEMPLATE.format(title=title, body=body, toc=toc)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK: {OUT} ({len(html) / 1024:.0f} KB)")


TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — конспект марафона</title>
<style>
:root {{
  --bg: #f6f7fb;
  --card: #ffffff;
  --ink: #1d2333;
  --muted: #5b6479;
  --line: #e4e7f0;
  --accent: #0f8a8a;
  --accent2: #4b4bd6;
  --warn: #b3560b;
  --good: #177245;
  --code: #eef1f8;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0; background: var(--bg); color: var(--ink);
  font: 17px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}}
#progress {{ position: fixed; top: 0; left: 0; height: 3px; width: 0; background: linear-gradient(90deg, var(--accent), var(--accent2)); z-index: 50; }}
.layout {{ display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 28px; max-width: 1400px; margin: 0 auto; padding: 0 22px; }}
/* ---------- sidebar ---------- */
aside {{
  position: sticky; top: 0; align-self: start; height: 100vh; overflow-y: auto;
  padding: 26px 10px 40px 0; font-size: 14.5px;
}}
aside .brand {{ font-weight: 800; font-size: 16px; line-height: 1.3; margin-bottom: 4px; }}
aside .brand small {{ display: block; font-weight: 500; color: var(--muted); font-size: 12.5px; margin-top: 4px; }}
aside .meta {{ color: var(--muted); font-size: 12.5px; margin: 10px 0 16px; }}
aside a {{ color: var(--muted); }}
aside ul {{ list-style: none; margin: 0; padding-left: 0; }}
aside ul ul {{ padding-left: 14px; }}
aside li {{ margin: 1px 0; }}
aside a.nav {{ display: block; padding: 4px 8px; border-radius: 7px; text-decoration: none; border-left: 3px solid transparent; }}
aside a.nav:hover {{ background: #eceffa; color: var(--ink); }}
aside a.nav.active {{ background: #e6f4f4; color: #0b6b6b; border-left-color: var(--accent); font-weight: 600; }}
aside .navtop {{ font-weight: 700; color: var(--ink); }}
.sidebtns {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 14px; }}
.sidebtns a, .sidebtns button {{
  font-size: 12.5px; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--line);
  background: #fff; color: var(--muted); cursor: pointer; text-decoration: none;
}}
.sidebtns a:hover, .sidebtns button:hover {{ border-color: var(--accent); color: var(--accent); }}
/* ---------- main ---------- */
main {{ padding: 26px 0 90px; min-width: 0; }}
main > h1 {{ font-size: 34px; line-height: 1.2; margin: 6px 0 10px; letter-spacing: -.4px; }}
main > h1 + p {{ color: var(--muted); }}
h2 {{
  font-size: 26px; margin: 54px 0 14px; padding: 12px 16px; background: var(--card);
  border-radius: 14px; border: 1px solid var(--line); box-shadow: 0 1px 2px rgba(20,30,60,.04);
  scroll-margin-top: 18px;
}}
h3 {{ font-size: 20px; margin: 30px 0 10px; scroll-margin-top: 18px; }}
h4 {{ font-size: 17.5px; margin: 22px 0 8px; }}
p, ul, ol, table, figure, blockquote, pre {{ margin: 12px 0; }}
a {{ color: var(--accent2); }}
ul, ol {{ padding-left: 24px; }}
li {{ margin: 4px 0; }}
strong {{ color: #101528; }}
code {{ background: var(--code); padding: 2px 6px; border-radius: 6px; font-size: 90%; }}
hr {{ border: none; border-top: 1px solid var(--line); margin: 44px 0; }}
/* таблицы */
table {{ border-collapse: collapse; width: 100%; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 2px rgba(20,30,60,.05); display: table; }}
th, td {{ border: 1px solid var(--line); padding: 8px 11px; text-align: left; vertical-align: top; }}
th {{ background: #eef1f8; font-size: 15px; }}
td {{ font-size: 15.5px; }}
/* таймкод */
a.tt {{ display: inline-block; font-size: 12.5px; font-weight: 600; color: #0b6b6b; background: #e6f4f4; border: 1px solid #c9e6e6; padding: 1px 8px; border-radius: 999px; text-decoration: none; vertical-align: 2px; margin-left: 8px; white-space: nowrap; }}
a.tt:hover {{ background: #0f8a8a; color: #fff; border-color: #0f8a8a; }}
/* цитаты-выноски */
blockquote {{ margin: 14px 0; padding: 12px 16px; border-radius: 12px; background: #fff; border: 1px solid var(--line); border-left: 5px solid var(--accent); }}
blockquote p:first-child {{ margin-top: 0; }}
blockquote p:last-child {{ margin-bottom: 0; }}
/* картинки */
figure.pic {{ margin: 18px 0; text-align: center; }}
figure.pic img {{ max-width: 100%; border-radius: 12px; border: 1px solid var(--line); box-shadow: 0 6px 18px rgba(20,30,60,.08); cursor: zoom-in; background: #fff; }}
figure.pic figcaption {{ font-size: 14px; color: var(--muted); margin-top: 7px; }}
#lightbox {{ position: fixed; inset: 0; background: rgba(12,16,30,.86); display: none; align-items: center; justify-content: center; z-index: 99; padding: 24px; cursor: zoom-out; }}
#lightbox img {{ max-width: 100%; max-height: 100%; border-radius: 10px; }}
#totop {{ position: fixed; right: 22px; bottom: 22px; width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--line); background: #fff; color: var(--muted); font-size: 19px; cursor: pointer; box-shadow: 0 6px 16px rgba(20,30,60,.14); display: none; z-index: 40; }}
#totop:hover {{ color: var(--accent); border-color: var(--accent); }}
@media (max-width: 980px) {{
  .layout {{ grid-template-columns: 1fr; gap: 0; }}
  aside {{ position: relative; height: auto; border-bottom: 1px solid var(--line); }}
  aside ul ul {{ display: none; }}
}}
@media print {{
  aside, #totop, #progress, .sidebtns {{ display: none !important; }}
  .layout {{ display: block; max-width: 100%; padding: 0; }}
  body {{ background: #fff; font-size: 12pt; }}
  h2 {{ break-after: avoid; box-shadow: none; }}
  figure.pic {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<div id="progress"></div>
<div class="layout">
<aside>
  <div class="brand">Вся химия с нуля до ЕГЭ<small>Конспект 12-часового марафона · Профиматика · Владислав Кварц</small></div>
  <div class="sidebtns">
    <a href="https://www.youtube.com/watch?v=s4d9DKnlCpE" target="_blank" rel="noopener">Открыть видео</a>
    <button onclick="window.print()">Скачать PDF</button>
  </div>
  <div class="meta">27.09.2026 · 11:54:32 · клик по «▶ время» открывает нужный момент в видео</div>
  {toc}
</aside>
<main>
{body}
</main>
</div>
<div id="lightbox" onclick="this.style.display='none'"><img id="lightbox-img" alt=""></div>
<button id="totop" title="Наверх" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
<script>
function zoom(el) {{
  var lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = el.src;
  lb.style.display = 'flex';
}}
document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') document.getElementById('lightbox').style.display = 'none'; }});
var links = [].slice.call(document.querySelectorAll('aside a.nav'));
var targets = links.map(function(a) {{
  var id = decodeURIComponent(a.getAttribute('href').slice(1));
  return document.getElementById(id);
}});
function onScroll() {{
  var h = document.documentElement;
  var p = h.scrollTop / (h.scrollHeight - h.clientHeight) * 100;
  document.getElementById('progress').style.width = p + '%';
  document.getElementById('totop').style.display = h.scrollTop > 600 ? 'block' : 'none';
  var best = -1, bestTop = -1e9;
  targets.forEach(function(t, i) {{
    if (!t) return;
    var top = t.getBoundingClientRect().top;
    if (top < 140 && top > bestTop) {{ bestTop = top; best = i; }}
  }});
  links.forEach(function(a) {{ a.classList.remove('active'); }});
  if (best >= 0) links[best].classList.add('active');
}}
document.addEventListener('scroll', onScroll, {{ passive: true }});
onScroll();
</script>
</body>
</html>
"""


def main() -> None:
    build()
    return None


if __name__ == "__main__":
    sys.exit(main())
