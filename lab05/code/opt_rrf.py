import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from coursekit.intelligence import search

question = "缓存键应包含哪些信息？"
a = search(question, method="tfidf", k=10)
b = search(question, method="bm25", k=10)
ra = {h["chunk_id"]: i + 1 for i, h in enumerate(a)}
rb = {h["chunk_id"]: i + 1 for i, h in enumerate(b)}
print("TF-IDF 排名:", [(h["chunk_id"], ra[h["chunk_id"]]) for h in a[:3]])
print("BM25   排名:", [(h["chunk_id"], rb[h["chunk_id"]]) for h in b[:3]])
print()
print("手算 RRF:")
for cid in list(ra)[:3]:
    p = 1 / (60 + ra[cid])
    s = 1 / (60 + rb[cid]) if cid in rb else 0
    print(f"  {cid}: 1/(60+{ra[cid]})={p:.6f} + {s:.6f} = {p+s:.6f}")
print()
h = search(question, method="hybrid", k=3)
print("程序 hybrid:", [(x["chunk_id"], round(x["score"], 6)) for x in h])
