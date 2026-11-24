import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from coursekit.intelligence import search

# 一个和语料几乎无关的查询
q = "今天天气怎么样"
print("查询:", q)
print("tfidf:", [(h["doc_id"], round(h["score"], 6)) for h in search(q, method="tfidf", k=5)])
print("hybrid:", [(h["doc_id"], round(h["score"], 6)) for h in search(q, method="hybrid", k=5)])
