"""
MarketBullets — Word Commentary Publisher
Gary writes the commentary in Word and saves it into commentary/ as
YYYY-MM-DD.docx. This watcher turns it into the live dashboard:

  1. writes commentary/YYYY-MM-DD.md   (same format as the hand-written files,
                                         so index.json and the delayed landing
                                         page keep working)
  2. rebuilds commentary/index.json
  3. rewrites the DAILY UPDATE ZONE (MB_CONFIG) in every dashboard copy —
     dateline, bullets, body, and (if the doc has them) BoR status + prices
  4. commits and pushes. The Squarespace page fetches index01.html from GitHub
     on every load, so the site is current within a minute or two.

Only the NEWEST dated .docx drives the dashboard. Re-saving an older one only
refreshes its .md. Files starting with "_" (drafts, template) are ignored, so
draft as _DRAFT_2026-10-23.docx and Save a Copy as 2026-10-23.docx to publish.

Word document layout (see commentary/_TEMPLATE.docx):
    Dateline: ...                optional — default "FRIDAY, OCTOBER 23, 2026 · Pre-Dawn Update"
    Box-o-Rox: EXECUTE           optional — SUSPEND | EXECUTE | TRIPWIRE, optional "· Oct 22, 2026"
    [prices table]               optional — header row starting "Contract"
    Headline                     first ordinary paragraph (Title style recommended)
    • bullet  • bullet ...       Word bulleted list; may start with a color tag: [bear] [bull] [global] [usda] [macro]
    Narrative paragraphs         bold / italic / hyperlinks carry through
    [chart: WHEAT_SRW_D | caption]   on its own line, or inside a bullet

No third-party libraries required (reads the .docx with zipfile + xml).

Usage:
    python tools/word_commentary.py                     # watch mode (leave running)
    python tools/word_commentary.py --once              # publish newest .docx if changed, then exit
    python tools/word_commentary.py --file X.docx --no-git   # convert one file, don't commit/push
"""

import json
import logging
import re
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Every dashboard copy that carries its own MB_CONFIG. index01.html is the one
# the live Squarespace page fetches; the others are kept in sync with it.
DASHBOARD_FILES = [
    "SUBSCRIBER DASHBOARD/index01.html",
    "SUBSCRIBER DASHBOARD/index.html",
    "docs/members-dashboard.html",
]

POLL_SECONDS = 10
SETTLE_SECONDS = 45   # file must be unchanged this long — absorbs Word AutoSave bursts
GIT_RETRIES = 6

DATE_DOCX = re.compile(r"^(\d{4}-\d{2}-\d{2})\.docx$")
DATE_MD = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")

BULLET_COLORS = {
    "bull": "#E8B820", "wheat": "#E8B820", "bullish": "#E8B820",
    "global": "#7BBFDE", "export": "#7BBFDE",
    "usda": "#8FCB8A", "fundamental": "#8FCB8A", "crop": "#8FCB8A",
    "bear": "#E08050", "bearish": "#E08050", "warning": "#E08050",
    "macro": "#B0C0D0", "neutral": "#B0C0D0",
    "default": "#F5E6C0",
}
DEFAULT_COLOR = BULLET_COLORS["default"]

BOR_STATUS = {
    "SUSPEND": "suspend",
    "EXECUTE": "execute-60d", "THRESHOLD": "execute-60d", "EXECUTE-60D": "execute-60d",
    "TRIPWIRE": "execute-20d", "EXECUTE-20D": "execute-20d",
}

# Which existing MB_CONFIG price row a Word table row belongs to.
PRICE_KEYS = [
    ("ZW", ("SRW", "CHICAGO", "ZW")),
    ("KE", ("HRW", "KANSAS", "KC", "KE")),
    ("MWE", ("HRS", "MINNEAPOLIS", "MPLS", "MWE")),
    ("EBM", ("FWH", "PARIS", "EURONEXT", "EBM")),
]

CHART_TAG = re.compile(r"\[chart:\s*([^\]|]+?)\s*(?:\|\s*([^\]]*?)\s*)?\]", re.I)
SETTING_LINE = re.compile(r"^\s*(dateline|box-o-rox|bor)\s*:\s*(.*?)\s*$", re.I)
COLOR_TAG = re.compile(r"^\s*\[([a-z]+)\]\s*", re.I)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

log = logging.getLogger("word_commentary")


# ──────────────────────────────────────────────────────────────────────────
#  .docx reading
# ──────────────────────────────────────────────────────────────────────────

class Seg:
    """A run of text with one formatting. text == "\n" marks a line break."""
    __slots__ = ("text", "bold", "italic", "link")

    def __init__(self, text, bold=False, italic=False, link=None):
        self.text, self.bold, self.italic, self.link = text, bold, italic, link

    def same_format(self, other):
        return (self.bold, self.italic, self.link) == (other.bold, other.italic, other.link)


def _on(el):
    """True if a toggle property like <w:b/> is on (absent val, or val not false)."""
    if el is None:
        return False
    return el.get(W + "val", "true").lower() not in ("0", "false", "off", "none")


def _hyperlink_target(instr):
    m = re.search(r'HYPERLINK\s+"([^"]+)"', instr or "")
    return m.group(1) if m else None


class DocxReader:
    def __init__(self, path: Path):
        # Read the bytes once so Word holding the file open can't bite mid-parse.
        with open(path, "rb") as fh:
            data = fh.read()
        import io
        zf = zipfile.ZipFile(io.BytesIO(data))
        self.doc = ET.fromstring(zf.read("word/document.xml"))
        self.rels = {}
        if "word/_rels/document.xml.rels" in zf.namelist():
            for rel in ET.fromstring(zf.read("word/_rels/document.xml.rels")).iter(PKG_REL + "Relationship"):
                self.rels[rel.get("Id")] = rel.get("Target")
        self.styles = {}
        if "word/styles.xml" in zf.namelist():
            for st in ET.fromstring(zf.read("word/styles.xml")).iter(W + "style"):
                name_el = st.find(W + "name")
                based = st.find(W + "basedOn")
                ppr = st.find(W + "pPr")
                self.styles[st.get(W + "styleId")] = {
                    "name": (name_el.get(W + "val") if name_el is not None else "").lower(),
                    "based": based.get(W + "val") if based is not None else None,
                    "num": ppr is not None and ppr.find(W + "numPr") is not None,
                }

    # ── style helpers ──
    def _style_chain(self, sid):
        seen = set()
        while sid and sid in self.styles and sid not in seen:
            seen.add(sid)
            yield self.styles[sid]
            sid = self.styles[sid]["based"]

    def is_list(self, p):
        ppr = p.find(W + "pPr")
        if ppr is not None:
            numpr = ppr.find(W + "numPr")
            if numpr is not None:
                num_id = numpr.find(W + "numId")
                return num_id is None or num_id.get(W + "val") != "0"
            ps = ppr.find(W + "pStyle")
            if ps is not None:
                for st in self._style_chain(ps.get(W + "val")):
                    if st["num"] or st["name"].startswith("list bullet") or st["name"].startswith("list number"):
                        return True
        return False

    def style_name(self, p):
        ppr = p.find(W + "pPr")
        ps = ppr.find(W + "pStyle") if ppr is not None else None
        if ps is None:
            return ""
        st = self.styles.get(ps.get(W + "val"))
        return st["name"] if st else ps.get(W + "val", "").lower()

    # ── paragraph text ──
    def segments(self, p):
        segs = []
        field = {"depth": 0, "instr": "", "in_result": False, "link": None}

        def walk(el, link):
            for child in el:
                tag = child.tag
                if tag == W + "r":
                    run(child, link)
                elif tag == W + "hyperlink":
                    rid = child.get(R + "id")
                    target = self.rels.get(rid) if rid else None
                    anchor = child.get(W + "anchor")
                    walk(child, target or (("#" + anchor) if anchor else link))
                elif tag == W + "fldSimple":
                    walk(child, _hyperlink_target(child.get(W + "instr")) or link)
                elif tag in (W + "ins", W + "smartTag", W + "customXml", W + "sdt", W + "sdtContent"):
                    walk(child, link)
                # w:del, w:pPr, bookmarks, comments: skipped

        def run(r, link):
            rpr = r.find(W + "rPr")
            bold = italic = False
            if rpr is not None:
                bold = _on(rpr.find(W + "b"))
                italic = _on(rpr.find(W + "i"))
                if rpr.find(W + "vanish") is not None and _on(rpr.find(W + "vanish")):
                    return
            for c in r:
                t = c.tag
                if t == W + "fldChar":
                    kind = c.get(W + "fldCharType")
                    if kind == "begin":
                        field.update(depth=field["depth"] + 1, instr="", in_result=False)
                    elif kind == "separate":
                        field["in_result"] = True
                        field["link"] = _hyperlink_target(field["instr"])
                    elif kind == "end":
                        field.update(depth=max(0, field["depth"] - 1), in_result=False, link=None)
                elif t == W + "instrText":
                    field["instr"] += c.text or ""
                elif field["depth"] and not field["in_result"]:
                    continue  # field code, not visible text
                elif t == W + "t":
                    segs.append(Seg(c.text or "", bold, italic, field["link"] or link))
                elif t == W + "tab":
                    segs.append(Seg(" ", bold, italic, field["link"] or link))
                elif t in (W + "br", W + "cr"):
                    if c.get(W + "type") in (None, "textWrapping"):
                        segs.append(Seg("\n"))
                elif t == W + "noBreakHyphen":
                    segs.append(Seg("-", bold, italic, field["link"] or link))
                elif t == W + "sym":
                    pass

        walk(p, None)
        return merge(segs)

    # ── document blocks ──
    def blocks(self):
        """Yields ('p', element) and ('tbl', rows-of-cell-text) in document order."""
        body = self.doc.find(W + "body")

        def walk(el):
            for child in el:
                if child.tag == W + "p":
                    yield "p", child
                elif child.tag == W + "tbl":
                    rows = []
                    for tr in child.iter(W + "tr"):
                        rows.append([plain(self.segments_of_cell(tc)) for tc in tr.findall(W + "tc")])
                    yield "tbl", rows
                elif child.tag in (W + "sdt", W + "sdtContent", W + "customXml"):
                    yield from walk(child)

        yield from walk(body)

    def segments_of_cell(self, tc):
        segs = []
        for p in tc.iter(W + "p"):
            if segs:
                segs.append(Seg(" "))
            segs.extend(self.segments(p))
        return segs


def merge(segs):
    out = []
    for s in segs:
        if not s.text:
            continue
        if out and s.text != "\n" and out[-1].text != "\n" and out[-1].same_format(s):
            out[-1].text += s.text
        else:
            out.append(Seg(s.text, s.bold, s.italic, s.link))
    # trim leading/trailing whitespace and breaks
    while out and not out[0].text.strip():
        out.pop(0)
    while out and not out[-1].text.strip():
        out.pop()
    if out:
        out[0].text = out[0].text.lstrip()
        out[-1].text = out[-1].text.rstrip()
    return out


def plain(segs):
    return "".join(s.text for s in segs).strip()


def strip_prefix(segs, n):
    """Remove the first n characters of text across segments."""
    out = []
    for s in segs:
        if n <= 0:
            out.append(s)
        elif len(s.text) <= n:
            n -= len(s.text)
        else:
            out.append(Seg(s.text[n:], s.bold, s.italic, s.link))
            n = 0
    return merge(out)


# ──────────────────────────────────────────────────────────────────────────
#  Document model
# ──────────────────────────────────────────────────────────────────────────

class Commentary:
    def __init__(self):
        self.headline = []        # segs
        self.dateline = None
        self.bor = None           # (status, date-text or None)
        self.prices = []          # rows of cell text, header excluded
        self.price_header = []
        self.bullets = []         # (color, segs)
        self.body = []            # ('p', segs) | ('li', segs) | ('chart', name, caption)
        self.warnings = []


def parse_docx(path: Path) -> Commentary:
    rd = DocxReader(path)
    c = Commentary()

    for kind, item in rd.blocks():
        if kind == "tbl":
            if item and item[0] and item[0][0].strip().lower().startswith("contract"):
                c.price_header = [h.strip().lower() for h in item[0]]
                # a row with no numbers filled in means "leave that contract as it is"
                c.prices = [row for row in item[1:] if any(cell.strip() for cell in row[1:])]
            else:
                c.warnings.append("A table that isn't the prices table was skipped.")
            continue

        p = item
        segs = rd.segments(p)
        text = plain(segs)
        if not text or text == "---":
            continue

        started = bool(c.headline)
        m = SETTING_LINE.match(text)
        if m and not c.bullets and not c.body:
            key, val = m.group(1).lower(), m.group(2)
            if not val:
                continue  # left blank → default dateline / BoR unchanged
            if key == "dateline":
                c.dateline = val
            else:
                parts = re.split(r"\s*[·|,–—-]\s*", val, maxsplit=1)
                status = BOR_STATUS.get(parts[0].strip().upper().replace(" ", "-"))
                if status:
                    c.bor = (status, parts[1].strip() if len(parts) > 1 and parts[1].strip() else None)
                else:
                    c.warnings.append(f"Box-o-Rox value '{val}' not recognized — use SUSPEND, EXECUTE or TRIPWIRE.")
            continue

        is_list = rd.is_list(p)
        chart = CHART_TAG.fullmatch(text)

        if not started and not is_list and not chart:
            c.headline = strip_prefix(segs, len(text) - len(text.lstrip("# "))) if text.startswith("#") else segs
            continue

        if chart and not is_list:
            c.body.append(("chart", chart.group(1).strip(), (chart.group(2) or "").strip()))
        elif is_list and not c.body:
            color = DEFAULT_COLOR
            cm = COLOR_TAG.match(text)
            if cm and cm.group(1).lower() in BULLET_COLORS:
                color = BULLET_COLORS[cm.group(1).lower()]
                segs = strip_prefix(segs, cm.end())
            c.bullets.append((color, segs))
        elif is_list:
            c.body.append(("li", segs))
        else:
            c.body.append(("p", segs))

    if not c.headline:
        raise ValueError("No headline found — the first paragraph of the document should be the headline.")
    if not c.body:
        raise ValueError("No narrative paragraphs found after the bullets.")
    return c


# ──────────────────────────────────────────────────────────────────────────
#  Rendering
# ──────────────────────────────────────────────────────────────────────────

def chart_file(name):
    name = name.strip()
    return name if re.search(r"\.(png|jpe?g|gif|webp)$", name, re.I) else name + ".png"


def to_html(segs):
    out = []
    for s in segs:
        if s.text == "\n":
            out.append("<br>")
            continue
        h = escape(s.text, quote=False)
        if s.italic:
            h = f"<em>{h}</em>"
        if s.bold:
            h = f"<strong>{h}</strong>"
        if s.link:
            h = f'<a href="{escape(s.link)}" target="_blank" rel="noopener">{h}</a>'
        out.append(h)
    return "".join(out)


def to_md(segs):
    out = []
    for s in segs:
        if s.text == "\n":
            out.append("  \n")
            continue
        t = s.text
        if s.italic:
            t = f"*{t}*"
        if s.bold:
            t = f"**{t}**"
        if s.link:
            t = f"[{t}]({s.link})"
        out.append(t)
    return "".join(out)


def bullet_html(segs):
    """Bullets aren't run through the page's shortcode pass, so expand chart tags here."""
    def thumb(m):
        url = "https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/" + chart_file(m.group(1))
        alt = escape(m.group(2) or m.group(1))
        return (f'<a href="{url}" target="_blank" rel="noopener" style="float:right;margin:2px 0 8px 14px">'
                f'<img src="{url}" class="inline-chart-thumb" alt="{alt}"></a>')
    return CHART_TAG.sub(thumb, to_html(segs))


def body_html(c: Commentary):
    parts = [f'<p style="font-size:1.15em;color:#E8B820"><strong>{to_html(c.headline)}</strong></p>']
    in_list = False
    for item in c.body:
        if item[0] == "li":
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"  <li>{to_html(item[1])}</li>")
            continue
        if in_list:
            parts.append("</ul>")
            in_list = False
        if item[0] == "p":
            parts.append("<p>" + CHART_TAG.sub(lambda m: f"[chart:{chart_file(m.group(1))}]", to_html(item[1])) + "</p>")
        else:  # chart on its own line → tuck the thumbnail into the paragraph it illustrates
            code = f"[chart:{chart_file(item[1])}]"
            if parts[-1].startswith("<p>") and parts[-1].endswith("</p>"):
                parts[-1] = parts[-1][:-4] + " " + code + "</p>"
            else:
                parts.append(f"<p>{code}</p>")
    if in_list:
        parts.append("</ul>")
    return parts


def markdown(c: Commentary):
    lines = [f"# {to_md(c.headline)}", ""]
    for _, segs in c.bullets:
        lines.append("- " + to_md(segs))
    lines += ["", "---", ""]
    for i, item in enumerate(c.body):
        if item[0] != "li" and i and c.body[i - 1][0] == "li":
            lines.append("")
        if item[0] == "p":
            lines += [to_md(item[1]), ""]
        elif item[0] == "li":
            lines.append("- " + to_md(item[1]))
        else:
            cap = f" | {item[2]}" if item[2] else ""
            lines += [f"[chart: {item[1]}{cap}]", ""]
    return "\n".join(lines).rstrip() + "\n"


# ── JavaScript string escaping (the dashboard breaks on one bad apostrophe) ──

def js_single(s):
    return ("'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\r", "").replace("\n", "\\n")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029").replace("</", "<\\/") + "'")


def js_template(s):
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${").replace("</", "<\\/")


# ──────────────────────────────────────────────────────────────────────────
#  MB_CONFIG update
# ──────────────────────────────────────────────────────────────────────────

# Same pattern the live page uses to pull MB_CONFIG out of index01.html.
CONFIG_BLOCK = re.compile(r"const MB_CONFIG = (\{[\s\S]*?\r?\n\});")
PRICE_FIELD = re.compile(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'")


def default_dateline(d: date):
    return f"{d:%A}, {d:%B} {d.day}, {d.year}".upper() + " · Pre-Dawn Update"


def previous_weekday(d: date):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def chg_dir(chg):
    t = chg.strip().replace("−", "-").replace("–", "-")
    if not t or t in ("—", "-") or t.lower().startswith("unch"):
        return "flat"
    if t.startswith("-"):
        return "dn"
    if re.sub(r"[^0-9]", "", t).strip("0") == "":
        return "flat"
    return "up"


def price_rows(c: Commentary, existing_block: str, nl: str):
    """New prices array body, or None if the doc has no prices table."""
    if not c.prices:
        return None
    existing = []
    for m in re.finditer(r"\{([^{}]*)\}", existing_block):
        fields = dict(PRICE_FIELD.findall(m.group(1)))
        if "ticker" in fields:
            existing.append(fields)
    by_ticker = {f["ticker"]: f for f in existing}

    header = c.price_header
    col = {name: header.index(name) for name in ("open", "high", "low", "close", "chg") if name in header}
    if "chg" not in col and "change" in header:
        col["chg"] = header.index("change")

    for row in c.prices:
        label = row[0].strip()
        up = label.upper()
        ticker = next((t for t, keys in PRICE_KEYS if any(re.search(rf"\b{k}\b", up) for k in keys)), None)
        if not ticker or ticker not in by_ticker:
            c.warnings.append(f"Price row '{label}' didn't match SRW / HRW / HRS / FWH — skipped.")
            continue
        f = by_ticker[ticker]
        f["contract"] = label
        for name, i in col.items():
            val = row[i].strip() if i < len(row) else ""
            f[name] = (val.replace("−", "-") if name == "chg" else val) or "—"
        f["chgDir"] = chg_dir(f.get("chg", ""))

    lines = []
    for f in existing:
        q = lambda k: js_single(f.get(k, "—"))
        lines.append(f"    {{ contract:{q('contract')}, exchange:{q('exchange')}, ticker:{q('ticker')}, unit:{q('unit')},")
        lines.append(f"      open:{q('open')},  high:{q('high')},  low:{q('low')},  close:{q('close')},  "
                     f"chg:{q('chg')},  chgDir:{q('chgDir')} }},")
    return nl.join(lines)


def build_config(old_block: str, c: Commentary, session: date, source_name: str):
    nl = "\r\n" if "\r\n" in old_block else "\n"
    block = old_block

    def sub_once(pattern, repl, label):
        nonlocal block
        new, n = re.subn(pattern, repl, block, count=1)
        if n != 1:
            raise ValueError(f"Couldn't find '{label}' inside MB_CONFIG — has the dashboard layout changed?")
        block = new

    dateline = c.dateline or default_dateline(session)
    sub_once(r"(\n  dateline:\s*)'(?:[^'\\]|\\.)*'", lambda m: m.group(1) + js_single(dateline), "dateline")

    bullets = nl.join(f"    {{ color: '{color}', text: {js_single(bullet_html(segs))} }},"
                      for color, segs in c.bullets)
    sub_once(r"(\n  bullets: \[)[\s\S]*?(\r?\n  \],)",
             lambda m: m.group(1) + (nl + bullets if bullets else "") + m.group(2), "bullets")

    comment = (f"/* ── COMMENTARY BODY ─────────────────────────────────{nl}"
               f"     {session:%A %Y-%m-%d}. Published from Word: commentary/{source_name}{nl}"
               f"     (tools/word_commentary.py — edit the .docx, not this block){nl}"
               f"     ─────────────────────────────────────────────────── */")
    block = re.sub(r"/\* ── COMMENTARY BODY[\s\S]*?\*/", lambda m: comment, block, count=1)

    body = nl.join(("    " + js_template(line)) if line else ""
                   for line in _with_blank_lines(body_html(c)))
    sub_once(r"(\n  body: `)[\s\S]*(`\s*\r?\n\})$",
             lambda m: m.group(1) + nl + body + nl + "  " + m.group(2).lstrip(), "body")

    if c.bor:
        status, when = c.bor
        sub_once(r"(\n  borStatus:\s*)'[^']*'", lambda m: m.group(1) + js_single(status), "borStatus")
        if not when:
            d = previous_weekday(session)
            when = f"{d:%b} {d.day}, {d.year}"
        sub_once(r"(\n  borDate:\s*)'[^']*'", lambda m: m.group(1) + js_single(when), "borDate")

    m = re.search(r"(\n  prices: \[)([\s\S]*?)(\r?\n  \],)", block)
    if m:
        rows = price_rows(c, m.group(2), nl)
        if rows is not None:
            block = block[:m.start()] + m.group(1) + nl + rows + m.group(3) + block[m.end():]

    return block


def _with_blank_lines(parts):
    out = []
    for p in parts:
        if out and not p.startswith("  <li>") and p != "</ul>":
            out.append("")
        out.append(p)
    return out


def validate_config(text: str, expect_bullets: int):
    """Re-extract MB_CONFIG exactly the way the live page does and sanity-check it."""
    m = CONFIG_BLOCK.search(text)
    if not m:
        raise ValueError("MB_CONFIG can't be extracted the way the live page reads it.")
    block = m.group(1)
    bullet_lines = re.findall(r"^    \{ color: '#[0-9A-Fa-f]{6}', text: '(?:[^'\\\r\n]|\\.)*' \},\r?$", block, re.M)
    if len(bullet_lines) != expect_bullets:
        raise ValueError(f"Bullet check failed: expected {expect_bullets}, found {len(bullet_lines)} well-formed.")
    body = re.search(r"\n  body: `([\s\S]*)`\s*\r?\n\}$", block)
    if not body or re.search(r"(?<!\\)(?:\\\\)*`", body.group(1)):
        raise ValueError("Body check failed: unescaped backtick in commentary body.")
    for line in block.splitlines():
        if line.startswith("};"):
            raise ValueError("Body check failed: a line starting with '};' would cut MB_CONFIG short.")


def update_dashboard(path: Path, c: Commentary, session: date, source_name: str) -> bool:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    m = CONFIG_BLOCK.search(text)
    if not m:
        raise ValueError(f"No MB_CONFIG block in {path.name}")
    new_block = build_config(m.group(1), c, session, source_name)
    new_text = text[:m.start(1)] + new_block + text[m.end(1):]
    validate_config(new_text, len(c.bullets))
    if new_text == text:
        return False
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8"))
    return True


# ──────────────────────────────────────────────────────────────────────────
#  commentary/index.json  (same format as tools/commentary_watcher.py)
# ──────────────────────────────────────────────────────────────────────────

def write_index(commentary_dir: Path) -> bool:
    entries = []
    for p in sorted(commentary_dir.glob("*.md"), reverse=True):
        m = DATE_MD.match(p.name)
        if not m:
            continue
        headline = "(no headline)"
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                headline = line.strip().lstrip("#").strip()
                break
        entries.append({"date": m.group(1), "headline": headline, "file": p.name})
    index_file = commentary_dir / "index.json"
    if index_file.exists():
        try:
            if json.loads(index_file.read_text(encoding="utf-8")).get("entries") == entries:
                return False
        except (json.JSONDecodeError, OSError):
            pass
    index_file.write_text(json.dumps({"generated": datetime.now().isoformat(timespec="seconds"),
                                      "entries": entries}, indent=2), encoding="utf-8")
    return True


# ──────────────────────────────────────────────────────────────────────────
#  git
# ──────────────────────────────────────────────────────────────────────────

def git(root: Path, *args):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, creationflags=flags)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def git_retry(root: Path, *args):
    """Retries while another watcher holds the index lock."""
    for attempt in range(GIT_RETRIES):
        rc, out, err = git(root, *args)
        if rc == 0 or "index.lock" not in err:
            return rc, out, err
        time.sleep(5)
    return rc, out, err


def commit_and_push(root: Path, paths: list, session: date) -> bool:
    rel = [str(p.relative_to(root)).replace("\\", "/") for p in paths]
    rc, _, err = git_retry(root, "add", "--", *rel)
    if rc != 0:
        log.error(f"git add failed: {err}")
        return False
    rc, staged, _ = git(root, "diff", "--cached", "--name-only", "--", *rel)
    if not staged:
        log.info("Nothing new to commit.")
        return True
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    rc, _, err = git_retry(root, "commit", "-m", f"Commentary from Word: {session} [{stamp}]", "--", *rel)
    if rc != 0:
        log.error(f"git commit failed: {err}")
        return False
    rc, _, err = git_retry(root, "pull", "--rebase", "--autostash", "origin", "main")
    if rc != 0:
        log.error(f"git pull --rebase failed (commit is saved locally, will retry next save): {err}")
        git(root, "rebase", "--abort")
        return False
    rc, _, err = git_retry(root, "push", "origin", "main")
    if rc != 0:
        log.error(f"git push failed (commit is saved locally, will retry next save): {err}")
        return False
    log.info("Pushed — the dashboard picks it up on next page load.")
    return True


# ──────────────────────────────────────────────────────────────────────────
#  Publish one file
# ──────────────────────────────────────────────────────────────────────────

def newest_docx(commentary_dir: Path):
    dated = [p for p in commentary_dir.glob("*.docx") if DATE_DOCX.match(p.name)]
    return max(dated, key=lambda p: p.name) if dated else None


def publish(docx: Path, root: Path, use_git=True, force_dashboard=False) -> bool:
    m = DATE_DOCX.match(docx.name)
    if not m:
        raise ValueError(f"{docx.name}: name must be YYYY-MM-DD.docx")
    session = date.fromisoformat(m.group(1))
    commentary_dir = root / "commentary"

    c = parse_docx(docx)
    for w in c.warnings:
        log.warning(f"{docx.name}: {w}")
    log.info(f"{docx.name}: headline '{plain(c.headline)[:70]}', {len(c.bullets)} bullets, "
             f"{sum(1 for b in c.body if b[0] == 'p')} paragraphs"
             + (f", BoR {c.bor[0]}" if c.bor else "") + (f", {len(c.prices)} price rows" if c.prices else ""))

    touched = [docx]
    md_path = commentary_dir / f"{session}.md"
    md_path.write_text(markdown(c), encoding="utf-8")
    touched.append(md_path)
    write_index(commentary_dir)
    touched.append(commentary_dir / "index.json")

    newest = newest_docx(commentary_dir)
    if force_dashboard or (newest and newest.name == docx.name):
        for rel in DASHBOARD_FILES:
            path = root / rel
            if not path.exists():
                log.warning(f"Dashboard copy missing, skipped: {rel}")
                continue
            if update_dashboard(path, c, session, docx.name):
                log.info(f"Updated MB_CONFIG in {rel}")
            touched.append(path)
    else:
        log.info(f"{docx.name} is not the newest commentary ({newest.name}) — dashboard left alone, .md refreshed.")

    if use_git:
        return commit_and_push(root, touched, session)
    return True


# ──────────────────────────────────────────────────────────────────────────
#  Watch loop
# ──────────────────────────────────────────────────────────────────────────

def needs_publish(docx: Path, root: Path) -> bool:
    md = root / "commentary" / (docx.stem + ".md")
    return not md.exists() or md.stat().st_mtime < docx.stat().st_mtime


def safe_publish(docx: Path, root: Path, use_git: bool):
    try:
        publish(docx, root, use_git)
    except PermissionError:
        log.info(f"{docx.name} is locked by Word mid-save — will retry.")
        return False
    except (ValueError, zipfile.BadZipFile, ET.ParseError, KeyError) as e:
        log.error(f"{docx.name} NOT published: {e}")
    return True


def watch(root: Path, use_git: bool):
    commentary_dir = root / "commentary"
    log.info("=" * 60)
    log.info("MarketBullets Word Commentary Publisher started")
    log.info(f"Watching: {commentary_dir}  (YYYY-MM-DD.docx)")
    log.info(f"Publishes once a file has been unchanged for {SETTLE_SECONDS}s.")
    log.info("=" * 60)

    seen = {}       # name -> mtime last published (or last failed)
    pending = {}    # name -> mtime waiting to settle
    for p in commentary_dir.glob("*.docx"):
        if DATE_DOCX.match(p.name):
            if needs_publish(p, root):
                pending[p.name] = p.stat().st_mtime
            else:
                seen[p.name] = p.stat().st_mtime

    try:
        while True:
            now = time.time()
            for p in commentary_dir.glob("*.docx"):
                if not DATE_DOCX.match(p.name):
                    continue
                try:
                    mtime = p.stat().st_mtime
                except OSError:
                    continue
                if seen.get(p.name) == mtime:
                    continue
                if pending.get(p.name) != mtime:
                    if p.name not in pending:
                        log.info(f"Change detected: {p.name} — waiting for Word to finish saving…")
                    pending[p.name] = mtime
            # oldest first, so the newest file has the final say on the dashboard
            ready = sorted(n for n, mt in pending.items() if now - mt >= SETTLE_SECONDS)
            for name in ready:
                p = commentary_dir / name
                if not p.exists():
                    pending.pop(name, None)
                    continue
                if safe_publish(p, root, use_git):
                    seen[name] = pending.pop(name)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        log.info("Word Commentary Publisher stopped.")


def main(argv):
    root = REPO_ROOT
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).resolve()
    use_git = "--no-git" not in argv

    handlers = [logging.StreamHandler()]
    log_file = root / "tools" / "word_commentary.log"
    if log_file.parent.exists():
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", handlers=handlers)

    if "--file" in argv:
        docx = Path(argv[argv.index("--file") + 1]).resolve()
        publish(docx, root, use_git, force_dashboard="--dashboard" in argv)
        return 0

    if "--once" in argv:
        newest = newest_docx(root / "commentary")
        if newest and needs_publish(newest, root):
            safe_publish(newest, root, use_git)
        else:
            log.info("Nothing to publish.")
        return 0

    (root / "commentary").mkdir(exist_ok=True)
    watch(root, use_git)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
