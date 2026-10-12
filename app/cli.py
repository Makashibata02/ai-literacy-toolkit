from __future__ import annotations

import argparse
import json
from .core import counts, data_digest, lint, search


def main():
    parser=argparse.ArgumentParser(description="离线比赛速查工具；基础功能无需安装依赖")
    top=parser.add_subparsers(dest="command",required=True)
    kb=top.add_parser("kb").add_subparsers(dest="action",required=True)
    kb.add_parser("build")
    finder=kb.add_parser("search")
    finder.add_argument("query")
    finder.add_argument("--top-k",type=int,default=5)
    finder.add_argument("--kind",choices=["task","platform","question","source"])
    finder.add_argument("--include-drafts",action="store_true")
    checker=kb.add_parser("lint");checker.add_argument("--strict",action="store_true")
    package=kb.add_parser("package");package.add_argument("--target",choices=["all","full","agent","chatgpt","offline"],default="all")
    kb.add_parser("status")
    args=parser.parse_args()
    code=0
    if args.action=="search":
        if not 1<=args.top_k<=100:
            parser.error("--top-k must be between 1 and 100")
        payload={"query":args.query,"results":search(args.query,args.top_k,args.kind,args.include_drafts)}
    elif args.action=="lint":
        payload=lint();code=int(args.strict and payload["status"]!="passed")
    elif args.action=="status":
        payload={"counts":counts(),"data_sha256":data_digest(),"media_status":"not_uploaded"}
    else:
        from .build import build, package_all
        payload=build() if args.action=="build" else package_all(args.target)
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    return code
