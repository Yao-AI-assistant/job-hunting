#!/usr/bin/env python
"""markdown -> 简历 docx(可带证件照、可自动压到指定页数、可顺带导 PDF)。

比 md2docx.py 多三件事:
  1. 右上角放一张证件照(无边框两列表格,不破坏 ATS 的可读性);
  2. --pages N:自动在一段字号区间里试,找到「刚好不超过 N 页」的最大字号,
     不用人肉反复调;页数靠 Word / WPS 的 COM 接口数,没有 COM 就跳过这一步;
  3. --pdf:连着导一份 PDF(同样走 COM)。

用法:
  python build_resume_docx.py <投递版.md> [输出.docx]
        [--photo 证件照.png] [--pages 2] [--body 9.5] [--min 8.0] [--pdf]

markdown 标记与 md2docx.py 一致:
  # 姓名 / ## 小节 / - 条目 /   - 子条目 / **粗体** / 第一个 ## 之前的行当联系方式
"""
import argparse
import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = '微软雅黑'
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
GRAY = RGBColor(0x55, 0x55, 0x55)
BODY = RGBColor(0x22, 0x22, 0x22)


def set_font(run, size, bold=False, color=BODY):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia'):
        rfonts.set(qn(attr), FONT)


def add_runs(p, text, size, color=BODY, base_bold=False):
    for i, seg in enumerate(re.split(r'\*\*(.+?)\*\*', text)):
        if not seg:
            continue
        set_font(p.add_run(seg), size, bold=base_bold or (i % 2 == 1), color=color)


def bottom_border(p, color='1F4E79'):
    ppr = p._p.get_or_add_pPr()
    borders = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '8')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color)
    borders.append(bottom)
    ppr.append(borders)


def read_md(path):
    with open(path, encoding='utf-8') as f:
        return [ln.rstrip() for ln in f.read().splitlines()]


def split_md(lines):
    """-> (姓名, [联系方式行], [(小节标题, [条目...])])"""
    name, contact, sections = '', [], []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith('# ') and not name:
            name = s[2:].strip()
        elif s.startswith('## '):
            sections.append((s[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
        elif name:
            contact.append(s)
    return name, contact, sections


def build(md_path, out_path, photo=None, body=9.5, photo_cm=3.0):
    name, contact, sections = split_md(read_md(md_path))

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.6)
    sec.top_margin = Cm(1.3)
    sec.bottom_margin = Cm(1.2)

    normal = doc.styles['Normal']
    normal.font.name = FONT
    normal.font.size = Pt(body)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    # ---- 抬头 ----
    if photo:
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        left, right = tbl.rows[0].cells
        left.width = Cm(21.0 - 3.2 - photo_cm)
        right.width = Cm(photo_cm + 0.4)
        head = left
        rp = right.paragraphs[0]
        rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rp.add_run().add_picture(photo, width=Cm(photo_cm))
    else:
        head = doc

    def head_para(first=False, space_after=1.0):
        p = head.paragraphs[0] if (first and hasattr(head, 'paragraphs')) else head.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        return p

    p = head_para(first=True, space_after=2)
    set_font(p.add_run(name), body + 12.5, bold=True, color=ACCENT)

    for i, line in enumerate(contact):
        if not line:
            continue
        p = head.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        # 含「求职意向」的行加粗一点,当作定位句
        strong = '求职意向' in line
        add_runs(p, line, body - 0.5, color=(RGBColor(0x33, 0x33, 0x33) if strong else GRAY), base_bold=strong)

    # ---- 正文 ----
    for title, body_lines in sections:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(2)
        bottom_border(p)
        set_font(p.add_run(title), body + 2.0, bold=True, color=ACCENT)

        for raw in body_lines:
            m = re.match(r'^(\s*)-\s+(.*)$', raw)
            if m:
                depth = len(m.group(1)) // 2
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent = Cm(0.46 + 0.5 * depth)
                pf.first_line_indent = Cm(-0.46)
                pf.space_after = Pt(1.5)
                pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
                set_font(p.add_run('· ' if depth == 0 else '– '), body, color=ACCENT)
                add_runs(p, m.group(2), body)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(1.5)
                p.paragraph_format.space_after = Pt(1.5)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                add_runs(p, raw.strip(), body, base_bold=True)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    doc.save(out_path)
    return out_path


_PS = r'''
$ErrorActionPreference = 'Stop'
$src = '{src}'
$app = $null
foreach ($prog in @('KWPS.Application','Word.Application')) {{
  try {{ $app = New-Object -ComObject $prog; $app.Visible = $false; break }} catch {{ }}
}}
if ($app -eq $null) {{ 'NOCOM'; exit 0 }}
$doc = $app.Documents.Open($src, $false, $true)
try {{
  if ('{mode}' -eq 'pages') {{ $doc.ComputeStatistics(2) }}
  else {{ $doc.ExportAsFixedFormat('{pdf}', 17); 'OK' }}
}} finally {{
  $doc.Close(0); $app.Quit()
}}
'''


def _ps(mode, path, pdf=''):
    """用 PowerShell 走 COM 数页数 / 导 PDF;机器上没有 Word/WPS 就返回 None。"""
    import subprocess
    import tempfile
    if os.name != 'nt':
        return None
    script = _PS.format(src=os.path.abspath(path).replace("'", "''"),
                        mode=mode, pdf=pdf.replace("'", "''"))
    with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False, encoding='utf-8-sig') as f:
        f.write(script)
        tmp = f.name
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', tmp],
                             capture_output=True, text=True, timeout=180).stdout.strip()
    except Exception:
        return None
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if not out or out == 'NOCOM':
        return None
    return out


def page_count(path):
    out = _ps('pages', path)
    try:
        return int(out)
    except (TypeError, ValueError):
        return None


def export_pdf(path, pdf_path):
    return _ps('pdf', path, os.path.abspath(pdf_path)) == 'OK'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst', nargs='?')
    ap.add_argument('--photo', default=None, help='证件照 png/jpg,放在右上角')
    ap.add_argument('--pages', type=int, default=0, help='目标页数上限,自动挑最大可容纳字号')
    ap.add_argument('--body', type=float, default=9.5, help='起始正文字号(pt)')
    ap.add_argument('--min', dest='min_pt', type=float, default=8.0)
    ap.add_argument('--pdf', action='store_true')
    a = ap.parse_args()

    dst = a.dst or os.path.splitext(a.src)[0] + '.docx'

    size = a.body
    build(a.src, dst, a.photo, size)
    if a.pages:
        while size > a.min_pt:
            n = page_count(dst)
            if n is None:
                print('没有 Word/WPS(COM),跳过页数自适应')
                break
            if n <= a.pages:
                print('body=%.1fpt pages=%d' % (size, n))
                break
            size = round(size - 0.3, 1)
            build(a.src, dst, a.photo, size)

    if a.pdf:
        pdf = os.path.splitext(dst)[0] + '.pdf'
        print('pdf ->', pdf if export_pdf(dst, pdf) else '导出失败(没有 Word/WPS)')

    print('OK', dst)
    return 0


if __name__ == '__main__':
    sys.exit(main())
