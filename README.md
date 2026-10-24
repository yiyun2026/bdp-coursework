# 云计算与大数据处理 课程实验

学号：2410311308　姓名：龚治榕　班级：24计科3

本仓库存放《云计算与大数据处理》课程各次实验的代码、运行证据与截图。各次实验的报告单独提交给授课老师。

## 目录结构

```
lab01/                                   实验 01 云端数据接口与可复现环境
├── evidence/                            原生运行证据，JSON 与同名 HTML 成对
├── screenshots/                         截图，evidence- 为浏览器证据页，step- 为命令行过程
├── code/                                个人修改后的脚本、原附件与 diff
└── downloaded-events.jsonl              S3 往返下载副本
```

## 实验 01 摘要

**数据**：`coursekit seed --rows 20000`，固定种子 seed=42，写入 `data/raw/events.jsonl`，共 20,102 行（20,000 条合法唯一事件 + 100 条完全重复事件 + 2 条不合法事件），文件 3,892,184 字节。

原始文件 SHA-256：

```
0d93bcd25e28047f804238c220bdb5b1d2dadf328647c07de85ba0104e8e2854
```

**对象存储往返**：桶 `bdp-teaching`，对象键 `bronze/events/<源文件SHA-256>.jsonl`，通过本机 Moto 模拟的 S3 HTTP 服务上传与下载。原始与下载副本摘要相同，`hash_matches = true`，`version_ids_differ = true`。

**个人修改**：`make_key()` 由共享前缀 `shared/raw/demo.json` 改为 `students/2410311308/raw/demo.json`，避免不同提交者的对象互相覆盖。

**三次对照结果**：

| 运行 | 对象键 | 内容 SHA-256 | 一致 |
|---|---|---|---|
| 基线 | `shared/raw/demo.json` | `23c0b20c65b4476c7e541044c09c88cd970bb02191681f804daef0b7ba49f0e8` | true |
| 改对象键 | `students/2410311308/raw/demo.json` | 同上，未变 | true |
| 改 payload（requests 3→4） | `students/2410311308/raw/demo.json` | `5657a58e4a955dcf741239aed81c7a600ca434c4b6c738557b8683d12b09d3f6` | true |

对象键变化不影响内容摘要，payload 变化才会改变摘要，证实摘要只由字节决定。

**故障与恢复**：将 endpoint 指向 `http://127.0.0.1:1` 得到 `EndpointConnectionError`（退出码 1），去掉参数后重新运行恢复正常，得到新的 run_id 并再次通过双哈希核对。

## 运行证据索引

| stage | run_id | 说明 |
|---|---|---|
| start | `55265e5e4a3140aeb926e097a13c7d45` | 身份登记 |
| probe-01 | `79e5ce682cc248b8b49d15d463d979c9` | 解释器版本与路径 |
| environment | `2e11f1746eec4561a33b412e31208b30` | pip check |
| probe-02 | `d13c3b0f0bee46df98bfad2fe0f47290` | 数据行数与首条事件 |
| verify | `983c601db37545de84751d7edcf7f01e` | 对象存储往返主实验 |
| student_object_roundtrip | `7ee816587ad44a0da9fa53a07c08c611` | 附件基线 |
| student_object_roundtrip | `28842a77ed8c4dbe95b930ac478fc2e3` | 改对象键 |
| student_object_roundtrip | `8a31f29580b54ba58f2ce2efa19fefa5` | 改 payload |
| expected-failure | `fc672d5db99b41999b508b48746f21b7` | 无效 endpoint 连接失败 |
| failed-lab01 | `c566e54cffd34ac39dd174b8bb47d2e2` | 失败的内层运行记录 |
| recovered | `d74f7fc7c3a2455c87fb7bf25b4d377f` | 恢复运行 |
| final | `fe0288c57b864d88a93a74d29aec4e3` | 最终身份登记 |

所有证据文件的 `_evidence` 中 `student_id` 为 `2410311308`、`experiment_id` 为 `01`。

## 截图索引

`lab01/screenshots/` 下两类：

- `evidence-*.png`：在 Chrome 打开的课程证据页，原生显示学号、实验号 01、run_id 与真实结果
- `step-*.png`：命令行操作过程截图

| 文件 | 内容 |
|---|---|
| evidence-01-probe-01 | 解释器版本与路径 |
| evidence-02-environment | 依赖检查结果 |
| evidence-03-probe-02 | 数据行数与首条事件 |
| evidence-04-verify | 对象存储往返主实验 |
| evidence-05-baseline | 个人练习基线 |
| evidence-06-change-key | 改对象键后 |
| evidence-07-change-payload | 改 payload 后 |
| evidence-08-expected-failure | 连接失败 |
| evidence-09-recovered | 故障恢复 |
| step-01-env-pip | 设置编码与 pip check |
| step-02-identity | 登记学号 |
| step-03-capture | 采集环境证据 |
| step-04-seed | 生成数据 |
| step-05-lines | 确认数据行数 |
| step-06-lab01 | 运行主实验 |
| step-07-baseline | 个人练习基线 |
| step-08-change-key | 改对象键 |
| step-09-change-payload | 改 payload |
| step-10-diff | 生成代码差异 |
| step-11-failure | 注入故障 |
| step-12-recovered | 故障恢复 |
| step-13-final | 最终确认 |

## 环境

- Windows 10.0.26200（64 位），CPU 运行
- Python 3.12.10，解释器 `.venv\Scripts\python.exe`
- boto3 1.43.93、moto 5.2.3、pandas 3.0.5、duckdb 1.5.5、dask 2026.8.0
- `pip check`：No broken requirements found
- 依赖对照 `requirements.lock.txt`，99 个包版本全部一致

## 说明

对象存储为 Moto 在本机启动的临时模拟服务，不是真实云存储。已验证本地 HTTP 请求真实发出、S3 接口语义可用、字节层面内容一致；未验证事件数据业务合法性、云存储耐久性、跨机容灾与真实 IAM。服务停止后内存对象即消失，跨实验保留的数据源是本地 `data/raw/events.jsonl`。

本仓库不包含课程仓库本体、`.venv`、模型权重或缓存。
