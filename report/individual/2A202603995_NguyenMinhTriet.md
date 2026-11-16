# Báo cáo Day 7 — Agentic RAG

**2A202603995 · Nguyễn Minh Triết** · ngày chạy: 2026-11-16 · mọi số liệu lấy từ `results/` (đường dẫn ghi ở từng mục).

## Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:** NIST AI 100-2e2025 *Adversarial Machine Learning: A Taxonomy and
  Terminology of Attacks and Mitigations* (03/2025), https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2025.pdf,
  DOI 10.6028/NIST.AI.100-2e2025. Tài liệu do NIST (Chính phủ Mỹ) soạn, không chịu bản quyền tại Mỹ (17 U.S.C. 105);
  repo không phân phối lại PDF. Index trang **14–73 (60 trang)**, **265 chunk** (index B của Day 6, chunk theo section,
  TB 632 ký tự, max 1060), import nguyên văn bằng `scripts/import_day6.py` → `data/day6/chunks.json`
  (sha256 đầu vào trong `data/day6/import_report.json`).
- **Vector store, embedding model, phiên bản và số chiều:** PostgreSQL + pgvector 0.8.7 (Docker Day 6), cột `vector(384)`,
  265 dòng; embedding `BAAI/bge-small-en-v1.5` (sentence-transformers 6.3.0, CPU, normalize, prefix query BGE).
  `scripts/check_day6_store.py` xác nhận DB khớp 265/265 chunk và tái lập Day 6 (dense dev Hit@1 11/15, Hit@3 12/15)
  — `results/step1/check.json`.
- **Agent model, cách chạy và phân chia dev/test:** OpenAI `gpt-4o-mini-2024-07-18` (tool calling, nhiệt độ mặc định),
  giá 0.15/0.60 USD per 1M token in/out. Benchmark `data/benchmark.json` 24 câu: **dev 15 có đáp án + 2 thiếu evidence**
  (q01–q15, u01–u02), **test 5 + 2** (q16–q20, u03–u04); trang gold dev và test không trùng
  (`data/benchmark_report.json`). Loại câu dev: direct 6, paraphrase 3, condition 3, filter 3; 5 câu có `filter`
  taxonomy do người dùng cung cấp (q13–q15, q19, q20).
- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:** câu có đáp án có `gold` = {source_id, page, evidence};
  `build_benchmark.py` kiểm tra evidence nằm nguyên văn trong chunk đúng trang. Hit = chunk đúng nguồn + trang và chứa
  nguyên chuỗi evidence (`starter/baseline.hit`). Câu thiếu evidence gần chủ đề (vd. u02 hỏi thiệt hại tiền của vụ
  Tay.AI có ở p40), kèm `terms_absent` được quét trên cả 265 chunk (không phụ thuộc top-k). Chấm câu trả lời 0/1/2,
  citation đúng/sai từng id, abstention theo BENCHMARK.md mục 3.

## Retrieval và thử nghiệm

Điều kiện chung: cùng corpus/index B, cùng câu hỏi gốc (không viết lại), filter = trường `filter` của câu hỏi.
Hit@1/Hit@3 = retrieval một lượt trên **query gốc** (`results/step3_dev`, `step3_dev_rerank`, `step3_test`);
Context Evidence Rate = context cuối của **agent** chứa evidence gold (n/N câu có đáp án). Agent: top_k=3,
max 3 search, prompt v1. Thời gian = median giây/câu của agent; chi phí = USD cả split (dev 17 câu, test 7 câu).
**Query viết lại:** trong agent, query của tool `search` do LLM tự viết (có thể khác câu hỏi gốc, tối đa 3 lượt);
mỗi lượt được ghi trong trace (`events[].query`, kết quả rank/score, `shown`, `dropped_budget`). Vì vậy Hit@1/Hit@3
báo trên query gốc, còn Context Evidence Rate là kết quả của cả pipeline agent.

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| Baseline `dense_k3_b800` | dense pgvector, k=3, filter given, không rerank, 800 ký tự | Day 6 dense + budget mặc định starter | dev | 11/15 (73%) | 12/15 (80%) | 4/15 (27%) | 4.11 s / 0.00535 USD |
| Phương pháp 2 `bm25_k3_b800` | BM25 (k1=1.5, b=0.75), k=3, 800 | Từ khóa kỹ thuật (FGSM, RONI…) hợp lexical | dev | 13/15 (87%) | 15/15 (100%) | 4/15 (27%) | 4.15 s / 0.00607 USD |
| Phương pháp 3 `hybrid_k3_b800` | RRF(dense, BM25), 20 candidate mỗi bên, k=60, k=3, 800 | Kết hợp ngữ nghĩa + từ khóa | dev | 11/15 (73%) | 13/15 (87%) | 5/15 (33%) | 4.11 s / 0.00540 USD |
| Cải thiện 1 `bm25_k3_b4000` (cũng chạy dense/hybrid b4000) | BM25, k=3, **4000** | 800 ký tự chỉ chứa ~1 chunk → kết quả search bị cắt | dev | 13/15 | 15/15 | **13/15 (87%)** (dense 12/15, hybrid 12/15) | 2.79 s / 0.00492 USD |
| Cải thiện 2 `bm25_rerank_k3_b4000` | BM25 top-20 → cross-encoder `ms-marco-MiniLM-L-6-v2` → top-3, 4000 | Lỗi còn lại là xếp hạng (gold ở top-20 nhưng ngoài top-3) | dev | 13/15 (87%) | 15/15 (100%) | **15/15 (100%)** | 4.20 s / 0.00563 USD |
| Cấu hình đã chọn `bm25_rerank_k3_b4000` | như trên | chốt trong `results/selected_config.json` trước test | test | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4.32 s / 0.00294 USD |
| Baseline `dense_k3_b800` | như baseline dev | — | test | 2/5 (40%) | 5/5 (100%) | 0/5 (0%) | 4.37 s / 0.00253 USD |

Bảng đầy đủ: [compare_dev.md](../../results/compare_dev.md), [compare_test.md](../../results/compare_test.md).
Retrieval hybrid/dense trên test: dense 2/5, 5/5; bm25 2/5, 3/5; hybrid 2/5, 4/5 (MRR@10 0.667 / 0.500 / 0.620;
bm25_rerank 0.700). Retrieval chạy cục bộ (0 USD): dense ~75–100 ms/query, BM25 ~1 ms, rerank ~1.0 s/query trên CPU.

**Hai lỗi dev, nguyên nhân, cách thử** (chi tiết: [analysis_6a.md](../../results/analysis_6a.md),
[analysis_6b.md](../../results/analysis_6b.md)):

1. **q12 — budget cắt evidence** ("DP có chống model extraction không?", gold p45). Ở b800 cả 3 phương pháp abstain:
   trace cho thấy p045:c03 bị `dropped_budget` hoặc search lần 2–3 không thêm được chunk (budget 800 ≈ 1 chunk; q02/bm25
   còn có context rỗng vì chunk top-1 > 800 ký tự). **Thử:** budget 4000, giữ nguyên mọi thứ khác.
   **Kết quả:** bm25 b4000 trả lời đúng ý chính [p045:c03] (chấm 1/2 vì thêm ý sai "property inference … directly
   related to model extraction"); dense/hybrid b4000 vẫn abstain nhưng giờ do **xếp hạng** (p045:c03 không vào top-3).
   Sau cải thiện 2 (rerank): p045:c03 hạng 1, trả lời 2/2. Toàn dev: Context Evidence 4–5/15 → 12–13/15, false refusal
   9–12/15 → 0–3/15.
2. **q05 — có evidence nhưng vẫn abstain** (FGSM mấy vòng lặp, gold p25). bm25/hybrid b800 có p025:c04 trong context
   nhưng model nhầm sang *iterative* FGSM rồi abstain. Giả thuyết ban đầu là cần sửa prompt; nhưng ở b4000 (context có
   thêm p026:c01, p025:c03) cả 3 phương pháp đều trả lời đúng "single iteration" [p025:c04], nên không sửa prompt
   (chỉ 1 lần chạy, chưa đo độ ổn định). Lỗi còn lại sau 6a chủ yếu là xếp hạng: **q07/bm25 b4000** trả lời sai
   "Boundary Attack" vì gold p028:c01 đứng hạng 5 với query do agent viết → cải thiện 2 (rerank) sửa được (2/2).

**Lý do chọn cấu hình** (tiêu chí chốt trước: [selection_criteria.md](../../results/selection_criteria.md)):
ràng buộc cứng abstention dev 2/2, citation ids in context 100%, 0 error — cả 7 cấu hình dev đều đạt.
Xếp hạng theo (1) answered ∧ context có gold: **bm25_rerank_k3_b4000 15/15** > bm25_k3_b4000 13/15 >
hybrid_k3_b4000 12/15 > dense_k3_b4000 11/15 > các b800 3–4/15. Chấm tay 2 cấu hình đầu cùng thứ tự (30/30 vs 27/30).
Đánh đổi: so với bm25_k3_b4000, rerank tốn +16% token (27452 → 31817), +0.0007 USD/17 câu và +1.4 s median latency.
Lưu ý: trên query gốc rerank **không** tăng Hit@1/MRR dev (13/15, 0.922 cả hai: lên hạng q03, q15, xuống hạng q02, q10);
lợi ích thấy ở query do agent viết.

## Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:** 3 tool — `search(query)` (retriever theo
  config, filter lấy từ câu hỏi, không bao giờ từ gold), `answer(answer, citations)`, `abstain(reason)`.
  Dừng khi model gọi answer/abstain, hoặc đạt `max_searches`=3 (search thêm bị từ chối, model phải kết luận), hoặc
  quá 6 lượt LLM (→ abstain `no_final_decision`). Context: dedup theo chunk id, tổng ký tự ≤ budget trên cả lượt chạy,
  chunk không vừa bị bỏ và ghi `dropped_budget`. Citation phải là id đã có trong context, nếu không → abstain
  `invalid_citation` (giữ `raw_answer`). Nội dung passage được coi là dữ liệu, không phải chỉ dẫn (prompt rule 2).
  Lỗi API/DB ghi `status: error`, không thay bằng kết quả giả (0 error trong mọi run).

Nhãn chấm tay: AI soạn nháp, tôi đọc trace/citation và xác nhận. Tổng hợp bằng `starter/agent_metrics.py`
(`results/agent/<config>_<split>/agent_metrics_summary.json`).

| Cấu hình / split | Tool use | Số lượt gọi (search) | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| bm25_k3_b4000 / dev | 17/17 | {1:16, 3:1} | 1/1/13, 1.80 | 16/17 | 15/15 | 2/2 | 0/15 |
| bm25_rerank_k3_b4000 / dev | 17/17 | {1:14, 2:1, 3:2} | 0/0/15, 2.00 | 19/19 | 15/15 | 2/2 | 0/15 |
| **dense_k3_b800 / test (baseline)** | 6/7 | {0:1, 3:6} | 5/0/0, 0.00 | 0/0 (không áp dụng) | 0/0 | 2/2 | 5/5 |
| **bm25_rerank_k3_b4000 / test (chọn)** | 7/7 | {1:5, 3:2} | 2/0/3, 1.20 | 4/5 | 4/4 | 2/2 | 1/5 |

Chấm context test 0/1/2 ([context_review_test.md](../../results/context_review_test.md)): baseline 5×0
(evidence của cả 5 câu được retrieval trả về nhưng bị cắt do budget 800); cấu hình chọn 0 = 1 (q16), 2 = 4 (q17–q20).

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| q17 (test, chọn) | có bằng chứng | 1 search "indirect prompt injection attacks attacker capability" → p064:c02, **p063:c04**, p065:c00 | "Indirect prompt injection attacks are enabled by **resource control** … without direct interaction with the application" [p063:c04] | grade 2, citation đúng: p063:c04 "INDIRECT PROMPT INJECTION attacks are enabled by RESOURCE CONTROL …" |
| u04 (test, chọn) | thiếu bằng chứng | 3 search ("EU AI Act data poisoning high-risk…", "EU AI Act article…", "EU AI Act protect against data poisoning") → p017, p014, p054, p073, p036; lần 4 bị `search_limit` | abstain: "passages do not provide … which article of the EU AI Act …" | abstention đúng; tài liệu không nhắc EU AI Act (đã quét 265 chunk), agent không bịa số điều |
| q18 (test, chọn) | lỗi | 3 search; context có **p072:c02** (gold: "quantized models inherit the vulnerabilities … introduce additional weaknesses") và p072:c01 (8-bit/4-bit) | abstain, dù `reason` của model nêu đúng đáp án ("inherit vulnerabilities … more vulnerable rather than safer") | grade 0 (từ chối nhầm), context 2: lỗi ở model/prompt với câu hỏi yes/no, không phải retrieval |
| q16 (test, chọn) | lỗi | 1 search → p056:c03, p063:c01, p058:c02 (không có p57) | "direct prompting attack … jailbreak" [p056:c03] | grade 0, citation sai: đáp án "refusal suppression" (p57) không vào context; model trả lời thay vì abstain |

- **Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:** trace đầy đủ (tool call, tham số, kết quả có rank/score,
  `shown`/`duplicate`/`dropped_budget`, context cuối, câu trả lời, citation, usage, latency):
  `results/agent/<config>_<split>/traces.json`; bản rút gọn cho agent_metrics `traces_metrics.json`; nhãn
  `reviews.json` (test) và `results/review_dev.json` (dev); xem từng câu `results/per_question_*.md`. Lệnh ở
  [README](../../README.md). Tổng chi phí LLM của toàn bộ lab (11 run kể cả smoke): **0.0465 USD**
  (dev mỗi run 17 câu 0.0049–0.0061 USD; test 0.0025–0.0029 USD); retrieval/embedding/rerank chạy cục bộ.
- **Kết quả trước/sau, đánh đổi và giới hạn:**
  - Trên test, cấu hình chọn vượt baseline rõ: answered đúng 3/5 so với 0/5, Context Evidence 4/5 so với 0/5,
    token +15% (15000 → 17279), latency median tương đương (4.32 s vs 4.37 s). Nhưng test (1.20/2) thấp hơn dev
    (2.00/2): dev đã dùng để chọn nên lạc quan; test chỉ 5 câu có đáp án nên mỗi câu = 20%.
  - q18 cho thấy lỗi "có evidence vẫn abstain" (kiểu q05) chưa hết; sửa prompt (v2) là bước tiếp theo nhưng **không**
    làm sau khi xem test để giữ test độc lập — cần test mới nếu thử.
  - Baseline u03 abstain với 0 search (vi phạm rule "always search"): abstention đúng nhưng không có căn cứ retrieval.
  - Mỗi cấu hình chỉ chạy 1 lần, nhiệt độ mặc định → kết quả có thể dao động; chưa đo phương sai.
  - Gold chỉ ghi 1 trang/câu; q02 có evidence thay thế ở p17 nên Context Evidence của một số run dev bị tính thấp
    (q02 ctx:N ở các run b4000 không rerank). Benchmark không sửa để giữ so sánh nhất quán.
  - Cross-encoder MS MARCO không chuyên AML và chậm trên CPU (~1 s/search, lần đầu ~15 s nạp model).
  - Benchmark nhỏ (24 câu), chỉ 1 tài liệu, chỉ text (bảng/hình trong PDF không được xử lý riêng).

### AI hỗ trợ và phần tôi tự kiểm tra

- **AI (Claude Code) hỗ trợ:** viết/sửa code (`src/`, `scripts/`, `tests/`), chạy thí nghiệm, đọc trace để phân tích lỗi,
  soạn nháp `analysis_6a.md`, `analysis_6b.md`, nháp nhãn chấm tay (dev và test) và nháp báo cáo/README.
- **Tôi tự kiểm tra:** chốt `selection_criteria.md` trước khi chạy cải thiện và test; đọc và xác nhận nhãn nháp dev
  (34 câu-config) và test (14 câu-config, 5 có đáp án + 2 thiếu evidence mỗi config) đối chiếu với citation; xác nhận
  cấu hình chọn trước khi chạy test; kiểm tra số liệu báo cáo khớp file `results/`; không chỉnh gì sau khi xem test.

## Thử thách nâng cao (nếu thực hiện)

Không thực hiện.
