### Retrieval only (dev, top-3, filter: user-given question filter (Day 6 strategy C))

| Method | Hit@1 | Evidence Hit@3 | Hit@10 | MRR@10 | Context Evidence (budget) | Median ms |
|---|---|---|---|---|---|---|
| dense | 11/15 | 12/15 | 14/15 | 0.781 | 4/15 (800 chars) | 100.2 |
| bm25 | 13/15 | 15/15 | 15/15 | 0.922 | 5/15 (800 chars) | 1.2 |
| hybrid_rrf | 11/15 | 13/15 | 15/15 | 0.827 | 4/15 (800 chars) | 94.3 |

### Agent (dev)

| Config | Method, top-k, budget, max searches | Context Evidence | Answered (answerable) | False refusal | Abstention (unanswerable) | Citation ids in context | Searches dist. | Median s | Tokens in/out | Cost USD | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_k3_b800 | dense, k=3, 800 chars, 3 | 4/15 | 5/15 | 10/15 | 2/2 | 5/5 | {'1': 7, '3': 10} | 4.11 | 29301/1585 | 0.00535 | 0 |
| bm25_k3_b800 | bm25, k=3, 800 chars, 3 | 4/15 | 3/15 | 12/15 | 2/2 | 3/3 | {'1': 3, '2': 1, '3': 13} | 4.15 | 34016/1611 | 0.00607 | 0 |
| hybrid_k3_b800 | hybrid_rrf, k=3, 800 chars, 3 | 5/15 | 6/15 | 9/15 | 2/2 | 6/6 | {'1': 7, '2': 1, '3': 9} | 4.11 | 29440/1647 | 0.0054 | 0 |
| dense_k3_b4000 | dense, k=3, 4000 chars, 3 | 12/15 | 12/15 | 3/15 | 2/2 | 15/15 | {'1': 13, '2': 1, '3': 3} | 2.89 | 33681/1730 | 0.00609 | 0 |
| bm25_k3_b4000 | bm25, k=3, 4000 chars, 3 | 13/15 | 15/15 | 0/15 | 2/2 | 17/17 | {'1': 16, '3': 1} | 2.79 | 25675/1777 | 0.00492 | 0 |
| hybrid_k3_b4000 | hybrid_rrf, k=3, 4000 chars, 3 | 12/15 | 14/15 | 1/15 | 2/2 | 16/16 | {'1': 15, '3': 2} | 2.75 | 29362/1780 | 0.00547 | 0 |
| bm25_rerank_k3_b4000 | bm25_rerank, k=3, 4000 chars, 3 | 15/15 | 15/15 | 0/15 | 2/2 | 19/19 | {'1': 14, '2': 1, '3': 2} | 4.2 | 29921/1896 | 0.00563 | 0 |
