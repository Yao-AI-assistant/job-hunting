# job-hunting

一套国内社招的**求职流水线**,不是简历模板合集,也不是自动投递机。

```
采岗 → 按证据评分 → 5–6 个的短清单 → 本人点头 → 定向改稿 → 导 docx → 本人投
```

拆成七步,每步的产物都落成文件——所以中途换模型、换人接手,都不用从头再来。

## 三条不可协商

1. **人是决策者。** AI 只做证据对齐和缺口清单,不替你选公司、不替你判「值不值得去」。
2. **事实不许编。** 只引用有来源的事实;你自己撤回过的内容,不许写回去。
3. **投递不可逆,永远是本人点。** 不自动投递、不打招呼语、不代填表单、不绕验证码。

## 它长这样

```
job-hunting/
├── SKILL.md                          流程总纲(先看这个)
├── references/
│   ├── scoring-method.md             评分:拆 JD、证据分级、1–5 分怎么给
│   ├── evidence-rules.md             事实底线:已实现 / 已验证 / 本人完成、撤回机制
│   ├── resume-rewrite.md             定向改简历五步与禁令
│   ├── resume-output.md              交付:Markdown 主版本 → docx,版式与自查
│   └── platforms-and-endpoints.md    平台接口、城市码、限流节奏
├── scripts/
│   ├── boss-search.js                在页面上下文里跑的结构化采岗脚本
│   ├── docx2md.py                    docx → 文本(文本框兜底)
│   └── md2docx.py                    Markdown → docx(简历版式)
├── templates/
│   ├── job-eval-template.md          单条岗位评分格式
│   └── daily-list-template.md        每日清单格式
├── CHANGELOG.md                      版本说明 + 已知瓶颈
└── LICENSE                           MIT
```

## 安装

安装 = **把整个目录搬进去**,没有安装脚本。任何「会扫技能目录」的 agent 都适用。

**DeepSeek Harness(DSH)**:放进用户级技能根目录,一次装好、所有项目可用。

```bash
# 用户级(推荐)
git clone <本仓库地址> ~/.dsh/skills/job-hunting     # Windows 下是 %USERPROFILE%\.dsh\skills\job-hunting

# 或者项目级:只在这个项目生效
git clone <本仓库地址> <项目根>/.dsh/skills/job-hunting
```

**别的编码 agent**(Claude Code / Codex / Cursor 等):放 `~/.agents/skills/job-hunting/`,或者直接把仓库丢给它,说「读一下 SKILL.md,按里面的流程带我走」。

**手机 / 网页上的对话式 AI**(没有文件系统):上传 `SKILL.md` + `references/` 下 5 个 md,第一句固定成「你现在按 SKILL.md 的流程来,先问我求职条件,不要直接改简历」。

三个最容易踩的坑:

| 坑 | 表现 | 正确做法 |
|---|---|---|
| 多套一层文件夹 | `skills/job-hunting/job-hunting/SKILL.md` | `SKILL.md` 的父目录就是技能本身 |
| 只搬了 SKILL.md | 能加载,一用就说「没有这个脚本」 | `references/` `scripts/` `templates/` 必须同级一起搬 |
| 递归找 SKILL.md | 塞进深目录 | 多数 agent 只认根目录下一层 |

依赖:Python 3.10+ 与 `pip install python-docx pypdf`(只有 docx 转换用得上);采岗脚本要求 agent 有浏览器控制能力,没有的话把页面 JSON 存成文件喂给它,后面几步照样能走。

## 装好之后

先写两份自己的底稿,否则它没有事实可对齐:

1. **证据库**——你真正做过的事,一条一条,带来源(项目、时间、你具体做了什么、结果是什么)。
2. **求职条件**——城市、方向、年限、薪资底线。

然后这样说:「帮我找 XX 方向的岗位」「这个 JD 值不值得投」「简历改成投这家」。

**第一次只跑一条 JD**,从评分走到 docx,把链路验一遍再批量。批量采岗守规矩:**半小时一批、一批 10 条,请求之间隔 8 秒**——这条是被人家的封 IP 换来的,别调快。

## 已知瓶颈

- **导出的简历版式还不好看**:字体、段距、边距是写死的常量,内容一长一短就容易挤或空,两栏和中英文混排没专门处理。近期会做成可切换模板。
- **只能导 docx,导不了 PDF**:得靠 LibreOffice / Word 另存。
- **采岗强依赖平台搜索接口**:接口、字段、城市码随时会变,限流阈值也在变。
- **评分质量取决于证据库质量**:证据写成「参与了项目」,分就只能给得含糊。

详见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

流程骨架参考了两个开源项目的思路(**只用思路,未复制代码**):

- **career-ops** ——硬要求 → 证据 → 缺口 的评估方法论。
- **resume-evidence-workflow** ——经历盘点 → JD 与证据矩阵 → 定向改写。

## 许可

MIT。见 [LICENSE](LICENSE)。第三方平台的接口与规则归各平台,使用前自行确认合规。
