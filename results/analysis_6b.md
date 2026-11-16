# 6b — Cải thiện #2: rerank cross-encoder trên BM25 (dev)

## Lựa chọn và giả thuyết (ghi trước khi chạy)

Ngày: 2026-11-16. Dựa trên lỗi còn lại sau 6a ([analysis_6a.md](analysis_6a.md)): đa số lỗi là
**retrieval xếp sai thứ hạng** — gold có trong top-20 nhưng ngoài top-3
(q07/bm25: gold p028:c01 hạng 5 với query của agent; q12 dense/hybrid; q15 dense).
Chỉ 1 trường hợp "evidence trong context nhưng abstain" (q01/dense) → không chọn sửa prompt.

- **Thay đổi duy nhất** so với cấu hình gốc `bm25_k3_b4000`: method `bm25` → `bm25_rerank`
  (BM25 lấy 20 candidate với cùng filter user-given, cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`
  chấm (query, passage) rồi giữ top-3). Giữ top_k=3, budget=4000, max_searches=3, filter_mode=given, prompt v1.
- **Giả thuyết**: cross-encoder đọc cả query và passage nên đưa được chunk trả lời trực tiếp
  (vd. p028:c01 "zeroth-order optimization … estimates the model's gradients") lên top-3 → q07 sửa được,
  Hit@1 retrieval tăng (BM25 13/15). Rủi ro: (a) model MS MARCO không quen thuật ngữ AML, có thể đẩy
  chunk đúng của BM25 xuống (Hit@3 BM25 đã 15/15, khó tăng); (b) thêm latency CPU cho 20 cặp/search;
  (c) abstention u01/u02 có thể hỏng nếu passage "gần chủ đề" được đưa lên — phải giữ 2/2.
- **Đo**: eval_retrieval (Hit@1, Hit@3, MRR@10 trên query gốc), run_agent dev, so với bm25_k3_b4000.

## Kết quả

### Retrieval (query gốc, dev, top-3, cùng filter) — [step3_dev_rerank/summary.json](step3_dev_rerank/summary.json)

| Method | Hit@1 | Evidence Hit@3 | Hit@10 | MRR@10 | Median ms/query |
|---|---|---|---|---|---|
| bm25 | 13/15 | 15/15 | 15/15 | 0.922 | 0.7 |
| bm25_rerank | 13/15 | 15/15 | 15/15 | 0.922 | 1007.3 (CPU, 20 cặp) |

Tổng bằng nhau là trùng hợp: rerank **lên hạng** gold ở q03 (hạng 2→1) và q15 (3→1) nhưng **xuống hạng** ở
q02 (1→3, đưa p017:c00 lên đầu — cũng chứa đáp án) và q10 (1→2). Với query gốc, giả thuyết "Hit@1 tăng" **không đúng**.

### Agent (dev) — chỉ đổi method so với bm25_k3_b4000

| Config | Context Evidence | Answered | Answered ∧ ctx gold | False refusal | Abstention u01/u02 | Citation ids in context | Searches | Median s | Tokens in/out | USD | Errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25_k3_b4000 | 13/15 | 15/15 | 13/15 | 0/15 | 2/2 | 17/17 | {1:16, 3:1} | 2.79 | 25675/1777 | 0.00492 | 0 |
| bm25_rerank_k3_b4000 | **15/15** | 15/15 | **15/15** | 0/15 | **2/2** | 19/19 | {1:14, 2:1, 3:2} | 4.20 | 29921/1896 | 0.00563 | 0 |

- **q07 đã sửa**: với query của agent, cross-encoder đưa p028:c01 vào top-3 → trả lời "zeroth-order optimization"
  [p028:c01] (bm25 b4000 trả lời sai "Boundary Attack").
- **q02**: context giờ có cả p017:c00 và gold p019:c01 → ctx:Y (cite cả hai).
- **q12**: p045:c03 hạng 1; câu trả lời không còn ý thêm sai về property inference.
- **q10, q15** tốn thêm search (2 và 3 lần) nhưng vẫn đúng.
- **Abstention u01/u02 không bị hỏng**: 2/2 vẫn abstain, lý do đúng.
- Đánh đổi: +16% token (27452 → 31817), +0.0007 USD/17 câu, median latency +1.4 s/câu (cross-encoder CPU;
  q01 18.7 s gồm lần nạp model đầu tiên).

### Chấm tay nháp (AI) — [review_dev_draft.json](review_dev_draft.json), cần người dùng xác nhận

| Config | Answer grade 0/1/2 | Tổng /30 | Citation hỗ trợ |
|---|---|---|---|
| bm25_k3_b4000 | 1 / 1 / 13 (q07 = 0, q12 = 1) | 27 | 16/17 |
| bm25_rerank_k3_b4000 | 0 / 0 / 15 | 30 | 19/19 |

Kết luận (chờ chấm tay xác nhận): cải thiện #2 giúp ở **agent** (query do model viết) dù không đổi metric
retrieval trên query gốc; theo selection_criteria, bm25_rerank_k3_b4000 đứng đầu.
