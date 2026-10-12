# Excel TRIM CLEAN MID FIND 数据清洗

ID: `task-excel-clean` · 类型：操作卡 · 审核：`machine_reviewed`

保留原列，在新列测试清洗公式。；用 TRIM 处理常见多余空格，用 CLEAN 处理常见非打印字符。

## 输入条件

从题干提取平台、对象、字段、时间、类型、排序指标及需要比较的选项文字。

## 操作与核对

1. 保留原列，在新列测试清洗公式。
2. 用 TRIM 处理常见多余空格，用 CLEAN 处理常见非打印字符。
3. 需要提取子串时，用 FIND 定位，再用 MID 截取。
4. 以题目示例逐条核对输出，再填充到其他行。

- 先检查字符类型和边界，不能假定所有空白都由同一公式清除。


## 证据定位

- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 00:56 · 2026-09-18: 用TRIM函数去除多余空格。
- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 02:02 · 2026-09-18: 用CLEAN函数删除所有非打印字符，包括手动换行符。
- [doc-d76af9a5e1f68182](doc-d76af9a5e1f68182.md) · 正文 · 2026-09-18: 熟练掌握 Excel 在数据处理中的应用，重点关注 LEFT、RIGHT、MID、FIND、TRIM、REPLACE、SUBSTITUTE、CONCAT、&、CLEAN、VLOOKUP、COUNTIF、COUNTIFS、SUMIF、SUMIFS、IF、INDEX、MATCH 等函数。
- [doc-d76af9a5e1f68182](doc-d76af9a5e1f68182.md) · 正文 · 2026-09-18: 探索：从百度 AI Studio、阿里云天池、OpenDataLab、OpenML 或 UCI Machine Learning Repository（Classic 版或 Beta 版）下载一个表格型数据集，查看其字段名称、样本数量、数据格式和缺失值情况。
