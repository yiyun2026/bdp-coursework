# 云计算与大数据处理 课程实验

学号：2410311308　姓名：龚治榕　班级：24计科3

本仓库存放《云计算与大数据处理》课程各次实验的报告、代码、运行证据与截图。

## 目录结构

```
2410311308_龚治榕_实验01云端数据接口与可复现环境.docx     实验 01 报告 Word 版
2410311308_龚治榕_实验01云端数据接口与可复现环境.pdf      实验 01 报告 PDF 版
2410311308_龚治榕_实验02数据湖与质量契约.docx             实验 02 报告 Word 版
2410311308_龚治榕_实验02数据湖与质量契约.pdf              实验 02 报告 PDF 版

lab01/                                   实验 01 云端数据接口与可复现环境
├── evidence/                            coursekit.run 的 JSON 与同名 HTML 成对；
│                                        另含 evidence-01..09 共 9 张浏览器证据页评分截图
├── screenshots/                         step-01..13 共 13 张命令行过程截图
├── code/                                个人修改后的脚本、原附件与 make_key.diff
└── downloaded-events.jsonl              S3 往返下载副本

lab02/                                   实验 02 数据湖与质量契约
├── evidence/                            coursekit.run 的 JSON 与同名 HTML 成对；
│                                        另含 evidence-01..12 共 12 张评分截图
├── code/                                student_quality_policy.py、optional_format_compare.py、原附件
├── results/                             quality.json、quarantine.json、query-plan.txt、
│                                        student-policy-2000.json、student-policy-1200.json 及 identity 旁证
└── optional/                            选做的 comparison.json 与两份查询计划

lab03/                                   实验 03 分布式批处理与性能分析
├── evidence/                            coursekit.run 的 JSON 与同名 HTML 成对；
│                                        另含 evidence-01..11 共 12 张评分截图
├── code/                                student_latency_aggregate.py、latency_errors.diff、
│                                        optional_shuffle_compare.py、原附件与核验器
├── results/                             三份 benchmark-*.json、student-latency-1000/2000.json、
│                                        optional-shuffle-compare.json 及 identity 旁证
└── screenshots/                         step-01..20 共 20 张命令行过程截图

lab04/                                   实验 04 增量事件处理与故障恢复
├── evidence/                            coursekit.run 的 JSON 与同名 HTML 成对；
│                                        另含 evidence-01..12 共 12 张评分截图
├── code/                                student_atomicity.py、atomicity.diff、
│                                        optional_daily_recompute.py、原附件
├── results/                             replay.json、latest.json、realtime_service.json、
│                                        student-atomicity-early/atomic.json、
│                                        optional-daily-recompute.json 及 identity 旁证
└── screenshots/                         step-01..16 共 16 张命令行过程截图
```

评分截图（`evidence-*.png`）统一放在各实验的 `evidence/` 下，命令行过程截图（`step-*.png`）统一放在 `screenshots/` 下。

## 实验 02 摘要

**数据来源**：复用实验 01 生成的 `data/raw/events.jsonl`，20,102 行，未重新生成。

**基线质量**：原始 20,102 行 → 合法独特 20,000、重复 100、隔离 2，守恒 20,102。两条被隔离记录分别为第 20101 行 `bad-negative`（`input_tokens` 为 -1，原因 `invalid_input_tokens`）和第 20102 行 `bad-time`（`event_time` 为 `not-a-time`，原因 `invalid_event_time`）。

**Parquet 与 SQL**：Silver 20,000 行、5 个行组、8 个字段；Gold 每日汇总 6 行。Silver 总量 (20000, 18015640, 6145862) 与 Gold 按 requests 求和完全一致，`totals_match` 为 true。

**个人改动**：阈值 2000 → 1200。

| 规则 | 原始 | 合法独特 | 重复 | 拒绝 | 输入 Token 总量 |
|---|---:|---:|---:|---:|---:|
| 基础课程契约 | 20102 | 20000 | 100 | 2 | 18015640 |
| 附加上限 2000 | 20102 | 20000 | 100 | 2 | 18015640 |
| 附加上限 1200 | 20102 | 13405 | 67 | 6630 | 8110488 |

重复数由 100 降到 67，因为程序先校验再去重，被阈值拒绝的原始重复行进入了拒绝计数。

**坏样本探针**：负数返回 `invalid_input_tokens`；布尔值 `True` 返回 `invalid_input_tokens`；无时区时间返回 `non_utc_time`；把布尔值换成字符串 `"100"` 后错误类型不变。

**选做扩展**：同一份 Silver 数据比较三种存储格式，预热 3 次、测量 7 次取中位数。

| 格式 | 字节数 | 相对 CSV | 中位耗时 |
|---|---:|---:|---:|
| CSV | 1,612,574 | 1.00 | 92.643 ms |
| Parquet 未压缩 | 1,250,207 | 0.78 | 5.028 ms |
| Parquet Zstd | 224,693 | 0.14 | 5.329 ms |

三种格式聚合结果一致。Parquet 比 CSV 快约 18 倍，但未压缩与 Zstd 耗时几乎相同，说明加速主要来自列裁剪与类型已知，而非压缩；Zstd 把体积压到 14% 却没有带来速度提升。

## 实验 03 摘要

**输入继承**：复用实验 02 的 `data/silver/events.parquet`，20,000 行，SHA-256 `516b3d78aab91c1487d9a24979eaef514c5acb7309d0d82a6688a762836634dc`，与清单一致。

**三配置受控对照**（数据、聚合口径完全相同，只改 Worker 数与分区数）：

| 配置 | 不同 PID | 任务数 | 启动秒 | 主计算秒 | 总秒 | SQL 一致 |
|---|---:|---:|---:|---:|---:|---|
| w1p8 | 1 | 115 | 1.053 | 1.535 | 3.209 | true |
| w2p8 | 2 | 115 | 1.058 | 2.353 | 3.924 | true |
| w2p4 | 2 | 43 | 1.067 | 2.277 | 3.773 | true |

两 Worker 主计算 2.353 秒反而比一 Worker 的 1.535 秒慢，加速比 0.65。原因是 20,000 条数据量下进程启动、序列化与调度开销占主导。

**分区倾斜**：`partition_rows_after_shuffle` 为 `[2023, 0, 14008, 3969, 0, 0, 0, 0]`，非空分区仅 3 个，最大分区 14008 行，与「只有三个服务键」一致；增加分区数只会增加空分区。

**个人改动**：慢请求阈值 1000 → 2000，`slow_requests` 由 10589/1519/3043 降至 7120/1011/2041，请求数与延迟总和不变。补全 `errors` 与 `error_rate` 四处逻辑后，核验器输出 `ERROR_EXTENSION_PASS {'total_errors': 800}`。

| 服务 | requests | errors | error_rate | slow_requests(2000) | slow_rate |
|---|---:|---:|---:|---:|---:|
| assistant | 14008 | 543 | 0.038764 | 7120 | 0.508281 |
| batch | 2023 | 78 | 0.038557 | 1011 | 0.499753 |
| search | 3969 | 179 | 0.045100 | 2041 | 0.514235 |

**手算核对**：assistant 平均延迟 28448309 / 14008 = 2030.861579 ms，慢请求率 7120 / 14008 = 0.508281，错误率 543 / 14008 = 0.038764，三项均与 JSON 一致。

**选做：显式 Shuffle 与可合并聚合**

| 指标 | 显式 Shuffle | 不 Shuffle |
|---|---:|---:|
| 任务数 | 115 | 19 |
| 非空分区 | 3 | 8 |
| 分区行数 | [2023,0,14008,3969,0,0,0,0] | [2500 × 8] |
| 主计算秒 | 2.5053 | 2.5343 |
| 结果一致 | true | true |

任务数相差约 6 倍，耗时只差约 1%。说明任务数不是性能指标本身；显式 Shuffle 得到的是「按键分区」，不 Shuffle 得到的是「按行均分」，后者看着均匀但每个分区混着三种服务。

## 实验 04 摘要

**前置输入**：复用实验 02 的 `data/silver/events.parquet`，20,000 行，Silver 哈希 `516b3d78…34dc`。

**分阶段结果**（主实验 run_id `eb5ee566e949`）：

| 阶段 | 新增 | 可见总行数 | 检查点 |
|---|---:|---:|---:|
| 初始微批完成 | 20000 | 20000 | 20000 |
| 重放前 100 条 | 0 | 20000 | 20000 |
| 提交前失败并回滚 | 0 | 20000 | 20000 |
| 关闭连接后恢复 | 1 | 20001 | 20001 |
| 接受晚到事件 | 1 | **20002** | **20002** |

数据库摘要 `45364a03…80ddb`，统计摘要 `d9d4eb24…466c`。只读核验 `matches_gold` 为 true。

**三种行数必须区分**：原始 JSONL 20,102 行（含 100 条重复 + 2 条非法）→ 实验 02 清洗后 20,000 条合法唯一 → 本章新增 `increment-new` 与 `increment-late` 两个新 ID → 20,002。

**四状态手算**：

| 场景 | 可见事件数 | 检查点 | 重放 |
|---|---:|---:|---|
| 同事务成功提交 | 4 | 4 | 不需要 |
| 提交前异常并回滚 | 3 | 3 | 整批重放 |
| 数据先提交、检查点未更新 | 4 | 3 | 重放靠去重兜住 |
| 检查点先提交、数据未写入 | 3 | 4 | **无法修复，永久丢失** |

后两个方向不对等：数据先落地能靠主键去重补救，进度先落地则重放根本不会发生。

**练习 A（修复提前提交）**：修改前 `atomic_contract_passed=false`、`rows_after_failure=1`、`offset_after_failure=0`；把 `COMMIT_EARLY` 改为 `False` 后 `atomic_contract_passed=true`、`rows_after_failure=0`、`final_rows=1`。diff 只有一行。

**选做：按日汇总与晚到重算**

晚到事件 `increment-late`（2026-02-28T23:59:00，assistant，input 1538 / output 291）落在主数据 3 月 1 日与 3 月 2 日之外，因此它新增了 `2026-02-28|assistant` 一个分组（1 条请求），既有日期分组计数完全不变。总请求数 20001 → 20002。按 `(day, service)` 缓存时需失效的键为 `2026-02-28|assistant`。

若晚到事件落在已有日期内，则会改写那一天的计数（例如 `2026-03-01|assistant` 由 12142 变 12143），这才是真正的历史改写；全历史按服务汇总看不出这个差别。

**语义边界**：注入的是受控 Python 异常，在 `commit()` 之前抛出并 rollback；没有断电、没有杀进程、没有网络分区。效果范围是单 SQLite 数据库内的事务提交与事件 ID 去重，不能表述为 Kafka exactly-once。本章未实现 watermark。

## 实验 04 运行证据索引

| stage | run_id | 说明 |
|---|---|---|
| start | `9735e149cafd4a17992c615fb20a58bb` | 身份登记 |
| verify | `ebd1727639f94c099a29c2006944931a` | 主实验全部阶段（第一次） |
| verify | `5587f4aa7c424c86b74f4b50216f15a8` | 主实验全部阶段（第二次） |
| inspect_state | `3a53f15664204358ad79f583b259c68b` | 只读检查数据库 |
| student_atomicity | `c71769aa4ec24dfe894ab4adce69a536` | 练习 A 修复前（失败） |
| student_atomicity | `571618fbecab4b8589c6f2a0c9fa4bee` | 练习 A 修复后（通过） |
| optional_daily_recompute | `1a41c52df1a54b0ea24341d148b58787` | 选做按日重算 |
| final | `aab839ba415a4bd0b7a3ec8e7fe4dc05` | 最终身份登记 |

## 实验 03 运行证据索引

| stage | run_id | 说明 |
|---|---|---|
| start | `f9968f40d31e4b788197b0da3edf76cb` | 身份登记 |
| probe-01 | `b29bf94d127d409ca89f3fd7fcde328b` | Silver 行数与哈希核验 |
| verify | `7ddeafe4dda0443bbe57dfc7d3fbabf3` | w1 p8 基准 |
| verify | `ef47743bd27f47cba531e902e4eafbe0` | w2 p8 基准 |
| verify | `c683aa0aa0a64ee382b057c8f9cbf4ae` | w2 p4 基准 |
| probe-02 | `4dea1306dde94d0eafb39e6374289af5` | 分区倾斜 |
| student_latency | `5f70c35b5e3a430992936f9f83156b52` | 阈值 1000 |
| student_latency | `d48e680043554ab7b8c6e8d5f52e1fae` | 阈值 2000 |
| check_error_extension | `8b580a0ca9ed45a982b8b5b6ed1206b3` | 错误统计专项核验 |
| expected-failure | `7aa7a37e1f014c04b07fde7ef3efcd7e` | workers=0 配置拒绝 |
| optional_shuffle_compare | `63b3cb6fae2e44d1a02ab98930664183` | 选做 Shuffle 对比 |
| final | `dcbcd08e325549afb0ea45f7eddd3c61` | 最终身份登记 |

## 实验 02 运行证据索引

| stage | run_id | 说明 |
|---|---|---|
| start | `cddfee846a1549db9abe3f1190d26d54` | 身份登记 |
| verify | `a578991845f842d88e8895d2e2c2db92` | 主流水线清洗与聚合 |
| probe-01 | `32a99557827a43d3927919b26ef2a504` | Parquet 结构与行组 |
| inspect_gold | `affccbecbf5c411bb7e60715e35bec69` | Silver 与 Gold 总量核对 |
| student_quality_policy | `4d92a580e80f43adb23a0303a7eb8303` | 阈值 2000 基线 |
| student_quality_policy | `98b0ab07a2cf44b48aa9d7e050eb220f` | 阈值 1200（首次运行，后被覆盖结果相同） |
| student_quality_policy | `1d25cc5ea3234e53968ed3cfc5dd931b` | 阈值 1200（正式留存） |
| student_quality_policy | `fff6ed51e2454113b8efa0e80040d802` | 字符串探针 `"100"` |
| probe-05 | `1a97d2117c334a7bb37fcf33588a2fe2` | 清单哈希核验 |
| optional_format_compare | `c3f8385aecd74e4f99473b74e102e62b` | 选做三种格式对比 |
| final | `07399fbd9f5542fe8b9bf22eb2b7ab2a` | 最终身份登记 |

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
