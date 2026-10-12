"""One-time, read-only extraction from a reviewed source library.

Usage: python scripts/extract.py --source <source-library>
Never reads raw media or infers facts from ASR/OCR. Existing reviewed output
is not overwritten on an identical hash; changed inputs require re-review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-10-12"
UPDATE = False


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(name, obj):
    path = ROOT / "data/curated" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == text:
            return
        if not UPDATE:
            raise SystemExit(f"Protected existing data: {name}; use --update for hash-guarded extraction.")
    path.write_text(text, encoding="utf-8", newline="\n")


# These are editorial task routes, not inferred answers. Each source is an
# existing reviewed record; current official web evidence is added separately.
RECIPES = [
 ("cnki-advanced", "CNKI 高级检索与结果筛选", [31,35], ["CNKI"], ["中国知网", "篇名", "作者", "作者单位", "CSSCI", "北大核心", "年度", "被引", "机构论文"], ["vid-b7bb6d67941f24ad", "vid-f5b84abd62ffc0e2"], "https://www.cnki.net/", ["确认题目要求的文献类型、篇名/主题、作者或机构、年份与来源类别。", "进入高级检索，先选文献类型，再将条件分别填入对应字段。", "核对精确/模糊匹配与条件间逻辑；执行检索后复查已选筛选条件。", "若题目要求最多、最新或被引最高，按指定指标排序，记录检索式和当前结果。"], ["文献类型、字段、年份与题目完全一致。", "数量和排名取现场结果；不同筛选项之间的逻辑不能凭直觉判断。"]),
 ("cnki-boolean", "CNKI 布尔逻辑 AND OR NOT", [32], ["CNKI"], ["知网", "并且", "或者", "排除", "布尔", "星号", "加号", "减号"], ["vid-fb303ba7539cbf1e", "doc-0c7da090c862ca53"], "https://www.cnki.net/", ["把题目拆成必须同时满足、满足其一及排除三个条件组。", "在高级检索各行设置字段与检索词，检查行间 AND/OR/NOT。", "同一字段的语法以当前平台提示为准，不把其他数据库语法直接复制过来。", "记录完整表达式，核对结果标题是否符合全部限定条件。"], ["注意 OR 的分组范围及同一来源类别多选的关系。"]),
 ("cnki-exact", "CNKI 精确与模糊匹配", [34], ["CNKI"], ["精确", "模糊", "匹配", "机构", "单位", "篇名", "中国知网"], ["vid-b4459b17ded2fd9b", "doc-bc5c608ce4797fa1"], "https://www.cnki.net/", ["先确定题目限定的是完整字段值还是包含某关键词。", "对比当前界面精确和模糊选项，再设置所需字段。", "检查命中记录实际字段，区分名称变体、简称和同名项。"], ["不能仅凭结果数量判断精确检索是否设置正确。"]),
 ("wanfang-analysis", "万方 检索、筛选与可视化机构排名", [31,35,50], ["万方"], ["万方数据", "高级检索", "题名", "机构", "发文量", "被引频次", "可视化", "排名"], ["vid-492556d39f0e6c51", "vid-5384d31df63fa222"], "https://www.wanfangdata.com.cn/", ["进入高级检索，限定文献类型、题名及题目要求的时间范围。", "在结果中应用来源类别等筛选，记录筛选后的检索范围。", "打开可视化分析，选择机构等分析维度。", "核对统计指标是发文量还是被引频次，并读取当前排名。"], ["分析维度和统计指标必须分别核对，旧教学排名仅作示例。"]),
 ("vip-fields", "维普 字段限制与布尔检索", [32,36], ["维普"], ["中文期刊服务平台", "专业检索", "字段代码", "题名", "篇名", "作者单位", "学位论文", "会议论文"], ["vid-5d13a2719f93c409", "vid-0613914ed908f2ce"], "https://www.cqvip.com/", ["区分维普网与中文期刊服务平台，选择题目指定的资源类型。", "查看该资源类型当前可用字段，不把期刊字段套到学位或会议资源。", "在高级或专业检索中组合字段和布尔关系，字段代码以当前帮助为准。", "复查检索式和命中记录。"], ["同一品牌下不同产品的字段及语法可能不同。"]),
 ("pubmed-search", "PubMed 标题、日期、文献类型与全文检索", [21,31,35], ["PubMed"], ["NCBI", "Title", "Advanced", "Clinical Trial", "Free Full Text", "PMC", "医学文献", "糖尿病", "临床试验", "免费全文"], ["vid-ab0bdcb28214da69"], "https://pubmed.ncbi.nlm.nih.gov/advanced/", ["确认题目的标题/主题、发表日期、文献类型与全文条件。", "在 Advanced 选择适当字段，组合检索词与日期。", "执行检索并应用所需筛选，查看已生效筛选条件。", "打开题录核对标题与标识符；通过全文链接查看全文来源。"], ["PubMed 题录与 PMC 全文不是同一个资源；数量以现场为准。"]),
 ("pubmed-wildcards", "PubMed 通配符、截词与自动映射核对", [33,36], ["PubMed"], ["通配符", "截词", "wildcard", "truncation", "星号", "自动词语匹配", "ATM"], ["web-pubmed-help"], "https://pubmed.ncbi.nlm.nih.gov/help/#wildcards-and-truncation", ["打开官方 User Guide 的 Wildcards and truncation 小节。", "用星号表示词或短语中的零个或多个字符，并检查当前指南中的限制。", "查看检索详情，核对字段与词语映射；不要套用其他库的通配规则。"], ["官方帮助核对日期为 2026-10-12；实际查询仍须检查检索详情。"]),
 ("standards-ics", "标准查询：名称、标准号与 ICS CCS 分类", [11], ["全国标准信息公共服务平台"], ["标准", "ICS", "CCS", "国际标准分类", "中国标准分类", "电动车", "电动汽车", "标准号", "国家标准", "行业标准", "地方标准"], ["doc-7519eae042f8f09e", "web-standards-search"], "https://std.samr.gov.cn/gb/search/gbAdvancedSearch", ["确认题目指定国家、行业或地方标准，以及名称关键词和标准状态。", "打开官方标准检索，输入名称或标准号，设置页面提供的限定条件。", "查看命中标准的详情或结果记录中的 ICS 和 CCS，逐条记录。", "比较题目选项；确认是在问 ICS 还是 CCS，并核对有效状态和查询日期。"], ["ICS 与 CCS 是两套分类，不互相替代；一个检索词可能命中多项标准。"]),
 ("stats-data", "国家统计局 数据查询与指标口径", [9], ["国家统计局"], ["统计数据", "国家数据", "年度", "季度", "月度", "指标", "地区", "快递量", "下载", "统计年鉴"], ["vid-27532b0a1d6f8133"], "https://data.stats.gov.cn/", ["选择题目指定的数据来源和数据频率，按指标关键词查询。", "核对指标名称、时间范围、地区和计量单位。", "在表格或图表中读取当前数据；不要沿用历史视频里的年份范围或数量。", "若下载需要登录，等待用户完成登录，再按页面可用格式导出。"], ["原视频笔记的示例答案存在冲突，本卡仅保留查询方法。", "注意累计值、当期值、单位与数据修订日期。"]),
 ("word-frequency", "微词云 报告全文分词与词频统计", [49], ["微词云"], ["词频", "统计", "政府工作报告", "动词", "成语", "分词", "筛词", "全文", "最高频"], ["vid-4d9ad348c7936bab", "vid-ddd1793443f03f4b"], "https://www.weiciyun.com/", ["从题目指定的官方页面获取指定年份、版本的报告全文。", "打开在线分词，粘贴文本或导入文件；记录预处理范围。", "按题目要求选择动词、成语等词类或筛词条件。", "按词频排序并读取当前统计结果，保留文本来源与分词设置。"], ["年份、全文范围、分词与筛词设置改变都会影响答案。"]),
 ("search-operators", "搜索引擎 site filetype 与限定检索", [37], [], ["搜索引擎", "site", "filetype", "站内搜索", "PDF", "官网", "检索语法"], ["vid-188b5eaaca3fad94", "vid-338f72a3586c1483", "doc-22bee0200563f76f"], "", ["提取题目的独特标题或短语，优先在官方域名范围检索。", "用 site: 限定域名，需找特定文件类型时加入 filetype:。", "打开原始结果并核对正文、日期和发布主体，不把搜索摘要直接作为答案。"], ["搜索没有命中不能证明内容不存在。"]),
 ("sciencedirect", "ScienceDirect 高级检索与全文定位", [21,31], ["ScienceDirect"], ["Elsevier", "爱思唯尔", "Advanced Search", "作者", "期刊", "出版年", "全文"], ["vid-da01b5107629d72a"], "https://www.sciencedirect.com/", ["进入 Advanced Search，按题目选择标题、作者、期刊或时间条件。", "执行检索后核对出版信息与文献类型。", "进入题录或全文页面，按题目定位段落、页面或单词。", "全文需订阅或机构认证时等待用户提供合法访问会话。"], ["题录可访问不代表全文可下载；PDF 页码与印刷页码需区分。"]),
 ("thesis", "MIT 学位论文与学术文献定位", [23], [], ["MIT", "Theses", "DSpace", "学位论文", "麻省理工", "论文标题", "作者", "PDF", "页码", "单词"], ["vid-01a1ae989b1ddea6", "doc-4d964945655f57b3"], "https://dspace.mit.edu/", ["使用题目给出的准确标题、作者或标识符定位论文。", "核对学位、年份、机构与版本，进入全文。", "按题目要求定位页码或段落，区分 PDF 文件页序与文内页码。", "记录全文链接及具体定位。"], ["不要只凭搜索结果标题相似就认定同一论文。"]),
 ("cnki-conference", "CNKI 学术会议论文与会议信息", [22], ["CNKI"], ["中国知网", "会议论文", "会议名称", "会议届次", "作者", "会议网"], ["vid-ca42627a9659187d", "doc-68489b705150812d"], "https://www.cnki.net/", ["选择会议资源，输入会议名称及题目指定届次或年份。", "核对会议详情与论文集范围，再查询论文或作者。", "若需要发文最多作者，限定同一论文集后查看统计或逐条核对。"], ["同名不同届会议不能合并统计。"]),
 ("literature-tracking", "CNKI PubMed RSS 文献追踪与提醒", [47], ["CNKI", "PubMed"], ["RSS", "文献追踪", "订阅", "邮件提醒", "新文献", "My NCBI"], ["vid-f5081c33be95054a", "vid-bb8f99ba163c3913", "doc-48eb7392b22b738e"], "https://pubmed.ncbi.nlm.nih.gov/", ["先建立可重复的检索式并记录条件。", "根据平台可用功能建立 RSS、保存检索或提醒。", "需个人账号时等待用户登录，再核对订阅内容和更新条件。"], ["区分 RSS 链接、检索链接与邮件提醒功能。"]),
 ("excel-clean", "Excel TRIM CLEAN MID FIND 数据清洗", [48], ["Excel"], ["去空格", "换行", "非打印字符", "提取", "字符串", "数据清洗", "TRIM", "CLEAN", "MID", "FIND"], ["vid-4e58b20c511d6cdd", "doc-d76af9a5e1f68182"], "", ["保留原列，在新列测试清洗公式。", "用 TRIM 处理常见多余空格，用 CLEAN 处理常见非打印字符。", "需要提取子串时，用 FIND 定位，再用 MID 截取。", "以题目示例逐条核对输出，再填充到其他行。"], ["先检查字符类型和边界，不能假定所有空白都由同一公式清除。"]),
 ("pdf-tools", "PDF 合并、拆分、转换与页码核对", [41], ["云展网"], ["PDF", "合并", "拆分", "转Word", "压缩", "另存为", "文件转换"], ["doc-f91c691389bf4c43", "vid-b4c67ab6b38da6a3"], "https://www.yunzhan365.com/", ["按题目确认合并、拆分、转换等目标和输出格式。", "在 Office 中可使用另存为 PDF；在线工具选择对应功能。", "查看当前界面的可选项、限制与输出结果，逐项对照题目。"], ["功能支持范围和限制以现场页面及实际文件为准。"]),
 ("reference-export", "参考文献著录格式与题录导出", [44], ["CNKI", "万方", "维普"], ["参考文献", "GB/T", "7714", "APA", "MLA", "导出", "著录格式", "引用"], ["doc-37c284e70e158a59", "vid-5c1e87e2875c9704"], "https://www.cnki.net/", ["确认题目指定的格式及版本，或查看目标期刊的投稿要求。", "在数据库选中文献，打开题录导出并查看实际支持的格式。", "核对文献类型、作者、年份、页码与标识符。", "不把教学材料中的格式版本当作所有平台已支持的证明。"], ["按题目要求选定版本；导出后仍需逐项检查。"]),
 ("citespace", "CiteSpace 项目、时间切片与节点类型", [50], ["CiteSpace"], ["Projects", "Time Slicing", "Node Types", "作者合作", "机构合作", "关键词", "共现", "文献可视化"], ["vid-dc804f940069a13a", "doc-8173bbe1d0254327"], "", ["创建项目并指定数据源与数据目录。", "设置分析起止时间和时间切片。", "选择题目要求的节点类型，再运行分析。", "核对图例与分析维度，记录参数配置。"], ["作者、机构、关键词等节点类型对应不同问题。"]),
 ("wechat-index", "微信指数 日期、关键词与异动来源", [29], ["微信指数"], ["指数", "环比", "异动来源", "日期", "京东", "热度", "网络指数"], ["vid-e464e4f5d68eb5a6", "doc-54a2e8cf2ca1a8fc"], "", ["在微信内进入微信指数，搜索题目指定关键词。", "选择题目指定日期或时间范围，查看对应曲线和信息。", "按当前界面查看异动来源或环比，记录页面值与日期。"], ["此类数值随日期和平台更新变化，需授权会话内实测。"]),
 ("library-catalog", "图书馆馆藏查询与索书号", [30], [], ["馆藏", "图书馆", "书名", "索书号", "馆藏地", "OPAC", "借阅"], ["vid-2dbc6a1ddc02278a", "doc-9c299a88488fee50"], "", ["进入题目指定图书馆的馆藏查询系统。", "以书名、作者或 ISBN 检索并核对版次。", "查看馆藏位置、索书号和当前馆藏状态，记录对应馆藏条目。"], ["不能把不同版次或不同图书馆的记录混用。"]),
 ("education-query", "学信网与中国教育考试网资格信息查询", [15,16], ["学信网", "中国教育考试网"], ["学历", "学位", "考试", "证书", "资格", "教资", "公告", "报名"], ["vid-97d419e18e5abc5d", "vid-4e424b2bc22bea57", "doc-cf2e7a42a8a5a3a9"], "https://www.chsi.com.cn/", ["识别题目查询的是学历学位、考试证书还是公告。", "进入对应官方平台，按公告年份、地区或证书类型定位。", "核对字段和正文；涉及个人信息的查询由用户在自己的账号中完成。"], ["学历学位查询与考试资格公告使用的入口不同。"]),
 ("health-query", "卫健委医卫统计与信息查询", [14], ["卫健委"], ["卫生健康", "卫健委", "卫生统计", "医疗", "数据", "公报", "年度"], ["vid-6c64cc14e449ad7f", "doc-cededfdf757185c2"], "https://www.nhc.gov.cn/", ["进入国家卫生健康委员会官网，定位题目指定栏目或统计发布。", "按年份及标题查找官方正文或附件。", "核对统计指标、单位与发布年份，记录表号或段落。"], ["统计年份与公报发布时间不一定相同。"]),
 ("research-projects", "国家社科基金项目数据库检索", [25], ["国家社科基金项目数据库"], ["社科", "基金", "项目", "立项", "负责人", "单位", "年度", "批准号"], ["vid-f7289510d1266938", "doc-cfb3f649834d35c5"], "", ["打开项目官方查询入口，确认基金类别及项目年度。", "按题目给出的项目名、负责人、单位或批准号检索。", "核对完整条目及限定条件，保存检索式和当前结果。"], ["不同基金类别、年度和项目状态不能合并判断。"]),
 ("qq-capture", "QQ 截图、贴图与录屏功能核对", [40], ["QQ"], ["截图", "贴图", "录屏", "快捷键", "图像", "工具栏"], ["vid-0c76d3bc9c5d1cbd", "doc-74ecaf8c8622f1d6"], "", ["在实际安装的 QQ 版本中打开截图或录屏工具。", "查看工具栏及菜单，按题目要求测试贴图、标注或录屏选项。", "记录软件版本和实际观察，不用旧版本教学菜单推断当前功能。"], ["界面功能随客户端版本变化，应实测后作答。"]),
]


def main():
    global UPDATE
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--update", action="store_true", help="Preserve identical-hash reviews; changed sources enter draft re-review.")
    args = parser.parse_args()
    UPDATE = args.update
    source = args.source / "data/curated"
    inputs = {}
    records = []
    keep = ["id", "title", "source_type", "file_type", "relative_path", "source_hash", "classification", "tags", "summary", "steps", "knowledge_points", "resources", "terms", "keywords", "synonyms", "traceable_refs", "quality", "review_status", "editorial_review", "created_at"]
    for folder in ["videos", "documents", "presentations"]:
        for path in sorted((source / folder).glob("*.json")):
            old = load(path)
            row = {k: old[k] for k in keep if k in old}
            row["record_hash"] = digest(path)
            row["snapshot_date"] = DATE
            row["context_note"] = "历史教学材料；示例答案、数量、排名、界面和版本不能直接用于当前题目。"
            if row["id"] == "vid-27532b0a1d6f8133":
                row["quarantine_reason"] = "知识点给出的答案判断与已整理证据摘录相互矛盾；仅使用不涉及答案的查询方法。"
            records.append(row)
            inputs[path.relative_to(args.source).as_posix()] = digest(path)
    existing_path=ROOT/'data/curated/sources.json'
    if UPDATE and existing_path.exists():
        import sys
        sys.path.insert(0,str(ROOT))
        from app.core import protect_record
        previous={s['id']:s for s in load(existing_path)}
        records=[protect_record(previous.get(s['id']),s) for s in records]
    byid = {r["id"]: r for r in records}
    modules = []
    for r in records:
        match = re.match(r"知识模块\s*(\d+)[:：]", r["title"])
        if match:
            modules.append({"id": f"module-{int(match[1]):02d}", "number": int(match[1]), "title": r["title"], "source_id": r["id"], "review_status": r["review_status"], "task_ids": []})
    original_entities = load(source / "web/entities.json")["entities"]
    # Union existing aliases without changing any source/entity IDs.
    canonical = {}
    platforms = []
    mapping = {}
    for n, entity in enumerate(original_entities, 1):
        eid = f"entity-{n:03d}"
        names = [entity["name"], *entity.get("aliases", []), entity.get("same_as", "")]
        existing = next((canonical[x.casefold()] for x in names if x and x.casefold() in canonical), None)
        if existing:
            row = existing
            row["origin_ids"].append(eid)
            row["aliases"] = sorted(set(row["aliases"] + names) - {"", row["title"]})
        else:
            row = {"id": eid, "kind": "platform", "title": entity["name"], "origin_ids": [eid], "aliases": sorted(set(names) - {"", entity["name"]}), "url": entity.get("url", ""), "summary": entity.get("features", ""), "access_mode": entity.get("access_mode", "manual"), "access_note": entity.get("access_note", ""), "verified_at": entity.get("last_verified", entity.get("retrieved_at", "")), "review_status": "machine_reviewed" if entity.get("status") == "verified" else "draft", "task_ids": [], "evidence": [{"source_id": "origin-web-entities", "locator": entity["name"], "url": entity.get("url", ""), "verified_at": entity.get("last_verified", "")}]}
            platforms.append(row)
        for name in names:
            if name:
                canonical[name.casefold()] = row
        mapping[eid] = row["id"]
    web_sources = [
        {"id": "web-pubmed-help", "title": "PubMed User Guide", "url": "https://pubmed.ncbi.nlm.nih.gov/help/", "verified_at": DATE, "review_status": "machine_reviewed", "facts": ["指南包含字段、布尔检索、通配符及截词的说明。", "星号可表示词或短语中的零个或多个字符；具体限制应核对当前指南。"], "locator": "Wildcards and truncation; Using search field tags", "verification_method": "official_page_read"},
        {"id": "web-standards-search", "title": "全国标准信息公共服务平台检索", "url": "https://std.samr.gov.cn/search/stdPage?q=%E6%B1%BD%E8%BD%A6", "verified_at": DATE, "review_status": "machine_reviewed", "facts": ["官方检索结果展示标准号、标准状态及 ICS、CCS 分类信息。"], "locator": "国家标准检索结果中的分类与状态字段", "verification_method": "official_page_search"},
    ]
    tasks = []
    for slug, title, module_nums, platform_names, aliases, source_ids, url, steps, checks in RECIPES:
        evidence = []
        requires_review = False
        for sid in source_ids:
            if sid.startswith("web-"):
                s = next(s for s in web_sources if s["id"] == sid)
                evidence.append({"source_id": sid, "locator": s["locator"], "url": s["url"], "verified_at": s["verified_at"], "excerpt": "；".join(s["facts"])})
            else:
                s = byid[sid]
                if s["review_status"] == "draft":
                    requires_review = True
                refs = [r for r in s.get("traceable_refs", []) if r.get("supports") in {"steps", "resources", "summary"}]
                if not refs:
                    refs = s.get("traceable_refs", [])[:1]
                for ref in refs[:3]:
                    evidence.append({"source_id": sid, "locator": ref.get("timestamp") or ref.get("locator") or "正文", "excerpt": ref.get("snippet", ""), "verified_at": s.get("editorial_review", {}).get("reviewed_at", "")[:10]})
        pids = list(dict.fromkeys(canonical[n.casefold()]["id"] for n in platform_names if n.casefold() in canonical))
        row = {"id": "task-" + slug, "kind": "task", "title": title, "aliases": aliases, "module_ids": [f"module-{n:02d}" for n in module_nums], "platform_ids": pids, "summary": "；".join(steps[:2]), "entry_url": url, "inputs": "从题干提取平台、对象、字段、时间、类型、排序指标及需要比较的选项文字。", "steps": steps, "checks": checks, "evidence": evidence, "review_status": "machine_reviewed", "reviewed_at": DATE, "dynamic_note": "数量、排名、页面菜单及功能限制需在题目指定时间和当前授权会话中核验。", "authored_by": "Codex editorial extraction"}
        if requires_review:
            row.update(review_status='draft',re_review_required=True)
        task_hash_material = '|'.join(byid[sid]['source_hash'] if sid in byid else next(w['verified_at']+w['url'] for w in web_sources if w['id']==sid) for sid in source_ids)
        row['source_hash'] = hashlib.sha256(task_hash_material.encode()).hexdigest()
        task_path=ROOT/'data/curated/tasks.json'
        if UPDATE and task_path.exists():
            old_task=next((t for t in load(task_path) if t['id']==row['id']),None)
            if old_task and old_task.get('source_hash'):
                row=protect_record(old_task,row)
                if requires_review:
                    row={**row,'review_status':'draft','re_review_required':True}
        tasks.append(row)
        for m in modules:
            if m["id"] in row["module_ids"]:
                m["task_ids"].append(row["id"])
        for p in platforms:
            if p["id"] in pids:
                p["task_ids"].append(row["id"])
    questions = load(source / "questions/questions.public.json")["questions"]
    manual = load(source / "questions/manual_answers.json")
    confirmed = {a["qid"]: a for a in manual["answers"]}
    web_answers = {r["question_id"]: r for r in load(source / "questions/web_inferred_answers.json")["questions"]}
    output_questions = []
    for old in questions:
        row = {k: old.get(k) for k in ["id", "stem", "options", "declared_type", "bank", "source_hash", "relative_source", "needs_review", "review_status", "reviewed_at"]}
        row.update({"kind": "question", "title": old["id"] + " · " + old["stem"][:80], "answer": None, "answer_text": "", "answer_status": "unverified", "candidate": None, "verification": None})
        if old["id"] in confirmed:
            a = confirmed[old["id"]]
            row.update({"answer": a["answer"], "answer_text": a["answer_text"], "answer_status": "human_confirmed", "verification": {k: a.get(k) for k in ["author", "basis", "verified_at"]}})
        r = web_answers.get(old["id"], {})
        evidence = [e for e in (r.get("evidence") or []) if e.get("url", "").startswith(("https://", "http://")) and (e.get("quote") or e.get("title"))]
        if r.get("web_candidate_answer") and evidence and r.get("web_status") in {"web_supported", "web_partial"}:
            row["candidate"] = {"answer": r["web_candidate_answer"], "answer_text": r.get("web_candidate_text", ""), "status": "candidate_supported" if r["web_status"] == "web_supported" else "candidate_partial", "evidence": evidence, "note": r.get("note", ""), "verified_at": r.get("retrieval_date", ""), "required_action": "仅作待验证提示，先按题目限定条件打开原始来源逐项核验。"}
        row["dynamic_note"] = "历史题目可能改变年份、数字、条件或选项顺序；人工确认仅针对原题和确认时点。"
        row["evidence"] = [{"source_id": old["id"], "locator": old.get("relative_source", "原始题图"), "verified_at": old.get("reviewed_at", "") or "2026-09-18"}]
        output_questions.append(row)
    samples = []
    for block in load(source / "questions/official_samples.json")["blocks"]:
        normalized = block.get("stem_norm", "")
        sid = "sample-" + hashlib.sha256((block["doc_id"] + block["locator"] + normalized).encode()).hexdigest()[:16]
        samples.append({"id": sid, "kind": "sample", "title": "培训材料样题 · " + block["stem_raw"][:70], "stem": block["stem_raw"], "options": block.get("options", {}), "answer": block.get("answer"), "rationale": block.get("rationale", ""), "complete": bool(block.get("complete")), "review_status": "machine_reviewed" if block.get("complete") and byid.get(block["doc_id"], {}).get("review_status") != "draft" else "draft", "answer_status": "training_sample", "source_id": block["doc_id"], "locator": block["locator"], "context_note": "从培训材料抽取的样题答案，尚未逐题人工复核；不等于当前比赛题的官方答案。"})
    samples = list({s["id"]: s for s in samples}.values())
    for p in platforms:
        p["steps"] = [next(t["title"] for t in tasks if t["id"] == tid) for tid in p["task_ids"]]
        if not p["task_ids"]:
            p["steps"] = ["本库暂无经过整理的专门操作卡；打开官方入口，按题目限定条件核验。"]
    for filename in ["web/entities.json", "questions/questions.public.json", "questions/manual_answers.json", "questions/official_samples.json", "questions/web_inferred_answers.json"]:
        inputs["data/curated/" + filename] = digest(source / filename)
    save("sources.json", records)
    save("modules.json", sorted(modules, key=lambda m: m["number"]))
    save("platforms.json", platforms)
    save("tasks.json", tasks)
    save("questions.json", output_questions)
    save("samples.json", samples)
    save("web-sources.json", web_sources)
    save("origin-manifest.json", {"origin_project": "ai-literacy-wiki", "extracted_at": DATE, "method": "reviewed_structured_fields_only", "input_hashes": inputs, "entity_id_mapping": mapping, "manual_answer_provenance": {k:v for k,v in manual.items() if k != "answers"}})
    save("media.json", {"status": "not_uploaded", "label": "原件尚未上传", "repository": "Makashibata02/ai-literacy-toolkit", "releases_url": "https://github.com/Makashibata02/ai-literacy-toolkit/releases", "base_url": None, "assets": [{"source_id": r["id"], "sha256": r["source_hash"], "asset_name": r["id"] + Path(r["relative_path"]).suffix.lower(), "url": None} for r in records]})
    save("competition.json", {"id": "competition-2026", "title": "2026 年赛事信息与官方入口", "url": "https://csc.xxsuyang.com/", "checked_at": DATE, "review_status": "machine_reviewed", "updates": [{"published_at": "2026-09-30", "title": "淘汰赛彩排与比赛时间安排", "locator": "官网最新公告"}, {"published_at": "2026-10-08", "title": "淘汰赛赛前培训通知", "locator": "官网最新公告"}], "note": "这里只登记已发现的公告标题；具体赛区时间、规则和可用工具以最新官方通知及赛场安排为准。通用查题方法不依赖某次赛事日程。", "verification_method": "official_homepage_search"})
    print(json.dumps({"sources": len(records), "modules": len(modules), "platforms": len(platforms), "tasks": len(tasks), "questions": len(output_questions), "samples": len(samples)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
