# 云计算与大数据处理 课程实验

学号：2410311308　姓名：龚治榕　班级：24计科3

本仓库用于提交《云计算与大数据处理》课程各次实验的材料。每次实验的报告由本人撰写，放在对应的 `labXX/` 目录下。

## 目录说明

| 目录 | 内容 |
|---|---|
| `lab01/` | 实验 01 云端数据接口与可复现环境 |
| `lab01/report.md` | 实验 01 报告（本人撰写） |
| `lab01/evidence/` | 本次运行的原生证据：`coursekit.run` JSON 与同名 HTML 成对 |
| `lab01/code/` | 个人修改后的脚本、原附件、代码差异 |

## 实验 01 摘要

- 数据：`coursekit seed --rows 20000`，`data/raw/events.jsonl` 共 20,102 行（20,000 合法 + 100 重复 + 2 非法），SHA-256 `0d93bcd25e28047f804238c220bdb5b1d2dadf328647c07de85ba0104e8e2854`。
- 往返：桶 `bdp-teaching`，对象键 `bronze/events/<sha256>.jsonl`，原始与下载摘要一致，`hash_matches = true`，`version_ids_differ = true`。
- 个人改动：`make_key()` 改为 `students/2410311308/raw/demo.json`；另做一次 payload 数值对照。
- 故障恢复：无效 endpoint 连接失败已记录，恢复后重新核对通过。

## 说明

本仓库不包含课程仓库本体、`.venv`、模型权重或缓存；运行环境与原始数据保留在本地课程工作区。
