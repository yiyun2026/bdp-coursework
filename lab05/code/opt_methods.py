import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from coursekit.intelligence import search

question = "用户每周的 CPU 推理配额是多少分钟？"
print("问题:", question)
print()
for m in ("tfidf", "bm25", "hybrid"):
    hits = search(question, method=m, k=5)
    print(f"{m:8}", [(h["doc_id"], round(h["score"], 5)) for h in hits])
