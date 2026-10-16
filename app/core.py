from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/curated"
STATES = {"machine_reviewed", "human_reviewed", "draft"}
STOPWORDS = ["请问", "告诉我", "如何", "怎么", "哪个", "哪些", "能不能", "寻找答案", "寻找", "一下"]


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n")
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path, data):
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKC", str(text)).lower() if c.isalnum())


def tokens(query):
    text = unicodedata.normalize("NFKC", query).lower()
    for word in STOPWORDS:
        text = text.replace(word, "")
    out = []
    for part in re.findall(r"[a-z]+[a-z0-9]*|[\u4e00-\u9fff]+", text):
        if part.isascii():
            out.append((part, 3))
        elif len(part) == 1:
            continue
        else:
            out.extend((part[i:i+2], 1) for i in range(len(part)-1))
    return list(dict.fromkeys(out))


def notices_for(row):
    """Match reviewed editorial fields, never historical raw transcripts."""
    text = " ".join(str(row.get(k, "")) for k in
                    ["title", "summary", "stem", "rationale", "steps", "knowledge_points"])
    return [n for n in read("notices.json")
            if row.get("id") in n.get("target_ids", []) + n.get("module_ids", [])
            or any(term in text for term in n.get("match_terms", []))]


def make_items():
    tasks = read("tasks.json")
    sources = read("sources.json")
    items = []
    for row in tasks:
        items.append({**row, "url": row.get("entry_url", ""), "category": "操作卡"})
    for row in read("platforms.json"):
        items.append({**row, "checks": [row.get("access_note", "")], "category": "平台"})
    for row in read("questions.json"):
        # Answer state is independent of question-text review status.
        details = [f"{key}. {value}" for key, value in (row.get("options") or {}).items()]
        items.append({**row, "summary": row["stem"], "steps": details, "checks": [row["dynamic_note"]], "category": "历史题目"})
    for row in sources:
        refs = [{"source_id": row["id"], "locator": r.get("locator") or r.get("timestamp") or "正文", "excerpt": r.get("snippet", "")} for r in row.get("traceable_refs", [])]
        items.append({**{k:row.get(k) for k in ["id", "title", "summary", "steps", "knowledge_points", "review_status", "quarantine_reason", "context_note"]}, "kind": "source", "aliases": [*(row.get("keywords") or []), *(row.get("synonyms") or [])], "evidence": refs, "category": row.get("classification", {}).get("category", "来源"), "checks": [row["context_note"]]})
    for item in items:
        item["current_notices"] = notices_for(item)
        # Original curated evidence and source hashes remain intact. Only the
        # compiled operational steps use the corrected entry.
        for notice in item["current_notices"]:
            for old in notice.get("superseded_entries", []):
                item["steps"] = [re.sub(r"(?<![\w.-])" + re.escape(old),
                                        lambda _: notice["entry_url"], s)
                                 for s in (item.get("steps") or [])]
        item["detail_url"] = "records/" + item["id"] + ".html"
        item["search_title"] = normalize(item["title"])
        item["search_aliases"] = normalize(" ".join(item.get("aliases") or []))
        notice_text = " ".join(n["text"] for n in item["current_notices"])
        item["search_body"] = normalize(" ".join([item.get("summary", ""), notice_text, *(item.get("steps") or []), *(item.get("knowledge_points") or []), *[e.get("excerpt", "") for e in item.get("evidence", [])]]))
        original_text = " ".join([item["title"], *(item.get("aliases") or []), item.get("summary", ""), *(item.get("steps") or []), *(item.get("knowledge_points") or []), *[e.get("excerpt", "") for e in item.get("evidence", [])]])
        item["search_latin"] = sorted(set(re.findall(r"[a-z]+[a-z0-9]*", unicodedata.normalize("NFKC", original_text + " " + notice_text).lower())))
    return items


def search(query, top_k=5, kind=None, include_drafts=False, items=None):
    items = make_items() if items is None else items
    q = normalize(query)
    ts = tokens(query)
    if not q or not ts:
        return []
    latin = [t for t,w in ts if w == 3 and not t.isdigit()]
    scored = []
    for item in items:
        if kind and item["kind"] != kind:
            continue
        if not include_drafts and (item.get("review_status") == "draft" or item.get("quarantine_reason")):
            continue
        title, aliases, body = (item.get("search_"+field, "") for field in ["title", "aliases", "body"])
        alltext = title+aliases+body
        # Named Latin terms, e.g. ICS, PubMed and Excel, are hard requirements.
        if latin and any(t not in item.get("search_latin", []) for t in latin):
            continue
        coverage = sum(w for t,w in ts if t in alltext)/sum(w for _,w in ts)
        if coverage < 0.5:
            continue
        score = (100 if q == title else 0) + (80 if q in title else 0) + (55 if q in aliases else 0)
        score += sum(w * (16 if t in title else 10 if t in aliases else 3 if t in body else 0) for t,w in ts)
        score = score * coverage + (8 if item["kind"] == "task" else 0)
        scored.append((round(score,3),item))
    scored.sort(key=lambda pair:(-pair[0],pair[1]["id"]))
    return [{"score":score, **{k:v for k,v in item.items() if not k.startswith("search_")}} for score,item in scored[:top_k]]


def match_confirmed(question, options):
    """Return current letters only for an exact, unambiguous text match."""
    if question.get("answer_status") != "human_confirmed":
        return None
    letters = re.findall(r"[A-Z]", question.get("answer", ""))
    old = question.get("options") or {}
    required = [old[x] for x in letters if x in old]
    if len(required) != len(letters) or not letters:
        return None
    current = []
    for text in required:
        matches = [key for key,value in options.items() if normalize(value) == normalize(text)]
        if len(matches) != 1:
            return None
        current.append(matches[0])
    return sorted(current)


def protect_record(existing, incoming):
    """Preserve reviewed fields; a new source hash always enters re-review."""
    if not existing:
        return incoming
    if existing.get("source_hash") == incoming.get("source_hash"):
        return existing
    return {**incoming, "id": existing["id"], "review_status": "draft",
            "re_review_required": True, "previous_source_hash": existing.get("source_hash"),
            "re_review_reason": "Source hash changed; previously reviewed fields are not current evidence."}


def counts():
    sources = read("sources.json")
    questions = read("questions.json")
    return {"sources":len(sources),"modules":len(read("modules.json")),"platforms":len(read("platforms.json")),"tasks":len(read("tasks.json")),"questions":len(questions),"samples":len(read("samples.json")),"drafts":sum(s["review_status"]=="draft" for s in sources),"quarantined_sources":sum(bool(s.get("quarantine_reason")) for s in sources),"confirmed_answers":sum(q["answer_status"]=="human_confirmed" for q in questions),"evidence_linked_candidates":sum(bool(q.get("candidate")) for q in questions)}


def data_digest():
    h = hashlib.sha256()
    for path in sorted(DATA.glob("*.json")):
        h.update(path.name.encode());h.update(path.read_bytes())
    return h.hexdigest()


def lint():
    issues = []
    sources = {r["id"]:r for r in read("sources.json")}
    web = {r["id"]:r for r in read("web-sources.json")}
    tasks = read("tasks.json")
    questions = read("questions.json")
    ids = [r["id"] for r in [*sources.values(),*web.values(),*tasks,*questions,*read("platforms.json"),*read("modules.json"),*read("samples.json")]]
    if len(set(ids)) != len(ids):
        issues.append("duplicate_id")
    notice_ids=[]
    for n in read('notices.json'):
        notice_ids.append(n['id'])
        if n.get('original_text_sha256') != hashlib.sha256(n['original_text'].encode()).hexdigest():
            issues.append('notice_hash_mismatch:'+n['id'])
        if n.get('review_status') not in STATES or not n.get('source_label') or not n.get('recorded_at'):
            issues.append('notice_without_provenance:'+n['id'])
        for target in n.get('target_ids',[])+n.get('module_ids',[])+n.get('preparation_excluded_ids',[]):
            if target not in ids:
                issues.append('unknown_notice_target:'+target)
    if len(set(notice_ids))!=len(notice_ids) or set(notice_ids)&set(ids):
        issues.append('duplicate_notice_id')
    for t in tasks:
        if not t.get("evidence") or not t.get("steps") or t.get("review_status") not in STATES:
            issues.append("task_without_review_or_evidence:"+t["id"])
        for e in t["evidence"]:
            if e["source_id"] not in sources and e["source_id"] not in web:
                issues.append("unknown_evidence:"+t["id"])
            if not e.get("locator") or not e.get("excerpt"):
                issues.append("empty_evidence:"+t["id"])
            if t['review_status']!='draft' and e["source_id"] in sources and sources[e["source_id"]]["review_status"] == "draft":
                issues.append("draft_recommended:"+t["id"])
    for q in questions:
        if q["answer_status"] != "human_confirmed" and q.get("answer"):
            issues.append("unverified_answer:"+q["id"])
        if q["answer_status"] == "human_confirmed" and (not q.get("verification") or not match_confirmed(q,q["options"])):
            issues.append("invalid_confirmation:"+q["id"])
        if q.get("candidate") and not q["candidate"].get("evidence"):
            issues.append("candidate_without_evidence:"+q["id"])
    forbidden_exts = {".mp4",".wav",".pptx",".pdf",".docx",".faiss",".npy"}
    excluded = {".git",".pytest_cache","__pycache__",".venv"}
    absolute = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file:///|/Users/|/home/[a-z]|/mnt/[a-z]")
    secret = re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")
    for p in ROOT.rglob("*"):
        relative = p.relative_to(ROOT)
        if any(x in excluded for x in relative.parts) or not p.is_file() or p.name == "origin-safety.json":
            continue
        if p.suffix.lower() in forbidden_exts:
            issues.append("raw_or_heavy_file:"+relative.as_posix())
        if p.suffix in {".json",".jsonl",".md",".txt",".html",".js",".css",".yml",".toml"}:
            text=p.read_text(encoding="utf-8")
            if absolute.search(text) or secret.search(text):
                issues.append("private_data:"+relative.as_posix())
    if (DATA/"build-manifest.json").exists():
        # This optional legacy file must not be included in the source digest.
        issues.append("unexpected_build_manifest_in_curated")
    return {"status":"failed" if issues else "passed","issues":issues,"counts":counts()}
