# 本地检索和维护

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

资料快照为 2026-10-12，提取自 ai-literacy-wiki 的结构化资料。包括 50 个模块、25 张操作卡、53 个平台档案、168 道历史题、146 个来源记录和 93 条培训样题。

27 个草稿来源及 1 个含冲突的来源不进入默认推荐。复核缺口见 [待复核清单](review-queue.md)，原始记录和哈希映射保留在结构化数据中。
