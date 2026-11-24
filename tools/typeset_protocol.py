#!/usr/bin/env python3
"""typeset_protocol.py - render docs/MANGO_LEAF_TRIAL.md to a readable A4 PDF.

No pandoc / LaTeX / cairo in this environment and no root to install them, so this is a
purpose-built renderer on ReportLab (pure wheel, no system libraries) using the DejaVu fonts
that are already on the box. It is deliberately NOT a general Markdown engine: it implements
exactly the constructs this document uses, and it FAILS LOUDLY on anything it does not
recognise, so no text can silently vanish from the PDF.

Constructs handled: ATX headings (#/##/###), pipe tables with alignment + bold cells and
wrapping, fenced code blocks, blockquotes as labelled callouts, ordered and unordered lists
with continuation lines, horizontal rules, and inline **bold**, *italic*, `code`, [links]().

Glyph safety: before rendering, every character outside ASCII is checked against the embedded
font's cmap. A missing glyph is an error, not a box in the output.

Usage:
    .venv/bin/python tools/typeset_protocol.py                    # -> docs/MANGO_LEAF_TRIAL.pdf
    .venv/bin/python tools/typeset_protocol.py --png-preview 2    # render page 2 to PNG
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "docs" / "MANGO_LEAF_TRIAL.md"
OUT = REPO / "docs" / "MANGO_LEAF_TRIAL.pdf"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

# ---------------------------------------------------------------- palette
INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5a5a5a")
RULE = colors.HexColor("#c8ccd2")
ACCENT = colors.HexColor("#0f5c8c")
ACCENT_LIGHT = colors.HexColor("#eaf2f8")
CODE_BG = colors.HexColor("#f4f5f7")
CODE_EDGE = colors.HexColor("#d8dbe0")
WARN = colors.HexColor("#b45309")
WARN_BG = colors.HexColor("#fdf6e8")
NOTE_BG = colors.HexColor("#f2f7fb")
NOTE_EDGE = colors.HexColor("#9dc0d8")
WARN_EDGE = colors.HexColor("#e0b070")
HEAD_BG = colors.HexColor("#eef1f4")
ZEBRA = colors.HexColor("#fafbfc")


# ---------------------------------------------------------------- fonts
def register_fonts() -> None:
    """Register DejaVu faces; synthesise italic by slanting (no oblique file on this box)."""
    needed = {
        "DVSans": "DejaVuSans.ttf",
        "DVSans-Bold": "DejaVuSans-Bold.ttf",
        "DVMono": "DejaVuSansMono.ttf",
        "DVMono-Bold": "DejaVuSansMono-Bold.ttf",
        "DVSerif": "DejaVuSerif.ttf",
        "DVSerif-Bold": "DejaVuSerif-Bold.ttf",
    }
    for name, fn in needed.items():
        path = FONT_DIR / fn
        if not path.exists():
            sys.exit(f"error: missing font {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    # ReportLab needs a registered family for <i>; map italic -> regular and let the tag
    # through only for emphasis we can fake with colour instead (see _inline).
    pdfmetrics.registerFontFamily(
        "DVSans", normal="DVSans", bold="DVSans-Bold", italic="DVSans", boldItalic="DVSans-Bold"
    )


def check_glyphs(text: str) -> list[tuple[str, str]]:
    """Return [(char, codepoint)] for any non-ASCII char the regular font cannot draw."""
    faces = {}
    for key, fn in (("regular", "DejaVuSans.ttf"), ("bold", "DejaVuSans-Bold.ttf"), ("mono", "DejaVuSansMono.ttf")):
        face = TTFont("probe-" + key, str(FONT_DIR / fn)).face
        faces[key] = set(face.charToGlyph)
    missing = []
    for ch in sorted({c for c in text if ord(c) > 126}):
        if not all(ord(ch) in cm for cm in faces.values()):
            missing.append((ch, f"U+{ord(ch):04X}"))
    return missing


# ---------------------------------------------------------------- inline markdown
# Order matters: code spans are protected first so ** inside them is not treated as bold.
_CODE_SPAN = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_BOLDITAL = re.compile(r"\*\*\*(.+?)\*\*\*", re.S)
_ITAL = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", re.S)


def _esc(s: str) -> str:
    return html.escape(s, quote=False)


def _inline(text: str, *, mono_size: float | None = None) -> str:
    """Convert inline Markdown to ReportLab mini-HTML.

    Order is deliberate and was a bug once: the WHOLE string is escaped first, then Markdown
    is replaced by real tags. Escaping last means a `<b>` produced by the bold pass gets
    escaped by the italic pass and appears literally on the page as "<b>20.00 wt %</b>".
    """
    text = _esc(text)

    # 1. code spans, stashed so later passes cannot touch them
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        idx = len(spans)
        size = f' size="{mono_size}"' if mono_size else ""
        spans.append(f'<font name="DVMono" color="#8a2b52"{size}>{m.group(1)}</font>')
        return f"\x00{idx}\x00"

    text = _CODE_SPAN.sub(stash, text)

    # 2. emphasis, widest marker first
    text = _BOLDITAL.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    text = _BOLD.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    # no oblique face on this box: emphasis stays roman but shifts colour, which still reads
    text = _ITAL.sub(lambda m: f'<font color="#24486b">{m.group(1)}</font>', text)

    # 3. links, last, so their labels may already carry tags. The label alone is shown:
    #    a relative path like ../nades_recipe.py is not clickable on paper.
    text = _LINK.sub(lambda m: m.group(1), text)

    # 4. restore code, then remove any asterisk that never formed a pair
    text = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)
    return text.replace("*", "")


# ---------------------------------------------------------------- styles
def build_styles() -> dict[str, ParagraphStyle]:
    base = dict(textColor=INK, alignment=TA_LEFT)
    return {
        "title": ParagraphStyle("title", fontName="DVSerif-Bold", fontSize=21, leading=25.5,
                                textColor=colors.HexColor("#0d3b5c"), spaceAfter=3 * mm),
        "subtitle": ParagraphStyle("subtitle", fontName="DVSans", fontSize=10.5, leading=15,
                                   textColor=MUTED, spaceAfter=2 * mm),
        "h2": ParagraphStyle("h2", fontName="DVSerif-Bold", fontSize=13.2, leading=16.5,
                             textColor=colors.HexColor("#0d3b5c"), spaceBefore=5.2 * mm,
                             spaceAfter=1.8 * mm),
        "h3": ParagraphStyle("h3", fontName="DVSans-Bold", fontSize=10.6, leading=13.6,
                             textColor=ACCENT, spaceBefore=3.6 * mm, spaceAfter=1.2 * mm),
        "body": ParagraphStyle("body", fontName="DVSans", fontSize=9.3, leading=13.4,
                               spaceAfter=2.1 * mm, **base),
        "bullet": ParagraphStyle("bullet", fontName="DVSans", fontSize=9.3, leading=13.4,
                                 spaceAfter=1.1 * mm, leftIndent=5.2 * mm,
                                 bulletIndent=1.2 * mm, **base),
        "number": ParagraphStyle("number", fontName="DVSans", fontSize=9.3, leading=13.4,
                                 spaceAfter=1.3 * mm, leftIndent=6.4 * mm,
                                 bulletIndent=1.0 * mm, **base),
        "callout": ParagraphStyle("callout", fontName="DVSans", fontSize=8.9, leading=12.9,
                                  spaceAfter=0, **base),
        "code": ParagraphStyle("code", fontName="DVMono", fontSize=7.5, leading=10.0,
                               textColor=colors.HexColor("#14304a"), spaceAfter=0),
        "th": ParagraphStyle("th", fontName="DVSans-Bold", fontSize=8.1, leading=10.6, **base),
        "td": ParagraphStyle("td", fontName="DVSans", fontSize=8.1, leading=10.6, **base),
        "ref": ParagraphStyle("ref", fontName="DVSans", fontSize=8.5, leading=12.4,
                              spaceAfter=1.6 * mm, **base),
    }


# ---------------------------------------------------------------- block parsing
class Block:
    def __init__(self, kind: str, payload, extra=None):
        self.kind = kind
        self.payload = payload
        self.extra = extra or {}


def strip_html_comments(text: str) -> str:
    """Drop <!-- ... --> blocks. They are notes to the build, not content, and a trailing one
    otherwise renders as an orphan page holding a single line."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def parse_markdown(lines: list[str]) -> list[Block]:
    """Turn the document's Markdown into a list of typed blocks. Unknown input raises."""
    blocks: list[Block] = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip("\n")

        if not line.strip():
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"\s*---+\s*", line):
            blocks.append(Block("hr", None))
            i += 1
            continue

        # fenced code
        if line.lstrip().startswith("```"):
            i += 1
            code: list[str] = []
            while i < n and not lines[i].lstrip().startswith("```"):
                code.append(lines[i].rstrip("\n"))
                i += 1
            if i < n:
                i += 1  # closing fence
            blocks.append(Block("code", code))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            blocks.append(Block(f"h{level}", m.group(2).strip()))
            i += 1
            continue

        # table: a header row followed by a delimiter row
        if line.strip().startswith("|") and i + 1 < n and re.match(
            r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]
        ):
            table_lines = [line]
            i += 1
            delimiter = lines[i]
            i += 1
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip("\n"))
                i += 1
            if i < n and i + 1 < n and not lines[i].strip() and lines[i + 1].strip().startswith("|"):
                raise SystemExit(
                    "malformed table: a blank line inside a table at line "
                    f"{i + 1} would leave rows as literal text - remove the blank line "
                    "(a blockquote inside a table also needs to move below the table)"
                )
            blocks.append(_parse_table(table_lines, delimiter))
            continue

        # blockquote -> one callout
        if line.lstrip().startswith(">"):
            quote: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]).rstrip("\n"))
                i += 1
            while quote and not quote[-1].strip():
                quote.pop()
            blocks.append(Block("callout", quote))
            continue

        # bullets
        if re.match(r"^\s*[-*]\s+", line):
            indent = len(line) - len(line.lstrip())
            items: list[tuple[str, str]] = []
            while i < n:
                cur = lines[i].rstrip("\n")
                mb = re.match(r"^(\s*)[-*]\s+(.*)$", cur)
                if mb:
                    items.append((mb.group(1), mb.group(2)))
                    i += 1
                elif cur.strip() and not cur.lstrip().startswith(("|", "#", ">", "```")) \
                        and len(cur) - len(cur.lstrip()) >= 2:
                    # continuation line belongs to the previous bullet
                    prev_indent, prev_text = items[-1]
                    items[-1] = (prev_indent, prev_text + " " + cur.strip())
                    i += 1
                else:
                    break
            # a list entry ending in '|' would be a table; we do not have any
            blocks.append(Block("ul", items))
            continue

        # ordered list
        if re.match(r"^\s*\d+[.)]\s+", line):
            items: list[tuple[str, str]] = []
            while i < n:
                cur = lines[i].rstrip("\n")
                mo = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", cur)
                if mo:
                    items.append((mo.group(2), mo.group(3)))
                    i += 1
                elif cur.strip() and not cur.lstrip().startswith(("|", "#", ">", "```")) \
                        and len(cur) - len(cur.lstrip()) >= 2:
                    num, prev_text = items[-1]
                    items[-1] = (num, prev_text + " " + cur.strip())
                    i += 1
                else:
                    break
            blocks.append(Block("ol", items))
            continue

        # paragraph: consume until a blank line or the start of another block
        para: list[str] = [line.strip()]
        i += 1
        while i < n:
            cur = lines[i].rstrip("\n")
            if not cur.strip():
                break
            if re.match(r"^(#{1,6})\s+", cur) or cur.lstrip().startswith(("```", ">")) \
                    or re.fullmatch(r"\s*---+\s*", cur) \
                    or re.match(r"^\s*[-*]\s+", cur) or re.match(r"^\s*\d+[.)]\s+", cur) \
                    or (cur.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|", lines[i + 1])):
                break
            para.append(cur.strip())
            i += 1
        blocks.append(Block("p", " ".join(para)))

    return blocks


def _parse_table(rows: list[str], delimiter: str) -> Block:
    def cells(row: str) -> list[str]:
        s = row.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        # no escaped pipes in this document; a simple split is correct
        return [c.strip() for c in s.split("|")]

    header = cells(rows[0])
    aligns = []
    for spec in cells(delimiter):
        spec = spec.strip()
        if spec.startswith(":") and spec.endswith(":"):
            aligns.append("CENTER")
        elif spec.endswith(":"):
            aligns.append("RIGHT")
        else:
            aligns.append("LEFT")
    body = [cells(r) for r in rows[1:]]
    ncol = len(header)
    for r in body:
        if len(r) != ncol:
            raise SystemExit(f"table row has {len(r)} cells, header has {ncol}: {r}")
    return Block("table", body, {"header": header, "aligns": aligns})


# ---------------------------------------------------------------- flowables
class Callout(Flowable):
    """A blockquote drawn as a boxed callout with an optional label."""

    def __init__(self, paras: list[Paragraph], label: str | None, width: float,
                 bg, edge, label_color):
        super().__init__()
        self.paras = paras
        self.label = label
        self._w = width
        self.bg = bg
        self.edge = edge
        self.label_color = label_color

    def wrap(self, availWidth, availHeight):
        self._w = availWidth
        pad = 2.6 * mm
        inner = availWidth - 2 * pad - 1.2 * mm
        total = 0.0
        for p in self.paras:
            w, h = p.wrap(inner, availHeight)
            total += h
        self._inner_h = total
        self._pad = pad
        return availWidth, total + 2 * pad

    def draw(self):
        c = self.canv
        h = self._inner_h + 2 * self._pad
        c.setFillColor(self.bg)
        c.setStrokeColor(self.edge)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, self._w, h, 1.6 * mm, stroke=1, fill=1)
        c.setFillColor(self.label_color)
        c.rect(0, 0, 1.1 * mm, h, stroke=0, fill=1)
        y = h - self._pad
        for p in self.paras:
            w, ph = p.wrap(self._w - 2 * self._pad - 1.2 * mm, h)
            p.drawOn(c, self._pad + 1.1 * mm, y - ph)
            y -= ph


def _outline_text(markdown_heading: str) -> str:
    """Strip inline markers for the bookmark label (no markup allowed in the panel)."""
    text = re.sub(r"`([^`]+)`", r"\1", markdown_heading)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def _join_split_code_spans(lines: list[str]) -> list[str]:
    """Re-join a `code span` that a line wrap in the source split across two lines.

    Markdown itself does not care (a backtick span may cross a newline), but this renderer
    draws each quote line as its own paragraph, so a single unmatched backtick would show up
    as a literal character. Joining only the affected lines fixes that without disturbing the
    rest of the quote's line structure.
    """
    out: list[str] = []
    carry: str | None = None
    for raw in lines:
        line = raw if carry is None else carry + " " + raw.strip()
        carry = None
        if line.count("`") % 2 == 1:
            carry = line
            continue
        out.append(line)
    if carry is not None:  # unmatched at the end: leave it as-is rather than lose the text
        out.append(carry)
    return out


def callout_flowable(quote_lines: list[str], width: float, styles) -> Callout:
    quote_lines = _join_split_code_spans(quote_lines)
    text = "\n".join(quote_lines).strip()
    label, color, bg, edge = None, ACCENT, NOTE_BG, NOTE_EDGE
    if "⚠" in text:
        label, color, bg, edge = "CORRECTION", WARN, WARN_BG, WARN_EDGE
    paragraphs = []
    for chunk in [c for c in text.split("\n") if c.strip()]:
        paragraphs.append(Paragraph(_inline(chunk, mono_size=7.6), styles["callout"]))
    return Callout(paragraphs, label, width, bg, edge, color)


def code_flowable(code_lines: list[str], width: float, styles) -> Table:
    text = "<br/>".join(
        _esc(l).replace(" ", "&nbsp;") if l.strip() else "&nbsp;" for l in code_lines
    )
    para = Paragraph(text, styles["code"])
    t = Table([[para]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, CODE_EDGE),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4 * mm),
    ]))
    return t


def _col_widths(header, body, width: float, pad_mm: float = 4.0) -> list[float]:
    """Size table columns from measured text, not from a guess.

    An earlier version used "does this column look numeric?" to give numbers a narrow share.
    That misfired on a "5 mg" column (digits and unit letters read as numeric), squeezing the
    header into a 15 pt sliver that wrapped one letter per line. Measuring the longest WORD
    per column and treating that as a hard minimum makes the failure impossible: a column can
    never be narrower than its widest word.
    """
    ncol = len(header)
    body_font, head_font = "DVSans", "DVSans-Bold"
    size = 8.1
    pad = pad_mm * mm  # total horizontal padding the TableStyle will apply to a cell

    def words(cell: str) -> list[str]:
        plain = re.sub(r"[`*\[\]]|\([^)]*\)", " ", str(cell))
        return plain.split()

    floor, want = [], []
    for c in range(ncol):
        col_cells = [str(r[c]) for r in body] + [str(header[c]).replace("*", "")]
        # HARD FLOOR: the widest single word plus the cell padding, so no word is ever broken
        # ("Value" must not become "Valu/e"). Whole-cell width is the wrong floor - it forces
        # long paragraphs onto one line and, summed across columns, exceeds the page. A +0.4 pt
        # epsilon absorbs float rounding, nothing more; giving up width here caused mid-word
        # breaks when tried.
        widest_word = max(
            (pdfmetrics.stringWidth(w, head_font, size) for cell in col_cells for w in words(cell)),
            default=size,
        )
        floor.append(widest_word + pad + 0.4)

        # DESIRE: everything on one line, capped, so wide text columns get the extra room
        widest_cell = max(
            (pdfmetrics.stringWidth(" ".join(words(cell)), body_font, size) for cell in col_cells),
            default=size,
        )
        want.append(min(widest_cell + pad, width * 0.42))

    want = [max(f, w) for f, w in zip(floor, want)]

    if sum(floor) > width:  # pathological: shrink floors proportionally
        k = width / sum(floor)
        floor = [f * k for f in floor]
        want = [w * k for w in want]

    spare = width - sum(floor)
    stretch = [max(0.0, w - f) for f, w in zip(floor, want)]
    total_stretch = sum(stretch)
    if total_stretch <= 0:
        # nobody wants more: split the spare evenly
        return [f + spare / ncol for f in floor]
    out = [f + spare * (st / total_stretch) for f, st in zip(floor, stretch)]
    out[-1] += width - sum(out)  # absorb float rounding into the last column
    return out


def table_flowable(header, body, aligns, width: float, styles) -> Table:
    col_w = _col_widths(header, body, width)

    data = [[Paragraph(_inline(h, mono_size=7.2), styles["th"]) for h in header]]
    for row in body:
        data.append([Paragraph(_inline(c, mono_size=7.2), styles["td"]) for c in row])

    t = Table(data, colWidths=col_w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.0 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.0 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.7 * mm),
    ]
    for c, a in enumerate(aligns):
        style.append(("ALIGN", (c, 0), (c, -1), a))
    for r in range(1, len(data)):
        if r % 2 == 0:
            style.append(("BACKGROUND", (0, r), (-1, r), ZEBRA))
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------- page furniture
class OutlineDoc(BaseDocTemplate):
    """DocTemplate that also builds the PDF bookmark panel from the headings.

    A 12-page bench protocol gets read on a phone or scrolled through for one section; the
    outline is what makes that bearable, so headings register themselves here.
    """

    def afterFlowable(self, flowable):
        entry = getattr(flowable, "_outline", None)
        if not entry:
            return
        level, text, key = entry
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)


def make_doc(path: Path, footer_text: str, doc_title: str) -> BaseDocTemplate:
    """`footer_text` / `doc_title` come from the source document, never hardcoded.

    They used to be fixed strings, so rendering a second document (TRIAL_RUNSHEET.md) put the
    first document's title in the footer and the PDF metadata - an error a reader sees on
    every page.
    """
    doc = OutlineDoc(
        str(path), pagesize=A4,
        leftMargin=17 * mm, rightMargin=17 * mm, topMargin=18 * mm, bottomMargin=17 * mm,
        title=doc_title,
        author="extractlab", subject="beta-alanine / citric acid / water NADES, 1:1 molar, 20 wt% water",
        creator="tools/typeset_protocol.py",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def footer(canv, d):
        canv.saveState()
        canv.setFont("DVSans", 7.2)
        canv.setFillColor(MUTED)
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.5)
        y = d.bottomMargin - 6.5 * mm
        canv.line(d.leftMargin, y + 3.4 * mm, d.leftMargin + d.width, y + 3.4 * mm)
        canv.drawString(d.leftMargin, y, footer_text)
        canv.drawRightString(d.leftMargin + d.width, y, f"page {d.page}")
        canv.restoreState()

    doc.addPageTemplates([PageTemplate(id="body", frames=[frame], onPage=footer)])
    return doc


# ---------------------------------------------------------------- build
def build(src: Path = SRC, out: Path = OUT) -> Path:
    register_fonts()
    styles = build_styles()
    text = src.read_text(encoding="utf-8")

    missing = check_glyphs(text)
    if missing:
        raise SystemExit("error: font cannot render: " + ", ".join(f"{c} {cp}" for c, cp in missing))

    blocks = parse_markdown(strip_html_comments(text).splitlines())

    # title = first h1, used for the footer and the PDF metadata
    doc_title = next((b.payload for b in blocks if b.kind == "h1"), src.stem)
    footer = _outline_text(doc_title)
    if len(footer) > 105:
        footer = footer[:102].rstrip() + "..."
    doc = make_doc(out, footer, footer)
    width = doc.width

    story: list = []
    title_done = False
    for idx, b in enumerate(blocks):
        # ---- title page furniture (first h1 + the metadataline under it)
        if b.kind == "h1" and not title_done:
            title_done = True
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(_inline(b.payload), styles["title"]))
            story.append(HRFlowable(width="100%", thickness=1.6, color=ACCENT,
                                    spaceBefore=1 * mm, spaceAfter=2.5 * mm))
            continue

        if b.kind == "h1":
            story.append(PageBreak())
            story.append(Paragraph(_inline(b.payload), styles["title"]))
            continue
        if b.kind == "h2":
            h = Paragraph(_inline(b.payload), styles["h2"])
            h._is_heading = True
            h._outline = (0, _outline_text(b.payload), f"h2-{idx}")
            story.append(h)
            d = HRFlowable(width="100%", thickness=0.7, color=RULE,
                           spaceBefore=0.4 * mm, spaceAfter=2.0 * mm)
            d._is_filler = True
            story.append(d)
            continue
        if b.kind == "h3":
            h = Paragraph(_inline(b.payload), styles["h3"])
            h._is_heading = True
            h._outline = (1, _outline_text(b.payload), f"h3-{idx}")
            story.append(h)
            continue
        if b.kind in ("h4", "h5", "h6"):
            story.append(CondPageBreak(14 * mm))
            story.append(Paragraph(_inline(b.payload), styles["h3"]))
            continue

        if b.kind == "p":
            st = styles["subtitle"] if not story or idx == 1 else styles["body"]
            # the two italic metadata lines directly under the title read as a subtitle
            if idx <= 2 and b.payload.startswith("*") and "companion code" in b.payload:
                st = styles["subtitle"]
            story.append(Paragraph(_inline(b.payload), st))
            continue

        if b.kind == "ul":
            for indent, item in b.payload:
                story.append(Paragraph(_inline(item), styles["bullet"], bulletText="•"))
            story.append(Spacer(1, 1.2 * mm))
            continue

        if b.kind == "ol":
            for num, item in b.payload:
                story.append(Paragraph(_inline(item), styles["number"], bulletText=f"{num}."))
            story.append(Spacer(1, 1.2 * mm))
            continue

        if b.kind == "code":
            story.append(Spacer(1, 1 * mm))
            story.append(code_flowable(b.payload, width, styles))
            story.append(Spacer(1, 2.4 * mm))
            continue

        if b.kind == "callout":
            story.append(Spacer(1, 1.2 * mm))
            story.append(KeepTogether([callout_flowable(b.payload, width, styles)]))
            story.append(Spacer(1, 2.6 * mm))
            continue

        if b.kind == "table":
            story.append(Spacer(1, 1.0 * mm))
            story.append(table_flowable(b.extra["header"], b.payload, b.extra["aligns"], width, styles))
            story.append(Spacer(1, 2.6 * mm))
            continue

        if b.kind == "hr":
            story.append(Spacer(1, 1.5 * mm))
            story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=1.5 * mm))
            continue

        raise SystemExit(f"unhandled block kind {b.kind!r}: {b.payload!r}")

    doc.build(_glue_headings(story))
    return out


def _glue_headings(story: list) -> list:
    """Keep a heading with the first block after it, so a section never starts as a widow.

    Page 11 of the first draft ended with the "10. What to write in the progress report"
    heading and a single line, with the actual text overleaf - the kind of thing that reads
    as a mistake. Gluing the heading, its rule and the following block together means the
    heading moves to the next page instead. Tables are NOT glued: one taller than the page
    cannot be kept whole, and forcing it would push an entire table to a fresh page for no
    benefit.
    """
    out: list = []
    i = 0
    while i < len(story):
        item = story[i]
        if getattr(item, "_is_heading", False):
            group = [item]
            j = i + 1
            while j < len(story) and getattr(story[j], "_is_filler", False):
                group.append(story[j])
                j += 1
            # glue the next block, unless it is a table (too tall to keep whole safely) or a
            # horizontal rule (the closing rule would then be what gets orphaned onto a page
            # of its own - exactly what happened to DAY2.pdf's final disclaimer line)
            if (j < len(story)
                    and not isinstance(story[j], Table)
                    and not isinstance(story[j], HRFlowable)):
                group.append(story[j])
                j += 1
            out.append(KeepTogether(group))
            i = j
        else:
            out.append(item)
            i += 1

    return out


def png_preview(pdf: Path, page: int, out: Path, dpi: int = 110) -> Path:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    pg = doc[page - 1]
    pg.render(scale=dpi / 72).to_pil().save(out)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--png-preview", type=int, metavar="PAGE",
                    help="also render this 1-based page to a PNG next to the PDF")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args(argv)

    out = build(args.src, args.out)
    size_kb = out.stat().st_size / 1024
    import pypdf

    pages = len(pypdf.PdfReader(str(out)).pages)
    print(f"wrote {out}  ({pages} pages, {size_kb:.0f} KB)")

    if args.png_preview:
        png = out.with_name(f"{out.stem}-p{args.png_preview}.png")
        png_preview(out, args.png_preview, png, args.dpi)
        print(f"preview {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
