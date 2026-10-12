# 数据清洗，可以用excel工具

ID: `vid-4e58b20c511d6cdd` · 类型：历史来源 · 审核：`machine_reviewed`

本视频介绍用Excel函数做数据清洗的三个例子：一是用TRIM函数（=TRIM(A1)）去除首尾及多余空格、仅留单词间一个空格；二是用CLEAN函数（=CLEAN(A1)）删除非打印字符（含手动换行符）将多行合并为一行；三是用MID配合FIND函数按起始位置和长度11提取手机号；均可用Ctrl+D向下填充。相关函数还有LEFT、RIGHT、LEN、REPLACE、SUBSTITUTE、CONCAT等。

## 操作与核对

1. 在Excel的B1单元格输入“=TRIM(A1)”并回车，可去除A1中首尾及多余的空格（仅保留单词间一个空格），再用Ctrl+D向下自动填充。
2. 在Excel的B1单元格输入“=CLEAN(A1)”并回车，可删除单元格中的非打印字符（包括手动换行符），将多行内容合并为一行，再用Ctrl+D填充。
3. 在Excel中用MID配合FIND函数，以FIND确定的字符起始位置和长度11提取手机号码，再用Ctrl+D填充。

- 历史教学材料；示例答案、数量、排名、界面和版本不能直接用于当前题目。


## 证据定位

- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 00:56 · : 用TRIM函数去除多余空格。
- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 02:02 · : 用CLEAN函数删除所有非打印字符，包括手动换行符。
- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 03:38 · : FIND函数用于确定某个字符在文本中出现的位置。
- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 04:14 · : Excel中用于数据清洗的函数包括字符清除函数TRIM、CLEAN，字符提取函数MID，位置确定函数FIND。
- [vid-4e58b20c511d6cdd](vid-4e58b20c511d6cdd.md) · 04:24 · : 与数据清洗相关的函数还有LEFT、RIGHT、LEN、REPLACE、SUBSTITUTE、CONCAT等。
