"""Publish the already validated toolkit using the user's configured Git auth.

Credentials remain inside this process and Git Credential Manager. They are
never printed, saved, or placed in a remote URL. This script refuses another
account and never overwrites an existing remote repository or release.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OWNER='Makashibata02'
NAME='ai-literacy-toolkit'
REPO=OWNER+'/'+NAME
API='https://api.github.com'


def credentials():
    result=subprocess.run(['git','-c','credential.interactive=never','credential','fill'],input='protocol=https\nhost=github.com\nusername='+OWNER+'\n\n',text=True,capture_output=True,check=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    if not values.get('password'):raise RuntimeError('No configured GitHub credential; user authentication is required.')
    return values['password']


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['check-auth','create','pages','release','status'])
    args=p.parse_args();token=credentials()
    def request(path,method='GET',payload=None,data=None,content_type=None):
        url=path if path.startswith('https://') else API+path
        headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,'X-GitHub-Api-Version':'2026-03-10','User-Agent':'ai-literacy-toolkit-publisher'}
        if payload is not None:data=json.dumps(payload).encode();content_type='application/json'
        if content_type:headers['Content-Type']=content_type
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method=method,data=data,headers=headers),timeout=45) as r:
                body=r.read();return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            message=e.read().decode(errors='replace')[:500]
            raise RuntimeError(f'GitHub HTTP {e.code}: {message}') from None
    profile=request('/user')
    if profile.get('login')!=OWNER:raise RuntimeError('Configured account does not match the requested repository owner.')
    if args.action=='check-auth':
        existing=request('/repos/'+REPO)
        print(json.dumps({'login':profile['login'],'repository_exists':existing is not None,'can_publish':True}))
    elif args.action=='create':
        if request('/repos/'+REPO) is not None:raise RuntimeError('Repository already exists; refusing to overwrite it.')
        result=request('/user/repos','POST',{'name':NAME,'description':'AI 信息素养比赛速查：离线阅读、Agent 知识包、证据与检索操作卡。','private':False,'auto_init':False,'has_issues':True,'homepage':'https://makashibata02.github.io/ai-literacy-toolkit/'})
        print(json.dumps({'url':result['html_url'],'private':result['private']}))
    elif args.action=='pages':
        existing=request('/repos/'+REPO+'/pages')
        result=existing or request('/repos/'+REPO+'/pages','POST',{'build_type':'workflow'})
        print(json.dumps({'html_url':result.get('html_url'),'status':result.get('status'),'build_type':result.get('build_type')}))
    elif args.action=='release':
        tag='v1.0.0'
        if request('/repos/'+REPO+'/releases/tags/'+tag):raise RuntimeError('Release already exists; refusing to replace assets.')
        release=request('/repos/'+REPO+'/releases','POST',{'tag_name':tag,'target_commitish':'main','name':'v1.0.0 · AI 信息素养比赛速查','body':'轻量、可离线阅读的比赛查题资料库，含 50 个模块、25 张操作卡、53 个平台、168 道历史题和 93 条培训样题。\n\n下载 toolkit-full.zip 后打开 index.html；Agent 可读 agent/START_HERE.md。其余文件为 Agent、聊天 AI 和离线阅读用途包。每个 ZIP 附 SHA-256 校验值。\n\n只有 6 道原题答案经用户确认；候选提示与培训样题分别标记。原始视频、PPT、PDF及题图尚未上传。','draft':False,'prerelease':False})
        upload=release['upload_url'].split('{')[0]
        assets=[]
        for path in sorted((ROOT/'dist').glob('*')):
            if not path.is_file() or not (path.name.endswith('.zip') or path.name.endswith('.sha256')):continue
            result=request(upload+'?name='+urllib.parse.quote(path.name),'POST',data=path.read_bytes(),content_type='application/zip' if path.suffix=='.zip' else 'text/plain')
            assets.append({'name':result['name'],'size':result['size'],'url':result['browser_download_url']})
        print(json.dumps({'url':release['html_url'],'assets':assets},ensure_ascii=False))
    else:
        repo=request('/repos/'+REPO)
        runs=request('/repos/'+REPO+'/actions/runs?per_page=6') or {}
        pages=request('/repos/'+REPO+'/pages') or {}
        print(json.dumps({'url':repo.get('html_url') if repo else None,'default_branch':repo.get('default_branch') if repo else None,'pages':{k:pages.get(k) for k in ['html_url','status','build_type']},'runs':[{k:r.get(k) for k in ['id','name','status','conclusion','html_url','head_sha']} for r in runs.get('workflow_runs',[])]},ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except (RuntimeError,subprocess.CalledProcessError,urllib.error.URLError) as e:
        # Do not include command stdout, environment, or request objects.
        print(str(e) if isinstance(e,RuntimeError) else 'Publication failed; inspect authenticated connectivity or Git configuration.',file=sys.stderr)
        raise SystemExit(1)
