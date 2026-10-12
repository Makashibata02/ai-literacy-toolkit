"""Read-only validation of generated consumer artifacts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote,urlsplit

from .core import ROOT,counts,data_digest,make_items,read,search


def validate():
    issues=[]
    items=make_items()
    for item in items:
        html=ROOT/'site'/item['detail_url'];md=ROOT/'wiki/records'/(item['id']+'.md')
        if not html.exists() or not md.exists():
            issues.append('missing_record:'+item['id']);continue
        expected=item.get('summary',item.get('stem',''))
        if expected and expected not in md.read_text(encoding='utf-8'):
            issues.append('summary_drift:'+item['id'])
        if item['kind']=='task':
            for step in item['steps']:
                if step not in md.read_text(encoding='utf-8'):
                    issues.append('step_drift:'+item['id'])
    for p in (ROOT/'site').rglob('*.html'):
        text=p.read_text(encoding='utf-8')
        for ref in re.findall(r'(?:href|src)="([^"]+)"',text):
            if ref.startswith(('http:','https:','#','data:','mailto:')):continue
            target=(p.parent/unquote(urlsplit(ref).path)).resolve()
            if not target.exists():issues.append('broken_html_link:'+str(p.relative_to(ROOT))+':'+ref)
    # Local links in generated Markdown are checked separately from web links.
    for parent in ['wiki','agent','docs']:
        for p in (ROOT/parent).rglob('*.md'):
            for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if ref.startswith(('http:','https:','#')):continue
                if not (p.parent/unquote(urlsplit(ref).path)).exists():issues.append('broken_md_link:'+str(p.relative_to(ROOT))+':'+ref)
    manifest=json.loads((ROOT/'reports/build-manifest.json').read_text(encoding='utf-8'))
    if manifest['data_sha256']!=data_digest():issues.append('stale_build')
    cases=json.loads((ROOT/'tests/retrieval-cases.json').read_text(encoding='utf-8'))
    results=[]
    for case in cases:
        ids=[r['id'] for r in search(case['query'],3)]
        results.append({**case,'top3':ids,'passed':case['expected'] in ids})
    passed=sum(r['passed'] for r in results)
    if passed<18:issues.append('retrieval_below_18_of_20')
    return {'status':'failed' if issues else 'passed','issues':issues,'counts':counts(),'retrieval':{'passed':passed,'total':len(results),'cases':results},'html_record_count':len(items)}


if __name__=='__main__':
    result=validate()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(result['status']!='passed')
