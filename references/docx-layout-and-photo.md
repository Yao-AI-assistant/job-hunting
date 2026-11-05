# 版式:证件照、页数自适应、模板怎么「抄样子不抄内容」

`scripts/md2docx.py` 是「能用」的版本;要更像一份正经投递件,用 `scripts/build_resume_docx.py`。

## 它多做了三件事

```bash
py scripts/build_resume_docx.py jobs/XX-简历-投递版.md jobs/XX-简历.docx \
   --photo 证件照.png --pages 2 --body 10.0 --pdf
```

| 参数 | 作用 |
|---|---|
| `--photo` | 右上角放证件照。用的是**无边框两列表格**(左列放姓名+联系方式,右列放照片),比浮在文字上层的浮动图片稳,ATS 读得出来。 |
| `--pages N` | 从 `--body` 开始,每 0.3pt 往下试,直到页数 ≤ N,拿下最大的那个字号。**人肉调字号的活就到这儿了。** |
| `--pdf` | 顺带导一份 PDF。 |

页数和 PDF 都靠 **Word / WPS 的 COM**(Windows):
先找 `KWPS.Application`(WPS),找不到再找 `Word.Application`;都没有就跳过自适应,只出 docx,不会报错中断。
脚本走 PowerShell 调 COM,所以**不需要装 pywin32**;非 Windows 上这一步自动跳过(LibreOffice 用户自己 `--convert-to pdf`)。

## 一页还是两页

- **一页不是硬指标。** 一页挤到 8pt、行距像报纸,读的人第一眼就累了;正式工龄短、项目多的简历,两页 9.5–10pt 读起来比一页 8pt 舒服得多。
- 先定页数上限,再让脚本去挤字号;`--pages 1` 只在「真的没内容可删」时才用。
- 经验线:正文 **9.5–10pt**、小节标题 +2pt、行距单倍,两页以内一般都能排下来。低于 8.5pt 就别再压了,**删内容**。

## 模板:抄样子,不抄内容

网上下载的「简历模板精选」大多是**带样例内容的排版文件**——里面是别人的学历、经历、甚至整页是图片。直接往里填等于用别人的事实打底。做法:

1. 拆开 docx,看它**版式参数**:纸张、页边距、分节线颜色与粗细、条目缩进、照片尺寸与位置。
2. 用 `build_resume_docx.py` 按这些参数重排自己的内容,**一个字都不从模板里搬**。
3. 模板里的照片同理:只用本人的。

```powershell
# 拆 docx 看结构和图片(Windows PowerShell)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead('模板.docx')
$e=$zip.Entries | ? { $_.FullName -eq 'word/document.xml' }
$sr=New-Object IO.StreamReader($e.Open()); $xml=$sr.ReadToEnd(); $sr.Close(); $zip.Dispose()
[regex]::Replace([regex]::Replace($xml,'</w:p>',"`n"),'<[^>]+>','')
```

## 内容一致性自查(比版式更容易翻车)

简历里**项目和成果必须对得上**。项目写「成果产出 SCI 2 篇」,成果栏只列 2 篇 —— 那就要问:另外几条项目说的论文在哪?

三种处理,按诚实程度排:

1. **补全**:把其余论文也列上(不知道题目就去问人要,别自己编)。
2. **降级表述**:项目里改成「相关成果合作发表于 SCI 期刊(见科研成果)」,不再报篇数。
3. **只留能被追认的**:没有可查来源的成果,宁可不提。

**不要**在成果栏留空、项目里却说「产出 N 篇」——面试一问「哪几篇」就露了。

## 回读校验

导出之后仍然要回读一遍(`scripts/docx2md.py`),确认没有乱码、没有空段落、没有掉字;页数自适应只保证「塞得下」,不保证「没排丢」。
