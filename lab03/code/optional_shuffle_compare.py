"""选做扩展：显式 Shuffle 与可合并聚合的对比。

同一份 Silver、同样的 2 Worker 与 8 分区，只改变是否在聚合前显式按 service 做 hash 交换：
  配置 A：显式 shuffle(on='service')，与课程 lab03 基线一致
  配置 B：不 shuffle，直接 groupby，让引擎用可合并的分段聚合完成

两种配置都用独立 DuckDB SQL 核对结果，并记录任务数、分区行数、各阶段耗时。
只读数据，不改写 data/silver。
"""
import json
import os
import sys
import time
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COURSE_ROOT))
from coursekit.common import DATA, OUT, write_json
from coursekit.evidence import capture_callable

WORKERS = 2
PARTITIONS = 8


def run_config(mode, silver):
    import dask.dataframe as dd
    import duckdb
    from distributed import Client, LocalCluster

    started = time.perf_counter()
    with LocalCluster(n_workers=WORKERS, threads_per_worker=1, processes=True,
                      memory_limit="1GiB", host="127.0.0.1", dashboard_address=None) as cluster:
        with Client(cluster) as client:
            startup_s = time.perf_counter() - started
            df = dd.read_parquet(str(silver)).repartition(npartitions=PARTITIONS)
            if mode == "explicit_shuffle":
                frame = df.shuffle(on="service", shuffle_method="tasks")
                target = frame
            else:
                frame = df
                target = frame
            group = target.groupby("service").agg({
                "event_id": "count",
                "input_tokens": "sum",
                "output_tokens": "sum",
                "latency_ms": "sum",
            })
            task_count = len(group.__dask_graph__())
            compute_started = time.perf_counter()
            actual = group.compute().reset_index().rename(
                columns={"event_id": "requests", "latency_ms": "latency_ms_sum"})
            compute_s = time.perf_counter() - compute_started
            actual = actual.sort_values("service").reset_index(drop=True)
            # 分区行数：显式 shuffle 时看交换后的分布，否则看原始分区分布
            partition_rows = target.map_partitions(len).compute().tolist()
            worker_pids = client.run(os.getpid)
    total_s = time.perf_counter() - started

    with duckdb.connect() as con:
        baseline = con.execute("""SELECT service, COUNT(*)::BIGINT AS requests,
            SUM(input_tokens)::BIGINT AS input_tokens, SUM(output_tokens)::BIGINT AS output_tokens,
            SUM(latency_ms)::BIGINT AS latency_ms_sum
            FROM read_parquet(?) GROUP BY service ORDER BY service""", [str(silver)]).fetchdf()
    # 与 lab03 一致：按排序后的记录逐行比较，避免索引与 dtype 造成误判
    expected_rows = baseline[["service", "requests", "input_tokens",
                              "output_tokens", "latency_ms_sum"]].to_dict(orient="records")
    actual_rows = actual[["service", "requests", "input_tokens",
                          "output_tokens", "latency_ms_sum"]].to_dict(orient="records")
    equal = actual_rows == expected_rows

    return {
        "mode": mode,
        "workers": WORKERS,
        "partitions": PARTITIONS,
        "worker_pids": worker_pids,
        "distinct_pids": len(set(worker_pids.values())),
        "task_count": task_count,
        "partition_rows": partition_rows,
        "nonempty_partitions": sum(1 for x in partition_rows if x > 0),
        "max_partition_rows": max(partition_rows),
        "startup_seconds": round(startup_s, 4),
        "compute_seconds": round(compute_s, 4),
        "total_seconds": round(total_s, 4),
        "matches_duckdb": equal,
        "aggregate": actual_rows,
    }


def main():
    from coursekit.common import read_json, sha256
    silver = DATA / "silver/events.parquet"
    manifest = read_json(DATA / "manifests/silver.json")
    assert sha256(silver) == manifest["silver_sha256"], "Silver 哈希与清单不一致"

    results = {}
    for mode in ("explicit_shuffle", "no_shuffle"):
        results[mode] = run_config(mode, silver)

    summary = {
        "source": "data/silver/events.parquet",
        "rows": manifest["rows"],
        "silver_sha256": manifest["silver_sha256"],
        "workers": WORKERS,
        "partitions": PARTITIONS,
        "configs": results,
        "comparison": {
            "task_count": {
                m: results[m]["task_count"] for m in results
            },
            "compute_seconds": {
                m: results[m]["compute_seconds"] for m in results
            },
            "nonempty_partitions": {
                m: results[m]["nonempty_partitions"] for m in results
            },
        },
        "note": "两种配置数据、Worker 数、分区数、聚合口径完全相同，只改变是否显式按 service 交换。"
                "显式 Shuffle 的分区行数反映交换后的分布，no_shuffle 反映原始分区分布；"
                "两者分组结果都必须与 DuckDB 一致。",
    }
    target = OUT / "lab03" / "optional-shuffle-compare.json"
    summary = write_json(target, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(capture_callable("03", "optional_shuffle_compare", main))
