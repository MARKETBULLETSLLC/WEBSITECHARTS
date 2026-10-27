"""
MarketBullets — Draft Preview
Renders a commentary draft (.md, or an editor.html saved-session .json) to
commentary/_PREVIEW.html and opens it in the browser. Charts load from the
local charts/ folder, so the preview shows tonight's exports.

    python tools/preview_draft.py                  # newest draft in commentary/
    python tools/preview_draft.py <file.md|.json>  # a specific file

Local only: nothing is committed, pushed, or published. _PREVIEW.html is gitignored.
"""
import datetime
import html
import json
import os
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
COMMENTARY = REPO_ROOT / "commentary"
OUT = COMMENTARY / "_PREVIEW.html"
CHARTS = "../charts/"

COLORS = {"bull": "#E8B820", "global": "#7BBFDE", "usda": "#8FCB8A",
          "bear": "#E08050", "macro": "#B0C0D0", "default": "#F5E6C0"}
BOR = {"suspend": "SUSPEND", "execute-60d": "EXECUTE", "execute-20d": "EXECUTE"}
CHART_TAG = re.compile(r"\[chart:\s*([A-Za-z0-9_\-]+)\s*(?:\|\s*([^\]]*))?\]")
DRAFT_NAME = re.compile(r"^_?(?:DRAFT_)?\d{4}-\d{2}-\d{2}\.(md|json)$")


def editor_notes(s):
    s = re.sub(r"<em>\s*\[EDITOR([^\]]*)\]\s*</em>", r"[EDITOR\1]", s)
    return re.sub(r"\[EDITOR([^\]]*)\]", r'<span class="ed">[EDITOR\1]</span>', s)


def md_inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\[EDITOR(.*?)\]\*", r"[EDITOR\1]", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    return editor_notes(s)


def chart(f, caption=None, small=False):
    if not f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        f += ".png"
    name = f.rsplit(".", 1)[0]
    missing = "" if (REPO_ROOT / "charts" / f).exists() else ' <span class="ed">MISSING in charts/</span>'
    cap = html.escape(caption) + " " if caption else ""
    return (f'<figure class="thumb{" small" if small else ""}"><a href="{CHARTS}{f}" target="_blank">'
            f'<img src="{CHARTS}{f}" alt="{name}"></a><figcaption>{cap}<code>{name}</code>{missing}</figcaption></figure>')


def bullet(color, text, thumb=""):
    return (f'<li><span class="dot" style="background:{color};box-shadow:0 0 6px 2px {color}40"></span>'
            f'<div style="color:{color}">{thumb}{text}</div></li>')


def from_md(path):
    head, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
    lines = head.splitlines()
    headline = md_inline(next(l for l in lines if l.strip()).lstrip("# ").strip())
    bullets = []
    for l in lines:
        if not l.startswith("- "):
            continue
        t = l[2:].strip()
        m = re.match(r"\[(bull|bear|global|usda|macro|default)\]\s*", t)
        color = COLORS[m.group(1) if m else "default"]
        t = t[m.end():] if m else t
        c = CHART_TAG.match(t)
        thumb = chart(c.group(1), small=True) if c else ""
        t = t[c.end():].strip() if c else t
        bullets.append(bullet(color, md_inline(t), thumb))
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        rows = block.strip().splitlines()
        if all(CHART_TAG.fullmatch(r.strip()) for r in rows):
            out.append('<div class="charts">' + "".join(
                chart(*CHART_TAG.fullmatch(r.strip()).groups()) for r in rows) + "</div>")
        elif all(r.startswith("- ") for r in rows):
            out.append("<ul>" + "".join(f"<li>{md_inline(r[2:])}</li>" for r in rows) + "</ul>")
        else:
            out.append("<p>" + "<br>".join(md_inline(r) for r in rows) + "</p>")
    date = re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    return dict(date=date.group(0) if date else None, dateline="", headline=headline,
                bullets="".join(bullets), body="".join(out), top="", saved="")


def from_json(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    rows = "".join(
        f"<tr><td>{html.escape(p['contract'])}</td><td>{p['open'] or '—'}</td><td>{p['high'] or '—'}</td>"
        f"<td>{p['low'] or '—'}</td><td class='cl'>{p['close'] or '—'}</td>"
        f"<td class='{'up' if p['chg'].startswith('+') else 'dn' if p['chg'].startswith('-') else ''}'>{p['chg'] or '—'}</td></tr>"
        for p in d.get("prices", []))
    bor = BOR.get(d["bor"]["status"], d["bor"]["status"].upper())
    top = (f'<div class="top"><div class="bor"><small>BOX-O-ROX</small>'
           f'<b class="{"sus" if bor == "SUSPEND" else "exe"}">{bor}</b><small>{d["bor"].get("date") or ""}</small></div>'
           f'<table><thead><tr><th>Contract</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Chg</th></tr></thead>'
           f'<tbody>{rows}</tbody></table></div>')
    bullets = "".join(bullet(b["color"], editor_notes(b["html"]),
                             chart(b["chart"], small=True) if b.get("chart") else "") for b in d["bullets"])
    body = ""
    for p in d["body"]:
        h = p["html"].strip()
        if h:
            body += editor_notes(h) if h.startswith(("<ul", "<ol")) else f"<p>{editor_notes(h)}</p>"
        if p.get("charts"):
            body += '<div class="charts">' + "".join(chart(c) for c in p["charts"]) + "</div>"
    return dict(date=d.get("date"), dateline=d.get("dateline", ""), headline=d["headline"],
                bullets=bullets, body=body, top=top, saved=d.get("savedAt", ""))


CSS = """
:root{--soil:#0A0704;--soil-lt:#1A1208;--wheat:#C8960A;--wheat-lt:#E8B820;--pal:#F5E6C0;--border:rgba(200,150,10,.2);}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--soil);color:var(--pal);font-family:Lora,Georgia,serif;font-size:17px;line-height:1.65;padding:0 16px 80px}
.banner{font:13px 'IBM Plex Mono',monospace;letter-spacing:.08em;text-transform:uppercase;text-align:center;padding:8px;background:rgba(200,150,10,.12);color:var(--wheat-lt);margin:0 -16px 28px}
main{max-width:860px;margin:0 auto}
.top{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:24px}
.bor{border:1px solid var(--border);background:var(--soil-lt);padding:14px 18px;border-radius:4px;min-width:180px}
.bor b{display:block;font:22px 'DM Serif Display',serif;letter-spacing:.04em} .bor .exe{color:#E05030} .bor .sus{color:#32C850}
.bor small{font:13px 'IBM Plex Mono',monospace;color:#cdbf9c}
table{flex:1 1 420px;border-collapse:collapse;font:14px 'IBM Plex Mono',monospace;border:1px solid var(--border);background:var(--soil-lt)}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid rgba(200,150,10,.09)} th:first-child,td:first-child{text-align:left}
th{color:var(--wheat);font-weight:400} .cl{color:var(--wheat-lt);font-weight:600} .up{color:#5AAA70} .dn{color:#E05030}
.dateline{font:15px 'IBM Plex Mono',monospace;color:var(--wheat);letter-spacing:.06em;margin-bottom:10px}
h1{font-family:'DM Serif Display',Georgia,serif;font-weight:400;color:var(--wheat-lt);font-size:30px;line-height:1.2;margin-bottom:22px}
ul.bul{list-style:none;border:1px solid var(--border);background:var(--soil-lt);padding:18px 20px;border-radius:4px;margin-bottom:32px}
ul.bul li{display:flex;gap:12px;font-size:18px;margin-bottom:14px} ul.bul li:last-child{margin-bottom:0}
ul.bul li div::after{content:"";display:block;clear:both}
.dot{flex-shrink:0;width:7px;height:7px;border-radius:50%;margin-top:11px}
.body p{margin-bottom:20px} .body ul{margin:0 0 20px 22px} .body li{margin-bottom:10px}
a{color:var(--wheat-lt);text-decoration:none;border-bottom:1px solid rgba(232,184,32,.35)}
strong,b{color:#FBF7EE}
.ed{background:#5a1e10;color:#ffb38a;font:14px 'IBM Plex Mono',monospace;padding:1px 5px;border-radius:3px}
.charts{display:flex;flex-wrap:wrap;gap:14px;margin:4px 0 24px}
.thumb{flex:1 1 380px;border:1px solid var(--border);background:var(--soil-lt);padding:6px;border-radius:4px}
.thumb img{width:100%;display:block} .thumb a{border:0}
.thumb figcaption{font-size:14px;color:#cdbf9c;padding:6px 2px 0} code{font:13px 'IBM Plex Mono',monospace;color:var(--wheat)}
.thumb.small{float:right;width:180px;flex:none;margin:0 0 8px 14px} .thumb.small figcaption{display:none}
@media (max-width:600px){.thumb.small{float:none;width:100%;margin:0 0 8px}}
"""


def newest_draft():
    files = [p for p in COMMENTARY.iterdir() if DRAFT_NAME.match(p.name)]
    if not files:
        sys.exit("No drafts found in commentary/")
    return max(files, key=lambda p: p.stat().st_mtime)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = pathlib.Path(args[0]).resolve() if args else newest_draft()
    d = from_json(path) if path.suffix.lower() == ".json" else from_md(path)
    dateline = d["dateline"]
    if not dateline and d["date"]:
        dateline = datetime.date.fromisoformat(d["date"]).strftime("%A, %B %d, %Y").upper() + " · Pre-Dawn Update"
    saved = f" · saved {d['saved']}" if d["saved"] else ""
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Draft Preview</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Lora:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="banner">Draft preview · {html.escape(path.name)}{saved} · not published · editor notes in red</div>
<main>{d['top']}
<div class="dateline">{html.escape(dateline)}</div>
<h1>{d['headline']}</h1>
<ul class="bul">{d['bullets']}</ul>
<div class="body">{d['body']}</div>
</main></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"Previewing {path.name} -> {OUT}")
    if "--no-open" not in sys.argv:
        os.startfile(OUT)


if __name__ == "__main__":
    main()
