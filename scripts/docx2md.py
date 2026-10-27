#!/usr/bin/env python
"""docx -> markdown 纯文本(给 agent 自己读用)。

用法:
  python docx2md.py <输入.docx> [输出.md]

不写输出路径时,输出到同目录 <名字>.auto.md。
普通文档走段落/表格映射;内容全在文本框里时(简历常见)自动切 XML 兜底。
"""
import sys
import os
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    from docx.oxml.ns import qn
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


def run_text(run):
    t = run.text
    if not t.strip():
        return t
    if run.bold and run.italic:
        return f"***{t}***"
    if run.bold:
        return f"**{t}**"
    if run.italic:
        return f"*{t}*"
    return t


def para_md(p):
    text = ''.join(run_text(r) for r in p.runs).rstrip()
    style = (p.style.name or '').lower()
    if not text.strip():
        return ''
    if style.startswith('heading'):
        lvl = ''.join(ch for ch in style if ch.isdigit()) or '1'
        return f"{'#' * min(int(lvl), 6)} {text.strip()}"
    if style.startswith('title'):
        return f"# {text.strip()}"
    if 'list' in style:
        return f"- {text.strip()}"
    return text


def table_md(tbl):
    rows = []
    for row in tbl.rows:
        cells = []
        for c in row.cells:
            cells.append(' '.join(pp.text.strip() for pp in c.paragraphs).replace('|', '\\|'))
        rows.append('| ' + ' | '.join(cells) + ' |')
    if not rows:
        return ''
    head = rows[0]
    sep = '| ' + ' | '.join(['---'] * (head.count('|') - 1)) + ' |'
    return '\n'.join([head, sep] + rows[1:])


def xml_fallback(src):
    """按文档顺序扫所有 <w:t>,遇到 </w:p> 断行。文本框、表格嵌套都读得到,相邻重复行去重。"""
    import re
    import zipfile
    from html import unescape
    lines = []
    with zipfile.ZipFile(src) as z:
        names = [n for n in z.namelist()
                 if re.match(r'word/(document|header\d*|footer\d*)\.xml$', n)]
        for n in sorted(names):
            xml = z.read(n).decode('utf-8', 'ignore')
            chunks = []
            pos = 0
            for m in re.finditer(r'</(?:w:)?p>', xml):
                seg = xml[pos:m.start()]
                txt = ''.join(re.findall(r'<(?:w:)?t(?:\s[^>]*)?>(.*?)</(?:w:)?t>', seg, flags=re.S))
                txt = unescape(txt).strip()
                if txt:
                    chunks.append(txt)
                pos = m.end()
            lines.extend(chunks)
    dedup = []
    for c in lines:
        if not dedup or dedup[-1] != c:
            dedup.append(c)
    return '\n'.join(dedup)


def main():
    if len(sys.argv) < 2:
        print('用法: python docx2md.py <输入.docx> [输出.md]')
        return 2
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '.auto.md'
    doc = Document(src)
    out = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            md = para_md(block)
            if md:
                out.append(md)
        else:
            md = table_md(block)
            if md:
                out.append(md)
                out.append('')
    text = '\n\n'.join(out).replace('\n\n\n', '\n\n')
    if len(text.strip()) < 50:
        text = xml_fallback(src)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'OK {dst} {len(text)} chars')
    return 0


if __name__ == '__main__':
    sys.exit(main())
