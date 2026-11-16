### Retrieval only (test, top-3, filter: user-given question filter (Day 6 strategy C))

| Method | Hit@1 | Evidence Hit@3 | Hit@10 | MRR@10 | Context Evidence (budget) | Median ms |
|---|---|---|---|---|---|---|
| dense | 2/5 | 5/5 | 5/5 | 0.667 | 1/5 (800 chars) | 76.2 |
| bm25 | 2/5 | 3/5 | 3/5 | 0.5 | 1/5 (800 chars) | 1.3 |
| hybrid_rrf | 2/5 | 4/5 | 5/5 | 0.62 | 1/5 (800 chars) | 72.6 |
| bm25_rerank | 3/5 | 4/5 | 4/5 | 0.7 | 1/5 (800 chars) | 1012.6 |

### Agent (test)

| Config | Method, top-k, budget, max searches | Context Evidence | Answered (answerable) | False refusal | Abstention (unanswerable) | Citation ids in context | Searches dist. | Median s | Tokens in/out | Cost USD | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_k3_b800 | dense, k=3, 800 chars, 3 | 0/5 | 0/5 | 5/5 | 2/2 | 0/0 | {'0': 1, '3': 6} | 4.37 | 14380/620 | 0.00253 | 0 |
| bm25_rerank_k3_b4000 | bm25_rerank, k=3, 4000 chars, 3 | 4/5 | 4/5 | 1/5 | 2/2 | 5/5 | {'1': 5, '3': 2} | 4.32 | 16499/780 | 0.00294 | 0 |
