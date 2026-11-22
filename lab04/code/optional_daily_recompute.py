"""选做扩展：按日汇总与晚到重算。

本章主实验的 Gold 是全历史按服务汇总，看不出晚到事件改变了哪一天。
本脚本在最近一次运行的只有读数据库上做两件事：
  1. 对比“晚到事件到达前”与“到达后”的按日统计，定位被改写的日期；
  2. 模拟下游缓存：若按 (day, service) 缓存统计，需要失效哪些键。

只读打开数据库，不改动主实验状态。
"""
import json
import sqlite3
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COURSE_ROOT))
from coursekit.common import DATA, OUT, read_json, write_json
from coursekit.evidence import capture_callable

LATE_PREFIX = "increment-late"


def daily(con, exclude_late):
    where = "" if not exclude_late else "WHERE event_id <> ?"
    args = [] if not exclude_late else [LATE_PREFIX]
    rows = con.execute(f"""
        SELECT substr(event_time,1,10) AS day, service,
               COUNT(*) AS requests,
               SUM(input_tokens)::BIGINT AS input_tokens,
               SUM(output_tokens) AS output_tokens
        FROM events {where}
        GROUP BY day, service
        ORDER BY day, service
    """.replace("::BIGINT", ""), args).fetchall()
    return {
        f"{day}|{service}": {
            "day": day, "service": service,
            "requests": requests,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        for day, service, requests, input_tokens, output_tokens in rows
    }


def main():
    latest = read_json(DATA / "state/latest.json")
    db = Path(latest["database"])
    if not db.exists():
        raise FileNotFoundError(f"数据库不存在：{db}")

    # 只读连接，避免改动主实验状态
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        before = daily(con, exclude_late=True)
        after = daily(con, exclude_late=False)
        total_rows = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        checkpoint = con.execute("SELECT offset FROM checkpoint WHERE id=1").fetchone()[0]
        late_row = con.execute(
            "SELECT event_id, event_time, service, input_tokens, output_tokens "
            "FROM events WHERE event_id = ?", (LATE_PREFIX,)
        ).fetchone()
    finally:
        con.close()

    # 找出被晚到事件改写的日期与服务
    changed = []
    for key in sorted(set(before) | set(after)):
        b = before.get(key)
        a = after.get(key)
        if b is None or a is None or b != a:
            changed.append({
                "key": key,
                "before": b,
                "after": a,
                "delta_requests": (a["requests"] if a else 0) - (b["requests"] if b else 0),
                "delta_input_tokens": (a["input_tokens"] if a else 0) - (b["input_tokens"] if b else 0),
                "delta_output_tokens": (a["output_tokens"] if a else 0) - (b["output_tokens"] if b else 0),
            })

    # 同时给出“若按日缓存，哪些键需要失效”
    invalidated = [c["key"] for c in changed]

    total_before = sum(v["requests"] for v in before.values())
    total_after = sum(v["requests"] for v in after.values())

    result = {
        "database": str(db),
        "run_id": latest["run_id"],
        "total_rows": total_rows,
        "checkpoint": checkpoint,
        "late_event": {
            "event_id": late_row[0], "event_time": late_row[1], "service": late_row[2],
            "input_tokens": late_row[3], "output_tokens": late_row[4],
            "arrival": "本次处理的最后才到达，但事件时间早于绝大多数已有记录",
        },
        "total_requests_before_late": total_before,
        "total_requests_after_late": total_after,
        "changed_groups": changed,
        "cache_keys_to_invalidate": invalidated,
        "daily_before": sorted(before.values(), key=lambda r: (r["day"], r["service"])),
        "daily_after": sorted(after.values(), key=lambda r: (r["day"], r["service"])),
        "conclusion": {
            "rewritten_day": changed[0]["key"].split("|")[0] if changed else None,
            "rewritten_service": changed[0]["key"].split("|")[1] if changed else None,
            "explanation": (
                "晚到事件的事件时间为 2026-02-28，早于主数据的 2026-03-01 与 2026-03-02，"
                "因此它改写的是按日汇总中一个此前不存在的新日期，而不是已有日期的计数。"
                "全历史按服务汇总看不出这一点，只有按日分组后才能定位。"
            ),
        },
        "note": "本脚本只读打开数据库，不写入任何状态；晚到事件已由主实验接受并入库，"
                "这里做的是按日重算与缓存失效分析。本章未实现 watermark。",
    }
    target = OUT / "lab04/optional-daily-recompute.json"
    result = write_json(target, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(capture_callable("04", "optional_daily_recompute", main))
