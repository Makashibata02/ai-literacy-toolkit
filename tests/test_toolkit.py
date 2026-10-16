import hashlib
import json
import zipfile

import pytest

from app.core import ROOT,counts,lint,make_items,match_confirmed,notices_for,protect_record,read,search
from app.validate_readable import validate


CASES=json.loads((ROOT/'tests/retrieval-cases.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case',CASES,ids=[c['expected'] for c in CASES])
def test_meaningful_retrieval(case):
    assert case['expected'] in [r['id'] for r in search(case['query'],3)]


def test_unknown_query_does_not_pad_results():
    assert search('zznonexistentplatformvv')==[]


def test_draft_and_conflict_are_excluded():
    assert all(r['review_status']!='draft' and not r.get('quarantine_reason') for r in search('国家统计局',100))
    assert any(r.get('quarantine_reason') for r in search('国家统计局',100,include_drafts=True))


def test_all_modules_and_legacy_aliases_are_traceable():
    assert {m['number'] for m in read('modules.json')}==set(range(1,51))
    mapping=read('origin-manifest.json')['entity_id_mapping']
    assert len(mapping)==56
    assert mapping['entity-002']==mapping['entity-029']
    assert len(read('platforms.json'))==53


def test_reordered_options_use_text_not_letter():
    q=next(q for q in read('questions.json') if q['id']=='Q002')
    options=dict(zip(['D','C','B','A'],q['options'].values()))
    assert match_confirmed(q,options)==['D']
    altered={**options,'D':'不同课程'}
    assert match_confirmed(q,altered) is None
    assert match_confirmed(q,{**options,'A':options['D']}) is None


def test_answer_states_and_provenance():
    qs=read('questions.json')
    assert sum(q['answer_status']=='human_confirmed' for q in qs)==6
    assert sum(q['answer'] is None for q in qs)==162
    assert all(q['verification']['author']=='用户人工复核' for q in qs if q['answer'])
    assert all('prior_hint' not in q and 'prior_hint' not in (q.get('candidate') or {}) for q in qs)
    assert all(q['candidate']['evidence'] for q in qs if q['candidate'])
    assert all(q['answer_status']!='official' for q in qs)


def test_same_hash_preserves_reviewed_fields_and_change_requires_review():
    old={'id':'doc-example','source_hash':'old','summary':'已复核','review_status':'machine_reviewed'}
    fresh={**old,'summary':'重新抽取'}
    assert protect_record(old,fresh)==old
    changed=protect_record(old,{**fresh,'source_hash':'new'})
    assert changed['review_status']=='draft' and changed['re_review_required']
    assert changed['id']==old['id']


def test_samples_are_independent_and_incomplete_are_flagged():
    samples=read('samples.json')
    assert len(samples)==93
    assert all(s['answer_status']=='training_sample' for s in samples)
    assert all(s['review_status']=='draft' for s in samples if not s['complete'])


def test_media_links_do_not_pretend_uploaded():
    media=read('media.json')
    assert media['status']=='not_uploaded'
    assert media['base_url'] is None and all(a['url'] is None for a in media['assets'])
    assert all(a['sha256'] and a['source_id'] for a in media['assets'])


def test_current_entry_overrides_steps_without_rewriting_original_evidence():
    url='https://datasearch.nmpa.gov.cn/datasearch/home-index.html'
    source=next(s for s in read('sources.json') if s['id']=='doc-cededfdf757185c2')
    item=next(s for s in make_items() if s['id']==source['id'])
    assert any(url in step for step in item['steps'])
    assert not any('datasearch.datasearch' in step for step in item['steps'])
    assert any('nmpa.gov.cn/datasearch' in step and url not in step for step in source['steps'])
    assets={a['source_id']:a['sha256'] for a in read('media.json')['assets']}
    assert source['source_hash']==assets[source['id']]
    results=search('国家药品监督管理局',5)
    assert results and all(any(n.get('entry_url')==url for n in r['current_notices']) for r in results)
    for path in ['README.md','docs/preparation.md','agent/START_HERE.md','llms-full.txt','site/modules.html']:
        assert url in (ROOT/path).read_text(encoding='utf-8')


def test_exclusion_is_visible_without_erasing_other_project_resources():
    notice=next(n for n in read('notices.json') if n.get('scope'))
    assert notice['module_ids']==['module-25']
    assert notice['preparation_excluded_ids']==['entity-038']
    result=next(r for r in search('国家社科基金项目数据库',30) if r['id']=='task-research-projects')
    assert any(n['id']==notice['id'] for n in result['current_notices'])
    assert all(not notices_for(q) for q in read('questions.json') if q['id']=='Q002')
    source=next(s for s in read('sources.json') if s['id']=='doc-cfb3f649834d35c5')
    assert '国家自然科学基金' in source['summary']
    prep=(ROOT/'docs/preparation.md').read_text(encoding='utf-8')
    assert '| [国家社科基金项目数据库]' not in prep
    assert notice['text'] in prep
    for qid in ['Q010','Q039']:
        q=next(q for q in make_items() if q['id']==qid)
        assert q['answer_status']=='unverified' and q['answer'] is None
        assert notice['text'] in (ROOT/'wiki/records'/f'{qid}.md').read_text(encoding='utf-8')


def test_notice_provenance_and_all_download_packages_are_current():
    for n in read('notices.json'):
        assert n['published_at'] is None and n['source_url'] is None
        assert n['review_status']=='machine_reviewed'
        assert hashlib.sha256(n['original_text'].encode()).hexdigest()==n['original_text_sha256']
    for path in (ROOT/'dist').glob('*.zip'):
        with zipfile.ZipFile(path) as z:
            guide=z.read('agent/START_HERE.md').decode('utf-8')
            assert all(n['text'] in guide for n in read('notices.json'))


def test_generated_artifacts_and_public_scan():
    assert lint()['issues']==[]
    result=validate()
    assert result['issues']==[]
    assert result['retrieval']['passed']>=18


def test_package_integrity_and_exclusions():
    for p in (ROOT/'dist').glob('*.zip'):
        checksum=p.with_suffix('.zip.sha256').read_text().split()[0]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==checksum
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            assert not any(n.endswith(('.mp4','.pptx','.pdf','.wav','.faiss','.npy')) or '/.git/' in n or 'origin-safety' in n for n in z.namelist())
    with zipfile.ZipFile(ROOT/'dist/toolkit-full.zip') as z:
        assert {'index.html','site/index.html','agent/START_HERE.md','app/cli.py','data/curated/tasks.json'}.issubset(z.namelist())


def test_idempotent_build():
    from app.build import build
    paths=[p for folder in ['data/curated','site','wiki','agent','dist'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    build()
    assert before=={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
