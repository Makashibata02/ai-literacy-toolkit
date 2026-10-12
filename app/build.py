from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

from .core import ROOT, DATA, counts, data_digest, make_items, read, write, write_json

LABELS={"task":"操作卡","platform":"平台","source":"历史来源","question":"历史题目","sample":"培训样题"}
REVIEW={"machine_reviewed":"机器整理","human_reviewed":"题目文字已复核","draft":"待复核"}


def esc(value):
    return html.escape(str(value or ""),quote=True)


def link(url,label):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>' if str(url).startswith(("https://","http://")) else esc(label)


def layout(title,body,prefix=""):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="AI 信息素养比赛速查：操作方法、证据与历史题目"><title>{esc(title)} · AI 信息素养速查</title><link rel="icon" href="{prefix}assets/favicon.svg"><link rel="stylesheet" href="{prefix}assets/style.css"></head>
<body><a class="skip" href="#main">跳到正文</a><header><a class="brand" href="{prefix}index.html"><span class="mark">AI</span><span>信息素养<span class="brand-sub">比赛速查</span></span></a><nav><a href="{prefix}index.html#tasks">按任务查找</a><a href="{prefix}modules.html">50 个模块</a><a href="{prefix}index.html#platforms">平台</a><a href="{prefix}index.html#questions">相似题</a><a href="{prefix}preparation.html">账号准备</a><a href="{prefix}quickstart.html">快速开始</a></nav></header><main id="main">{body}</main><footer>资料快照 2026-10-12 · 机器整理保留证据 · 原始媒体尚未上传<br>原创整理署名 ai-literacy-wiki contributors · {link('https://github.com/Makashibata02/ai-literacy-toolkit','GitHub 仓库')}</footer></body></html>'''


def evidence_html(refs,prefix=""):
    lines=[]
    for e in refs:
        sid=e.get("source_id","")
        source = f'<a href="{prefix}records/{esc(sid)}.html">{esc(sid)}</a>' if sid.startswith(("doc-","vid-","Q")) else esc(sid)
        lines.append(f'<li><div>{source} · {esc(e.get("locator"))} {link(e.get("url"),"官方来源") if e.get("url") else ""}</div><p>{esc(e.get("excerpt"))}</p><small>{esc(e.get("verified_at"))}</small></li>')
    return '<ul class="evidence">'+''.join(lines)+'</ul>'


def item_html(item):
    kind=item["kind"]
    text=f'<div class="eyebrow">{LABELS.get(kind,kind)} · {REVIEW.get(item.get("review_status"),"待复核")}</div><h1>{esc(item["title"])}</h1>'
    if item.get("quarantine_reason"):
        text+=f'<aside class="warning">隔离复核：{esc(item["quarantine_reason"])}</aside>'
    if kind=="question":
        text+=f'<p class="lead">{esc(item["stem"])}</p><ol class="options">'+''.join(f'<li><strong>{esc(k)}</strong> {esc(v)}</li>' for k,v in item["options"].items())+'</ol>'
        text+=f'<aside class="notice">{esc(item["dynamic_note"])}</aside>'
        if item["answer_status"]=="human_confirmed":
            text+=f'<section class="answer"><h2>人工确认的原题答案</h2><p>{esc(item["answer_text"])}（原题选项 {esc(item["answer"])}）</p><p>{esc(item["verification"]["basis"])} · {esc(item["verification"]["verified_at"])}</p><p>如果选项换序，按选项文字重新匹配；条件变化需重新查证。</p></section>'
        else:
            text+='<section class="answer"><h2>答案状态：未验证</h2><p>本库没有这道题的已确认答案。先搜索题干中的平台、对象与操作任务。</p></section>'
        if item.get("candidate"):
            c=item["candidate"]
            text+=f'<details class="candidate"><summary>展开有出处的待验证提示（非确认答案）</summary><p>{esc(c["answer"])} · {esc(c["answer_text"])}</p><p>{esc(c["note"])}</p><p>{esc(c["required_action"])} 核对日期：{esc(c["verified_at"])}</p><ul>'+''.join(f'<li>{link(e["url"],e.get("title","来源"))}<p>{esc(e.get("quote"))}</p></li>' for e in c["evidence"])+'</ul></details>'
    else:
        text+=f'<p class="lead">{esc(item.get("summary"))}</p>'
        url=item.get("entry_url") or item.get("url")
        if url:
            text+='<p class="entry">'+link(url,"打开官方入口 ↗")+'</p>'
        if item.get("verified_at"):
            text+=f'<p class="muted">入口资料核对日期：{esc(item["verified_at"])}（未承诺当前所有功能均已实测）</p>'
        if item.get("access_note"):
            text+=f'<aside class="notice">访问说明：{esc(item["access_note"])}</aside>'
        if item.get("inputs"):
            text+=f'<h2>先从题干提取</h2><p>{esc(item["inputs"])}</p>'
        text+='<h2>操作路径</h2><ol class="steps">'+''.join(f'<li>{esc(s)}</li>' for s in (item.get("steps") or []))+'</ol>'
        if item.get("task_ids"):
            tasks={t["id"]:t for t in read("tasks.json")}
            text+='<h2>本平台操作卡</h2><ul>'+''.join(f'<li><a href="{esc(tid)}.html">{esc(tasks[tid]["title"])}</a></li>' for tid in item["task_ids"])+'</ul>'
        if item.get("checks"):
            text+='<h2>作答前核对</h2><ul class="checks">'+''.join(f'<li>{esc(s)}</li>' for s in item["checks"])+'</ul>'
        if kind=="source":
            text+='<details><summary>历史教学知识点（不能直接作为当前题目答案）</summary><ul>'+''.join(f'<li>{esc(s)}</li>' for s in (item.get("knowledge_points") or []))+'</ul></details>'
    text+='<h2>证据与定位</h2>'+evidence_html(item.get("evidence",[]),"../")
    if kind=="source":
        text+='<aside class="notice">原件尚未上传。后续原件入口：'+link(read("media.json")["releases_url"],"仓库 Releases")+'。当前引用可回溯到来源 ID 和原始页码/时间戳。</aside>'
    return layout(item["title"],'<article class="detail">'+text+'</article>',"../")


def item_md(item):
    lines=[f'# {item["title"]}',"",f'ID: `{item["id"]}` · 类型：{LABELS[item["kind"]]} · 审核：`{item.get("review_status","draft")}`',""]
    if item.get("quarantine_reason"):
        lines.extend(["> 隔离复核："+item["quarantine_reason"],""])
    lines.extend([item.get("summary",item.get("stem","")),""])
    url=item.get("entry_url") or item.get("url")
    if url:
        lines.extend([f'官方入口：[{url}]({url})',""])
    if item.get("access_note"):
        lines.extend(["访问说明："+item["access_note"],"资料核对日期："+item.get("verified_at","未记录"),""])
    if item.get("inputs"):
        lines.extend(["## 输入条件","",item["inputs"],""])
    lines.extend(["## 操作与核对",""])
    lines.extend(f'{i}. {s}' for i,s in enumerate(item.get("steps") or [],1))
    lines.extend(["",*["- "+s for s in (item.get("checks") or [])],""])
    if item["kind"]=="question":
        lines.extend([f'答案状态：`{item["answer_status"]}`',""])
        if item["answer_status"]=="human_confirmed":
            lines.extend(["人工确认原题答案："+item["answer_text"],"原题字母："+item["answer"],"确认依据："+item["verification"]["basis"],"确认时点："+item["verification"]["verified_at"],"按选项文字重新匹配；题干限定条件变化必须重新查证。",""])
        c=item.get("candidate")
        if c:
            lines.extend(["## 有出处的待验证提示（非确认答案）","",c["answer_text"] or c["answer"],c["note"],c["required_action"],"核对日期："+c["verified_at"],""])
            lines.extend(f'- [{e.get("title","来源")}]({e["url"]})：{e.get("quote","")}' for e in c["evidence"])
    lines.extend(["", "## 证据定位",""])
    for e in item.get("evidence",[]):
        sid=e.get("source_id","")
        local=f'[{sid}]({sid}.md)' if sid.startswith(("doc-","vid-","Q")) else f'`{sid}`'
        url=f' · [原始来源]({e["url"]})' if e.get("url") else ""
        lines.append(f'- {local} · {e.get("locator","")}{url} · {e.get("verified_at","")}: {e.get("excerpt","")}')
    return "\n".join(lines).rstrip()+"\n"


def guides():
    c=counts()
    quick='''# 快速开始

1. 双击首页 index.html；也可以在 GitHub Pages 在线阅读。
2. 搜索“平台 + 操作”，例如“CNKI 高级检索”“标准 ICS 分类”“报告 词频”。
3. 打开操作卡，照着输入条件、步骤和核对项寻找证据。
4. 历史题目用于定位方法。只有标为人工确认的原题答案经过用户核对，条件变化仍需重查。
5. 需要登录、验证码、机构认证或付费资源时，由用户在自己的合法会话中完成。

## 四个查题例子

- 查文献数量：先限定文献类型、字段、年份和筛选条件，再记录现场结果。
- 查最多/最高：先确定统计范围，再核对排序指标是发文量、被引量还是其他指标。
- 查页面菜单或软件功能：确认软件版本，在当前界面逐项核对。
- 查报告词频：确认文本年份、全文范围、分词及筛词口径。

## 给 Agent 使用

把仓库链接 https://github.com/Makashibata02/ai-literacy-toolkit 发给能够浏览网页的 Agent，让它先读使用说明，列出网站与账号准备清单。收到题目后，优先联网查找当前证据，用仓库定位平台、检索方法和核对条件。

也可以下载文件夹，让 Agent 读取 AGENTS.md、agent/START_HERE.md 和 agent/task-index.md。聊天 AI 可上传 llms-full.txt；需要完整证据时再上传 agent/主题分片。
'''
    preparation=['# 账号与访问准备','',"公开检索和需要账号的操作要分别准备；以下是历史资料记录，不代表已在当前账号中实测。",'',"| 平台 | 访问方式与准备 | 核对日期 |","|---|---|---|"]
    for p in read("platforms.json"):
        preparation.append(f'| [{p["title"]}]({p["url"]}) | {p["access_note"].replace("|","/")} | {p["verified_at"]} |')
    preparation.extend(['','遇到认证界面时等待用户登录；仓库不保存密码、Cookie 或令牌。临近使用时先在自己的电脑上测试入口、检索及所需功能。'])
    agent='''# Agent 使用入口

目标：辅助用户准备访问条件和查证题目。优先联网查找当前证据，仓库用于定位平台、选择检索方法和提供历史参考。

## 先列出准备清单

读取任务目录和相关平台档案，列出官方入口、所需账号、校园网或 CARSI 访问条件，以及建议提前试用的操作。区分无需登录的公开查询和需要账号的功能，优先准备题目或学习范围涉及的平台。访问说明的核对日期较早时，先查官方页面再下结论。

## 收到题目后

1. 从题干提取对象、字段、时间、资源类型、逻辑关系、排序指标及选项文字。
2. 优先联网搜索答案的证据，先查官方页面、数据库和原始文档，打开原页核对，不只依据搜索摘要。
3. 需要查找入口、选择字段或确定操作流程时，读取 task-index.md 及相关操作卡。历史题目和候选提示只帮助定位，不代替当前证据。
4. 按题目条件核验数量、排名、菜单和功能；保留检索式、筛选与排序条件、查询日期。
5. 原题人工确认记录仅适用于原题条件和选项文字；换序时重新匹配文字，条件变化时重新联网查证。
6. 遇到登录、验证码、校园/CARSI 认证或付费墙，说明入口和所需操作，等待用户在合法会话中完成。
7. 给出建议选项及选项文字、当前证据 URL/页码/时间戳、查询条件及验证日期；证据不足时写“未确定”。辅助判断，不代替用户作出或提交最终答案。

如果无法访问 GitHub 或联网查证，说明具体限制，请用户按需提供相关文件或页面结果；不能声称已读取或已验证未访问的内容。

## 回答模板

结论：已确定 / 待验证 / 未确定。选项文字：……

证据：来源 ID；官方 URL 或页码/时间戳；核对日期。

查询条件：平台、对象、字段、时间、类型、筛选与排序。

限制/下一步：尚缺的证据、需要用户登录的操作，或条件变化。

## 本地检索

python -m app kb search "CNKI 高级检索" --top-k 5

默认不推荐草稿或被隔离来源。需要研究缺口时使用 --include-drafts。只有 Python CLI 需要 Python 3.11；资料阅读不需要任何依赖。
'''
    overview=f'''# AI 信息素养比赛速查

遇到需要查数据库、看平台界面或核对统计数据的题目，可以在这里找到对应的入口、检索步骤和证据位置。你可以直接搜索，也可以把资料交给 Agent，让它按步骤帮你查。

[打开在线速查](https://makashibata02.github.io/ai-literacy-toolkit/) · [下载资料包](https://github.com/Makashibata02/ai-literacy-toolkit/releases/latest)

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

- 看清答案标记。目前 {c['confirmed_answers']} 道原题答案经过人工确认；其余题目需继续查证，有出处的候选提示单独展示。
- 对比题干条件和选项文字。年份、筛选条件变化或选项换序时，重新核对，不要照抄旧选项字母。
- 数量、排名和界面功能以题目要求的时间和实际页面为准。需要账号或机构访问时，先按 [账号准备](docs/preparation.md) 完成登录。

## 继续查阅

- [快速开始](docs/quickstart.md)：常见查题方式和例子。
- [任务与模块目录](agent/task-index.md)：按任务或知识模块找资料。
- [全部资料目录](wiki/index.md)：浏览操作卡、平台、题目和来源。
- [维护说明](docs/maintaining.md)：本地检索命令、构建、测试及资料更新。

代码采用 [MIT](LICENSE)，原创整理内容采用 [CC BY 4.0](LICENSE-CONTENT)。引用请注明 ai-literacy-wiki contributors、ai-literacy-toolkit 和资料日期；第三方资料保留原作者权利。
'''
    maintaining=f'''# 本地检索和维护

维护前克隆仓库或下载完整包。阅读资料和使用网页搜索不需要安装依赖；运行下面的命令需要 Python 3.11 或更高版本，测试另需安装 pytest。

## 检索资料

```text
python -m app kb search "标准 ICS 分类" --top-k 5
python -m app kb status
```

搜索默认返回 JSON，包括操作步骤、审核状态和证据。需要查看草稿或被隔离来源时，加上 `--include-drafts`。

## 构建和验证

```text
python -m app kb build
python -m app kb lint --strict
python -m app.validate_readable
python -m pytest
python -m app kb package --target all
```

所有网页、Wiki 和知识包从 `data/curated/` 生成。修改整理内容后重新构建，不要单独手改生成页面中的结论。

## 更新资料

`scripts/extract.py` 只读取原项目已经整理的字段。相同来源哈希保留审核稿；哈希变化后进入草稿复核。新增的机器整理内容不能自动标为人工确认。

原件地址配置在 `data/curated/media.json`。当前状态为未上传；以后补充资源地址及权限信息时，保留来源 ID 和文件哈希。

## 资料范围

资料快照为 2026-10-12，提取自 ai-literacy-wiki 的结构化资料。包括 {c['modules']} 个模块、{c['tasks']} 张操作卡、{c['platforms']} 个平台档案、{c['questions']} 道历史题、{c['sources']} 个来源记录和 {c['samples']} 条培训样题。

{c['drafts']} 个草稿来源及 {c['quarantined_sources']} 个含冲突的来源不进入默认推荐。复核缺口见 [待复核清单](review-queue.md)，原始记录和哈希映射保留在结构化数据中。
'''
    competition=read("competition.json")
    competition_md=['# 赛事信息（与通用方法分开）','',f'官方入口：[{competition["url"]}]({competition["url"]})',f'核对日期：{competition["checked_at"]}','',competition["note"],'']
    competition_md.extend(f'- {u["published_at"]}：{u["title"]}（{u["locator"]}）' for u in competition["updates"])
    return {"quickstart":quick,"preparation":"\n".join(preparation)+"\n","agent":agent,"overview":overview,"maintaining":maintaining,"competition":"\n".join(competition_md)+"\n"}


def simple_html(md):
    # Guides are plain headings, paragraphs and lists. Tables remain readable
    # with explicit row markup; no remote Markdown renderer is necessary.
    lines=[];in_table=False;in_list=False
    def inline(value):
        return re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:link(html.unescape(m[2]),html.unescape(m[1])),esc(value))
    for line in md.splitlines():
        if in_table and not line.startswith("|"):
            lines.append('</tbody></table></div>');in_table=False
        if in_list and not re.match(r'^(?:\d+\. |\- )',line):
            lines.append('</ul>');in_list=False
        if line.startswith("|"):
            if re.match(r'^\|[- |]+\|$',line):
                continue
            if not in_table:
                lines.append('<div class="table-wrap"><table><tbody>');in_table=True
            lines.append('<tr>'+''.join('<td>'+inline(s.strip())+'</td>' for s in line.strip('|').split('|'))+'</tr>')
        elif line.startswith('#'):
            depth=min(len(line)-len(line.lstrip('#')),3)
            lines.append(f'<h{depth}>{inline(line.lstrip("# "))}</h{depth}>')
        elif re.match(r'^(?:\d+\. |\- )',line):
            if not in_list:
                lines.append('<ul>');in_list=True
            lines.append('<li>'+inline(re.sub(r'^(?:\d+\. |\- )','',line))+'</li>')
        elif line:
            lines.append('<p>'+inline(line)+'</p>')
    if in_table:lines.append('</tbody></table></div>')
    if in_list:lines.append('</ul>')
    return ''.join(lines)


def build():
    items=make_items();c=counts();g=guides()
    site=ROOT/"site"
    for name in ["style.css","app.js","favicon.svg"]:
        write(site/"assets"/name,(ROOT/"assets"/name).read_text(encoding="utf-8"))
    payload={"items":items,"counts":c,"stopwords":["请问","告诉我","如何","怎么","哪个","哪些","能不能","寻找答案","寻找","一下"]}
    write(site/"search-index.js","window.TOOLKIT = "+json.dumps(payload,ensure_ascii=False,separators=(",",":"))+';\n')
    body=f'''<section class="hero"><div><div class="eyebrow">2026 · 客观题通用速查</div><h1>先找到方法，<br><em>再找到答案。</em></h1><p class="lead">平台入口、检索条件、操作步骤与证据定位，集中在这里。<br>给人快速查阅，也给 Agent 清晰的查找路径。</p><div class="hero-links"><a class="button primary" href="quickstart.html">三分钟开始 →</a><a class="button" href="../agent/START_HERE.md">Agent 入口 ↗</a></div></div><aside class="hero-note"><span class="pill">离线可用</span><h2>一题，一条可核对的路径</h2><ol><li>看清对象和限定条件</li><li>选择平台与检索方法</li><li>用原始证据核对选项</li></ol><p>历史答案与当前结果分别标记。</p></aside></section>
<section class="numbers" aria-label="资料统计"><div><strong>{c['tasks']}</strong><span>重点操作卡</span></div><div><strong>{c['modules']}</strong><span>知识模块</span></div><div><strong>{c['platforms']}</strong><span>平台与工具</span></div><div><strong>{c['questions']}</strong><span>历史题目</span></div></section>
<section class="workspace" aria-label="查找资料"><div class="section-heading"><div><div class="eyebrow">从题目里的关键词开始</div><h2>找到你的查题路径</h2></div><a href="preparation.html">先检查账号与访问 →</a></div><label class="searchbox" for="q"><span>⌕</span><input id="q" type="search" placeholder="例如：CNKI 高级检索、标准 ICS 分类、报告词频" autocomplete="off"><kbd>/</kbd></label><div class="examples"><span>试试</span><button data-query="CNKI 高级检索">CNKI 高级检索</button><button data-query="标准 ICS 分类">标准 ICS 分类</button><button data-query="报告 词频">报告词频</button><button data-query="PubMed 通配符">PubMed 通配符</button></div><div class="filters"><div class="tabs" role="group" aria-label="资料类型"><button data-kind="task" class="active">操作卡</button><button data-kind="platform">平台</button><button data-kind="question">相似题</button><button data-kind="source">来源资料</button><button data-kind="">全部</button></div><label><input id="drafts" type="checkbox"> 包含待复核资料</label></div><p id="status" class="muted" aria-live="polite"></p><div id="results" class="results"></div><noscript><p>浏览器未启用 JavaScript，请使用 <a href="../wiki/index.md">Markdown 目录</a> 阅读。</p></noscript></section>
<section class="closing"><div><h2>查得到出处，才有把握。</h2><p>机器整理、人工确认、候选提示各有标记。遇到需要登录的平台，由你完成授权访问。</p></div><a href="competition.html">赛事官方信息 →</a></section><script src="search-index.js"></script><script src="assets/app.js"></script>'''
    write(site/"index.html",layout("首页",body))
    homepage=(site/'index.html').read_text(encoding='utf-8').replace('<div id="results" class="results"></div>','<div id="results" class="results"></div><button id="show-more" class="button more-button" hidden>显示更多</button>')
    write(site/'index.html',homepage)
    module_body='<article class="detail"><div class="eyebrow">命题范围与覆盖</div><h1>50 个知识模块</h1><p class="lead">每个模块保留来源。重点任务可直接打开操作卡；暂无专门操作卡的模块请阅读来源，并按需要在平台实测。</p><div class="module-list">'
    task_map={t['id']:t for t in read('tasks.json')}
    for m in read('modules.json'):
        module_body+=f'<section><h2>{esc(m["title"])}</h2><p>{REVIEW[m["review_status"]]} · <a href="records/{esc(m["source_id"])}.html">阅读来源 →</a></p>'
        if m['task_ids']:
            module_body+='<ul>'+''.join(f'<li><a href="records/{esc(tid)}.html">{esc(task_map[tid]["title"])}</a></li>' for tid in m['task_ids'])+'</ul>'
        else:module_body+='<p class="muted">暂无专门操作卡，方法覆盖待补充。</p>'
        module_body+='</section>'
    write(site/'modules.html',layout('50 个模块',module_body+'</div></article>'))
    write(ROOT/"index.html",'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=site/index.html"><title>打开速查</title></head><body><a href="site/index.html">打开离线速查页面</a></body></html>\n')
    for item in items:
        write(site/item["detail_url"],item_html(item))
        write(ROOT/"wiki/records"/(item["id"]+".md"),item_md(item))
    for name in ["quickstart","preparation","competition","maintaining"]:
        write(ROOT/"docs"/(name+".md"),g[name])
        write(site/(name+".html"),layout(name,'<article class="detail">'+simple_html(g[name])+'</article>'))
    write(ROOT/"README.md",g["overview"])
    write(ROOT/"START_HERE.md",'# 从这里开始\n\n双击 [index.html](index.html) 搜索资料，或先看 [快速开始](docs/quickstart.md)。\n\n也可以把 [仓库链接](https://github.com/Makashibata02/ai-literacy-toolkit) 发给 Agent，让它先列访问准备清单，再优先联网辅助查题。[README](README.md) 提供可直接复制的提示词。\n\n把文件夹交给 Agent 时，让它先读 [agent/START_HERE.md](agent/START_HERE.md) 和 [任务目录](agent/task-index.md)。\n')
    write(ROOT/"AGENTS.md",'''# Agent instructions

Start with START_HERE.md and agent/START_HERE.md. This is an evidence-linked quick reference, not an automatic answer service.

data/curated/ is the sole fact source. Site, Wiki, upload packs and llms-full.txt are compiled by python -m app kb build. Never infer conclusions from raw ASR/OCR. Preserve source IDs, hashes and review provenance. Identical source hashes must not overwrite reviewed fields; changed hashes require draft status and re-review.

Separate question-text review from answer verification. Human-confirmed answers apply only to the original conditions and option text. Candidates and training samples are separate records. New machine-authored material is machine_reviewed, never human_reviewed without the user's confirmation.

First help the user prepare relevant official entries, accounts and institutional access, distinguishing public lookup from account-only functions. When answering a question, prioritize current online evidence from official platforms and original documents. Use this repository to identify platforms, choose search methods and consult historical references, not as a substitute for live verification. Use python -m app kb search when local files are available. Draft and quarantined sources are excluded by default. Validate dynamic values on the original platform. Stop at login, CAPTCHA, institutional authentication and paywalls; wait for the user's authorized session. Explain unavailable access honestly. Do not store credentials or submit competition answers automatically.

Do not publish absolute paths, secrets, guesses or raw media. Future media links belong in data/curated/media.json. Before handoff run python -m app kb build, python -m app kb lint --strict, python -m app.validate_readable and python -m pytest.
''')
    task_index=['# 任务与模块目录','',"先按任务定位，再读完整操作卡。没有操作卡的模块仍保留来源及审核状态。",'']
    for task in read("tasks.json"):
        task_index.append(f'- [{task["title"]}](../wiki/records/{task["id"]}.md) · '+', '.join(task['module_ids']))
    task_index.extend(['','## 全部模块',''])
    for m in read("modules.json"):
        task_index.append(f'- [{m["title"]}](../wiki/records/{m["source_id"]}.md) · `{m["review_status"]}` · '+('、'.join(m['task_ids']) if m['task_ids'] else '暂无专门操作卡，阅读来源或请用户实测'))
    write(ROOT/"agent/START_HERE.md",g["agent"])
    write(ROOT/"agent/task-index.md",'\n'.join(task_index)+'\n')
    wiki=['# 速查 Wiki','',"[使用入口](../START_HERE.md) · [任务与模块](../agent/task-index.md) · [账号准备](../docs/preparation.md)",'']
    for kind in ["task","platform","question","source"]:
        wiki.extend(['## '+LABELS[kind],''])
        wiki.extend(f'- [{item["title"]}](records/{item["id"]}.md) · `{item["review_status"]}`' for item in items if item["kind"]==kind)
        wiki.append('')
        shard=[g["agent"], '\n# '+LABELS[kind]+'主题分片\n']
        for item in items:
            if item["kind"]!=kind or item["review_status"]=="draft" or item.get("quarantine_reason"):
                continue
            # Internal links in shards resolve relative to agent/.
            md=item_md(item)
            md=re.sub(r'\]\(((?:doc-|vid-|Q)[^)]+\.md)\)',r'](../wiki/records/\1)',md)
            shard.append(md)
        write(ROOT/"agent"/(kind+".md"),'\n'.join(shard))
    write(ROOT/"wiki/index.md",'\n'.join(wiki)+'\n')
    compact=[g["agent"],"\n# 完整重点操作卡与平台入口\n"]
    for item in items:
        if item["kind"] in {"task","platform"} and item["review_status"]!='draft':
            compact.append(item_md(item))
    compact.append('\n# 人工确认的原题答案（仅限原题条件）\n')
    compact.extend(item_md(i) for i in items if i["kind"]=='question' and i["answer_status"]=='human_confirmed')
    full='\n'.join(compact)
    full=re.sub(r'\]\(((?:doc-|vid-|Q)[^)]+\.md)\)',r'](wiki/records/\1)',full)
    write(ROOT/"llms-full.txt",full)
    write(ROOT/"llms.txt",'# AI literacy toolkit\n\nStart: agent/START_HERE.md\nTask index: agent/task-index.md\nCompact upload pack: llms-full.txt\nAll evidence records: wiki/index.md\nStructured truth: data/curated/\n')
    # Training samples keep independent status and never merge into history answers.
    sample_md=['# 培训材料样题（独立附录）','',"材料中出现的答案不等于当前比赛标准答案。缺失选项或来自草稿的条目标为待核对。",'']
    for s in read("samples.json"):
        sample_md.extend([f'## {s["id"]}', '', s['stem'], '', f'状态：`{s["review_status"]}` · 完整性：{s["complete"]}', '', *[f'- {k}. {v}' for k,v in s['options'].items()], '', f'材料记载答案：{s["answer"] or "缺失"}', s['rationale'], f'来源：[{s["source_id"]}](../wiki/records/{s["source_id"]}.md) · {s["locator"]}', s['context_note'], ''])
    write(ROOT/"docs/training-samples.md",'\n'.join(sample_md)+'\n')
    gaps=['# 覆盖与待复核清单','',f'已覆盖 {c["modules"]} 个模块，其中 {c["tasks"]} 张操作卡覆盖重点任务。','']
    gaps.extend(f'- {s["id"]} · {s["title"]}：'+(s.get('quarantine_reason') or '原稿为 draft；保留问题说明，不纳入默认推荐。') for s in read('sources.json') if s['review_status']=='draft' or s.get('quarantine_reason'))
    write(ROOT/'docs/review-queue.md','\n'.join(gaps)+'\n')
    manifest={"data_sha256":data_digest(),"counts":c,"generated_from":"data/curated","snapshot_date":"2026-10-12"}
    write_json(ROOT/"reports/build-manifest.json",manifest)
    package_result=package_all()
    return {"status":"built",**manifest,"packages":package_result["files"]}


def package_all(target="all"):
    choices={"full":("toolkit-full.zip",["app","scripts","tests","assets","data/curated","wiki","docs","agent","site","index.html","README.md","START_HERE.md","AGENTS.md","LICENSE","LICENSE-CONTENT","CITATION.cff","pyproject.toml","llms.txt","llms-full.txt","reports/build-manifest.json","reports/validation.json"]),"agent":("agent-pack.zip",["agent","wiki","docs","data/curated","app","assets","AGENTS.md","START_HERE.md","llms-full.txt","LICENSE-CONTENT"]),"chatgpt":("chatgpt-pack.zip",["agent","wiki","docs","llms-full.txt","LICENSE-CONTENT"]),"offline":("offline-reader.zip",["site","index.html","docs","wiki","agent","llms-full.txt","LICENSE-CONTENT"])}
    files=[]
    for kind,(name,roots) in choices.items():
        if target not in {"all",kind}:continue
        path=ROOT/"dist"/name;path.parent.mkdir(parents=True,exist_ok=True)
        paths=[]
        for folder in roots:
            p=ROOT/folder
            if p.is_file():paths.append(p)
            elif p.exists():paths.extend(f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(paths):
                info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
                z.writestr(info,p.read_bytes(),compresslevel=9)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        write(path.with_suffix('.zip.sha256'),digest+'  '+name+'\n')
        files.append({"file":'dist/'+name,"bytes":path.stat().st_size,"sha256":digest})
    return {"target":target,"files":files}
