# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.

---

## Bài làm: 2A202603995 · Nguyễn Minh Triết

Báo cáo: [report/individual/2A202603995_NguyenMinhTriet.md](report/individual/2A202603995_NguyenMinhTriet.md).
Corpus NIST AI 100-2e2025 trang 14–73, 265 chunk (index B Day 6). Embedding `BAAI/bge-small-en-v1.5` (384 chiều),
PostgreSQL + pgvector (Docker Day 6). Agent: `gpt-4o-mini-2024-07-18`. Retrieval: `dense`, `bm25`, `hybrid_rrf`,
`bm25_rerank`. Cấu hình chọn trên dev: **`bm25_rerank_k3_b4000`** ([results/selected_config.json](results/selected_config.json)).

### Cài đặt (Windows PowerShell, Python 3.11)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # rồi điền LLM_API_KEY; KHÔNG commit .env
```

`.env` gồm `DATABASE_URL` (pgvector Day 6), `EMBEDDING_MODEL`, `DAY6_STRATEGY=B`, `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL`, `LLM_MIN_INTERVAL`, `LLM_PRICE_IN_PER_M`, `LLM_PRICE_OUT_PER_M` (giá dùng để tính chi phí).
Lần đầu chạy, sentence-transformers tải `BAAI/bge-small-en-v1.5` và `cross-encoder/ms-marco-MiniLM-L-6-v2` từ Hugging Face.

### Bật vector store Day 6

```powershell
cd <repo Day 6>\starter
docker compose -p day6_student_starter up -d --wait
cd <repo Day 7>
```

### Tái lập từng bước

```powershell
# 1. Import chunk/câu hỏi Day 6 (đã có sẵn trong data/day6/, chỉ cần khi tái tạo)
python scripts/import_day6.py --day6 <repo Day 6>\starter
# 2. Benchmark 24 câu -> data/benchmark.json, data/cases.json, data/benchmark_report.json
python scripts/build_benchmark.py
# 3. Kiểm tra vector store khớp corpus và tái lập Day 6 -> results/step1/
python scripts/check_day6_store.py
# 4. Retrieval (query gốc, top-3, filter của câu hỏi)
python scripts/eval_retrieval.py --split dev                                       # dense, bm25, hybrid_rrf
python scripts/eval_retrieval.py --split dev --methods bm25,bm25_rerank --tag rerank
# 5. Agent trên dev (mỗi run 17 câu ~0.005-0.006 USD)
foreach ($c in "dense_k3_b800","bm25_k3_b800","hybrid_k3_b800","dense_k3_b4000","bm25_k3_b4000","hybrid_k3_b4000","bm25_rerank_k3_b4000") {
  python scripts/run_agent.py --config $c --split dev }
# 6. Bảng so sánh và từng câu
python scripts/compare_runs.py --split dev
python scripts/per_question.py --split dev --configs dense_k3_b4000,bm25_k3_b4000,hybrid_k3_b4000 --out per_question_dev_b4000.md
# 7. Test (chỉ chạy được khi đã có results/selected_config.json)
python scripts/run_agent.py --config dense_k3_b800 --split test
python scripts/run_agent.py --config bm25_rerank_k3_b4000 --split test
python scripts/eval_retrieval.py --split test --methods dense,bm25,hybrid_rrf,bm25_rerank
python scripts/compare_runs.py --split test
python scripts/per_question.py --split test --configs dense_k3_b800,bm25_rerank_k3_b4000
# 8. Tổng hợp nhãn chấm tay (reviews.json) bằng script starter
python starter/agent_metrics.py --cases data/cases.json --traces results/agent/bm25_rerank_k3_b4000_test/traces_metrics.json `
  --reviews results/agent/bm25_rerank_k3_b4000_test/reviews.json --split test `
  --output results/agent/bm25_rerank_k3_b4000_test/agent_metrics_summary.json
# Unit test (không cần DB/API)
python -m unittest discover -s tests
```

Chạy lại agent cho kết quả có thể khác (LLM không tất định); `run_agent.py` ghi đè thư mục cùng tên, nên đổi tên thư mục
cũ (vd. hậu tố `_v1`) trước khi chạy lại. Kết quả chính: [results/compare_dev.md](results/compare_dev.md),
[results/compare_test.md](results/compare_test.md), [results/analysis_6a.md](results/analysis_6a.md),
[results/analysis_6b.md](results/analysis_6b.md), [results/selection_criteria.md](results/selection_criteria.md).
