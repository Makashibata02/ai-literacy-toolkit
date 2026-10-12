# AI 信息素养比赛速查

把题目变成可执行的查找路径：找到平台、选对字段、取得证据、核对选项。

本库从既有 ai-literacy-wiki 结构化资料提取，资料快照为 2026-10-12。包含 50 个模块、25 张重点操作卡、53 个合并别名后的平台档案、168 道历史题、146 个来源记录和 93 条培训样题。操作卡集中覆盖优先查题任务；所有模块均可追溯到来源，未覆盖的操作会明确显示缺口。

## 立即使用

- 人类用户：[双击离线首页](index.html) → 搜索平台或任务 → 打开操作卡。
- Agent：[使用指引](agent/START_HERE.md) → [任务目录](agent/task-index.md) → 操作与证据。
- 上传文件的聊天 AI：[精简总包](llms-full.txt)，或上传 agent/ 中的主题分片。
- 纯 Markdown：[Wiki 目录](wiki/index.md)；[账号准备](docs/preparation.md)。
- 在线页面：[GitHub Pages](https://makashibata02.github.io/ai-literacy-toolkit/)。
- 打包下载：[GitHub Releases](https://github.com/Makashibata02/ai-literacy-toolkit/releases)。toolkit-full.zip 为完整包；agent-pack.zip、chatgpt-pack.zip、offline-reader.zip 为用途分包，均有 SHA-256 校验文件。

## 资料状态

只有 6 道原题答案经用户人工确认；其他题目答案仍未验证。有出处的候选提示单独展示，不能直接采纳。题目文字审核、答案确认和培训样题发布来源是不同状态。

27 个草稿来源及 1 个含冲突的来源不进入默认推荐。原始视频、PPT、PDF、题图均未上传。原件链接预留在 data/curated/media.json，当前 URL 为 null，不承诺原件可下载。

## 维护和验证

基础命令使用 Python 标准库，不需要模型、API Key、OCR 或向量运行环境。

```text
python -m app kb search "标准 ICS 分类" --top-k 5
python -m app kb status
python -m app kb build
python -m app kb lint --strict
python -m app.validate_readable
python -m pytest
python -m app kb package --target all
```

测试环境另装 pytest。所有网页、Wiki 和 Agent 文件由 data/curated/ 生成，禁止独立手改结论。scripts/extract.py 只读取原项目已整理字段；相同数据重复提取不覆盖，输入变化必须重新审核。

## 来源、权利与引用

代码 MIT；原创整理内容 CC BY 4.0。引用应注明 ai-literacy-wiki contributors、ai-literacy-toolkit 和资料日期。第三方资料、引用、商标与原件遵循原作者权利，不由本库统一重新授权。见 LICENSE、LICENSE-CONTENT 和 CITATION.cff。
