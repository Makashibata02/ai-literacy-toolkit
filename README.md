# AI 信息素养比赛速查

遇到需要查数据库、看平台界面或核对统计数据的题目，可以在这里找到对应的入口、检索步骤和证据位置。你可以直接搜索，也可以把资料交给 Agent，让它按步骤帮你查。

[打开在线速查](https://makashibata02.github.io/ai-literacy-toolkit/) · [下载资料包](https://github.com/Makashibata02/ai-literacy-toolkit/releases/latest)

## 备考更新（收录 2026-10-16）

### 模块 14：药监局数据查询入口变更

知识模块 14：国家药品监督管理局数据查询系统网址已变更，请使用新入口开展药品、化妆品和医疗器械检索。

更新后入口：[https://datasearch.nmpa.gov.cn/datasearch/home-index.html](https://datasearch.nmpa.gov.cn/datasearch/home-index.html)

请提前在浏览器中测试新入口；站内查询功能尚未实测。

来源：用户提供的赛事通知，第 2 条；收录日期：2026-10-16。

### 模块 25：国家社科基金项目数据库条目免备考

国家社科基金项目数据库已无法正常访问。本次省赛淘汰赛不再设置该知识点相关考题，无需针对该条目备考。仅适用于国家社科基金项目数据库，不代表模块 25 全部免考；国家自然科学基金等其他条目不受此通知影响。

来源：用户提供的赛事通知，第 3 条；收录日期：2026-10-16。

## 打开速查页面

1. 打开上面的在线速查；也可以下载 `toolkit-full.zip`，解压后双击 `index.html`。阅读和搜索都不用安装软件。
2. 输入“平台名 + 想做的操作”，例如 `CNKI 高级检索`、`标准 ICS 分类`、`报告 词频`。
3. 打开操作卡，按卡片中的输入条件、操作步骤和核对项，到对应平台查找。
4. 想找相似题时，切换到“相似题”；想按范围浏览时，打开“50 个模块”。

查文献数量或排名时，先看清题目限定的年份、文献类型、字段和排序指标，再读取当前结果。

## 让 Agent 帮你查

把 [仓库链接](https://github.com/Makashibata02/ai-literacy-toolkit) 发给能够浏览网页的 Agent，无需先下载。复制下面这段提示，让它先告诉你需要准备什么，再辅助查题：

```text
请读取这个仓库的 README、agent/START_HERE.md 和相关操作卡、平台档案：
https://github.com/Makashibata02/ai-literacy-toolkit

先阅读 README 中的备考更新及 docs/competition.md，按通知适用的赛次和条目安排备考，使用更新后的入口。

先给我一份准备清单：相关网站的官方入口、哪些功能需要提前注册登录、
是否需要校园网或 CARSI，以及建议提前试用的操作。区分公开查询和需账号的功能。

之后我会发送题干和选项。请优先联网搜索，先查官方页面、数据库和原始文档；
用仓库辅助定位平台和检索方法，不要直接把历史答案或候选提示当作当前答案。

请辅助我核对选项，列出建议选项及文字、证据链接、查询条件和核对日期。
数量、排名和界面功能要按题目条件实查。需要登录或验证码时，告诉我入口和操作，等待我完成。
找不到可靠证据时说明还缺什么；不要编造来源，也不要代我提交答案。

如果不能读取链接，请说明，我会提供相关文件。
```

拿到准备清单后，先完成需要的注册、登录和访问测试，再把完整题干与选项发给 Agent。

也可以下载 `toolkit-full.zip` 或 `agent-pack.zip`，解压后在 Agent 中打开文件夹，让它先读 `AGENTS.md` 和 `agent/START_HERE.md`，然后按上面的方式查证。

## 上传给聊天 AI

先上传 [llms-full.txt](llms-full.txt)，请它阅读上传的资料，再按上面提示中的准备和查证步骤发送题干、选项。需要更多资料时，下载 `chatgpt-pack.zip`，按需补充 `agent/` 中的操作卡、平台、题目或来源分片。

如果聊天 AI 无法浏览网站，就按它找到的步骤自行操作，再把页面结果发给它核对。

## 选择下载包

所有下载包都在 [Releases](https://github.com/Makashibata02/ai-literacy-toolkit/releases/latest) 中。优先选完整包，需要减少文件时再选用途分包。

| 文件 | 下载后怎么用 |
|---|---|
| `toolkit-full.zip` | 保留完整资料。双击 `index.html` 阅读，也可以把文件夹交给 Agent。 |
| `agent-pack.zip` | 解压后交给能读取文件的 Agent，从 `AGENTS.md` 开始。 |
| `chatgpt-pack.zip` | 解压后选择需要的文本文件，上传到聊天 AI。 |
| `offline-reader.zip` | 解压后双击 `index.html`，离线搜索和浏览。 |

每个 ZIP 都附有 `.sha256` 校验文件。原始视频、PPT、PDF和题图暂未上传，操作卡仍保留来源位置供核对。

## 使用答案前核对

- 看清答案标记。目前 6 道原题答案经过人工确认；其余题目需继续查证，有出处的候选提示单独展示。
- 对比题干条件和选项文字。年份、筛选条件变化或选项换序时，重新核对，不要照抄旧选项字母。
- 数量、排名和界面功能以题目要求的时间和实际页面为准。需要账号或机构访问时，先按 [账号准备](docs/preparation.md) 完成登录。

## 继续查阅

- [快速开始](docs/quickstart.md)：常见查题方式和例子。
- [任务与模块目录](agent/task-index.md)：按任务或知识模块找资料。
- [全部资料目录](wiki/index.md)：浏览操作卡、平台、题目和来源。
- [维护说明](docs/maintaining.md)：本地检索命令、构建、测试及资料更新。

代码采用 [MIT](LICENSE)，原创整理内容采用 [CC BY 4.0](LICENSE-CONTENT)。引用请注明 ai-literacy-wiki contributors、ai-literacy-toolkit 和资料日期；第三方资料保留原作者权利。
