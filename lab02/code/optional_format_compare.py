"""选做扩展：同一清洗数据上比较 CSV、未压缩 Parquet、Zstd Parquet。

固定查询与测量范围：同一张 Silver 表、同一条聚合 SQL、同一台机器、同一进程，
每种格式预热 3 次后测量 7 次取中位数，避免首次读盘的冷缓存干扰。
只读数据，不改写 data/silver 与 data/gold。
"""
import json
import statistics
import sys
import time
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COURSE_ROOT))

from coursekit.common import DATA, OUT, write_json
from coursekit.evidence import capture_callable

REPEAT = 7
WARMUP = 3

# 固定查询：按服务汇总请求数与 Token，与手册第 7 节的 Gold 口径一致。
QUERY = """
SELECT service,
       COUNT(*) AS requests,
       SUM(input_tokens)::BIGINT AS input_tokens,
       SUM(output_tokens)::BIGINT AS output_tokens
FROM read_{fmt}(?)
GROUP BY service
ORDER BY service
"""


def timed(con, sql, path):
    start = time.perf_counter()
    rows = con.execute(sql, [str(path)]).fetchall()
    return (time.perf_counter() - start) * 1000.0, rows


def measure(con, sql, path):
    for _ in range(WARMUP):
        timed(con, sql, path)
    samples = sorted(timed(con, sql, path)[0] for _ in range(REPEAT))
    return {
        "median_ms": round(statistics.median(samples), 3),
        "min_ms": round(samples[0], 3),
        "max_ms": round(samples[-1], 3),
    }


def main():
    import duckdb
    import pyarrow as pa
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    src = DATA / "silver/events.parquet"
    work = OUT / "lab02" / "compare"
    work.mkdir(parents=True, exist_ok=True)

    table = pq.read_table(src)
    csv_path = work / "events.csv"
    pq_raw = work / "events_uncompressed.parquet"
    pq_zstd = work / "events_zstd.parquet"

    pv.write_csv(table, csv_path)
    pq.write_table(table, pq_raw, compression="none", row_group_size=4096)
    pq.write_table(table, pq_zstd, compression="zstd", row_group_size=4096)

    sizes = {
        "csv": csv_path.stat().st_size,
        "parquet_uncompressed": pq_raw.stat().st_size,
        "parquet_zstd": pq_zstd.stat().st_size,
    }

    con = duckdb.connect()
    plans = {}
    results = {}
    timings = {}

    for fmt, path, reader in (
        ("csv", csv_path, "csv_auto"),
        ("parquet_uncompressed", pq_raw, "parquet"),
        ("parquet_zstd", pq_zstd, "parquet"),
    ):
        sql = QUERY.format(fmt=reader)
        if reader == "csv_auto":
            # read_csv 的参数化写法不同，改为子查询形式保持同一测量范围。
            sql = ("SELECT service, COUNT(*) AS requests, "
                   "SUM(input_tokens)::BIGINT AS input_tokens, "
                   "SUM(output_tokens)::BIGINT AS output_tokens "
                   "FROM read_csv_auto(?, header=true) GROUP BY service ORDER BY service")
        timings[fmt] = measure(con, sql, path)
        results[fmt] = [list(map(str, row)) for row in timed(con, sql, path)[1]]
        plans[fmt] = con.execute("EXPLAIN " + sql, [str(path)]).fetchone()[1]

    same = results["csv"] == results["parquet_uncompressed"] == results["parquet_zstd"]
    assert same, "三种格式的聚合结果必须一致"

    baseline = sizes["csv"]
    summary = {
        "source": "data/silver/events.parquet",
        "rows": table.num_rows,
        "query": "按 service 分组统计 requests 与输入/输出 Token 总量",
        "repeat": REPEAT,
        "warmup": WARMUP,
        "formats": {
            name: {
                "bytes": sizes[name],
                "size_ratio_vs_csv": round(sizes[name] / baseline, 4),
                **timings[name],
            }
            for name in sizes
        },
        "results_identical": same,
        "timings": timings,
        "note": "同一进程、同一机器、同一查询；CSV 为 UTF-8 文本，Parquet 行组 4096。"
                "CSV 需要类型推断且无列裁剪，Parquet 带列统计与列式编码。",
    }

    write_json(work / "comparison.json", summary)
    (work / "query-plan-uncompressed.txt").write_text(plans["parquet_uncompressed"], encoding="utf-8")
    (work / "query-plan-zstd.txt").write_text(plans["parquet_zstd"], encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(capture_callable("02", "optional_format_compare", main))
