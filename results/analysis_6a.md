# 6a — Cải thiện #1: context budget 800 → 4000 ký tự (dev)

Ngày chạy: 2026-11-16. Model `gpt-4o-mini-2024-07-18`. Chỉ đổi `budget`; giữ top_k=3, max_searches=3,
filter_mode=given, cùng prompt (v1), cùng corpus/index (Day 6 B, 265 chunk), cùng 17 câu dev.
Tiêu chí chọn đã chốt trước trong [selection_criteria.md](selection_criteria.md).

## Giả thuyết (ghi trước khi chạy)

Budget 800 ký tự chỉ chứa ~1 chunk B (TB 632, max 1060 ký tự), nên kết quả search lần 2–3 (và đôi khi
cả lần 1) bị cắt → context thiếu evidence → abstain nhầm. Budget 4000 (~6 chunk) sẽ đưa
Context Evidence Rate gần Hit@3 retrieval và giảm false refusal; đổi lại tốn thêm prompt token.

## Kết quả trước/sau theo phương pháp (dev, 15 câu có đáp án + 2 thiếu evidence)

| Phương pháp | Budget | Context Evidence | Answered (có đáp án) | Answered ∧ ctx có gold | False refusal | Abstention u01/u02 | Citation ids in context | Phân bố số search | Median s | Tokens in/out | USD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dense | 800 | 4/15 | 5/15 | 4/15 | 10/15 | 2/2 | 5/5 | {1:7, 3:10} | 4.11 | 29301/1585 | 0.00535 |
| dense | 4000 | **12/15** | **12/15** | **11/15** | 3/15 | 2/2 | 15/15 | {1:13, 2:1, 3:3} | 2.89 | 33681/1730 | 0.00609 |
| bm25 | 800 | 4/15 | 3/15 | 3/15 | 12/15 | 2/2 | 3/3 | {1:3, 2:1, 3:13} | 4.15 | 34016/1611 | 0.00607 |
| bm25 | 4000 | **13/15** | **15/15** | **13/15** | 0/15 | 2/2 | 17/17 | {1:16, 3:1} | 2.79 | 25675/1777 | 0.00492 |
| hybrid_rrf | 800 | 5/15 | 6/15 | 4/15 | 9/15 | 2/2 | 6/6 | {1:7, 2:1, 3:9} | 4.11 | 29440/1647 | 0.00540 |
| hybrid_rrf | 4000 | **12/15** | **14/15** | **12/15** | 1/15 | 2/2 | 16/16 | {1:15, 3:2} | 2.75 | 29362/1780 | 0.00547 |

Cả 3 cấu hình b4000 thỏa ràng buộc cứng (abstention 2/2, citation in context 100%, 0 error).
Giả thuyết đúng: Context Evidence tăng 4–5/15 → 12–13/15, false refusal giảm 9–12/15 → 0–3/15.
Token **không** tăng nhiều (bm25 còn giảm 34016 → 25675) vì với budget lớn model trả lời ngay sau
1 search thay vì search lại 3 lần; latency median giảm ~4.1 s → ~2.8 s.
Tổng chi phí 6a: 0.01648 USD.

Nguồn: [compare_dev.md](compare_dev.md), [per_question_dev_b4000.md](per_question_dev_b4000.md),
traces trong `results/agent/<config>_dev/traces.json`.

## Lỗi dev đã ghi ở bước 5

- **q12 (gold p45)** — lỗi #1 (budget). Với b800, p045:c03 bị cắt/không vào context.
  - bm25_k3_b4000: **đã sửa** — search 1 trả p046:c02, p045:c03, p035:c03, cả 3 vào context, model trả lời
    "DP does not provide guarantees against model extraction … designed to protect the training data, not the model"
    [p045:c03][p046:c02]. Lưu ý: câu trả lời thêm ý "property inference … directly related to model extraction"
    không có trong passage (cần chấm tay, có thể chỉ được 1/2).
  - dense_k3_b4000 / hybrid_k3_b4000: **chưa sửa**, nhưng nguyên nhân giờ là **retrieval xếp hạng**, không còn là
    budget: các truy vấn "differential privacy model extraction …" chỉ trả p020, p041, p046, p035; p045:c03
    không lọt top-3 lần nào (không có passage nào bị `dropped_budget`).
- **q02 (gold p19)** — lỗi #1 (bm25 b800 context rỗng vì chunk top-1 > 800). Với b4000 cả 3 phương pháp đều
  answered "availability breakdown, integrity violation, and privacy compromise" và cite **p017:c00**.
  per_question ghi ctx:N vì gold chỉ khai báo p19, nhưng p017:c00 có nguyên văn "The attacker's objectives are
  shown as disjointed circles …: availability breakdown, integrity violation, and privacy compromise."
  → đây là **evidence thay thế hợp lệ chưa được ghi trong benchmark**, không phải lỗi của agent. Chưa sửa nhãn
  benchmark (cần người dùng quyết định; nếu thêm thì áp dụng cho mọi run và ghi rõ).
- **q05 (gold p25)** — lỗi #2 (có evidence nhưng abstain). Với b4000 cả 3 phương pháp đều answered
  "FGSM performs a single iteration of gradient descent" [p025:c04]. Ở b800 bm25/hybrid search 1–2 lần, context
  chỉ có p25 và model nhầm sang iterative FGSM; với b4000 context có thêm p026:c01 và p025:c03/p028, model đọc đúng.
  **Đã hết lỗi** trong run này (1 lần chạy, chưa kiểm tra độ ổn định qua nhiều seed).

## Các câu còn sai / cần chấm tay sau 6a

| Câu | Config | Hiện tượng | Nguyên nhân (đọc trace) |
|---|---|---|---|
| q07 | bm25_k3_b4000 | answered **sai**: "Boundary Attack … random walks" (đó là decision-based, không phải zeroth-order) [p028:c02] | Agent viết query "score-based black-box evasion attacks gradient estimation method"; BM25 xếp gold p028:c01 ở hạng **5**, top-3 là p028:c02, p028:c00, p033:c01 → **retrieval xếp hạng**. Model chọn đáp án gần nhất trong context thay vì abstain. |
| q12 | dense, hybrid b4000 | abstain | Gold p045:c03 không vào top-3 qua 2–3 query → **retrieval xếp hạng** (BM25 với cùng query xếp p045:c03 hạng 2). |
| q15 | dense_k3_b4000 | abstain | 3 search (filter generative_ai) chỉ ra p047/p049/p050/p059; p056:c00 không vào top-3 → **retrieval xếp hạng** (BM25 xếp p056:c00 hạng 1 cho query tương tự). |
| q01 | dense_k3_b4000 | abstain dù context có gold p014:c01 | **Model**: cho rằng passage "không có định nghĩa ngắn gọn". Search 3 bị cắt p025:c03 do budget (3662/4000). |
| q03 | hybrid_k3_b4000 | answered "backdoor attack" [p021:c02], ctx:N | Gold khai báo p20; p021:c02 nói về backdoor cần control cả train và test → có thể là evidence thay thế; cần chấm tay. |
| q02 | cả 3 | answered [p017:c00], ctx:N | Evidence thay thế hợp lệ (xem trên). |
| q04 (dense), q10 (hybrid) | b800 | answered khi ctx không có gold | Đã ghi từ bước 5; ở b4000 cả hai có gold trong context. |

## Kết luận 6a và lựa chọn cho 6b

- Xếp hạng theo selection_criteria: **bm25_k3_b4000** (answered∧ctx 13/15, ctx 13/15, 27452 token) >
  hybrid_k3_b4000 (12/15, 12/15, 31142) > dense_k3_b4000 (11/15, 12/15, 35411).
- Lỗi còn lại chủ yếu là **retrieval xếp sai thứ hạng** (q07/bm25, q12 dense+hybrid, q15 dense: gold nằm ngoài
  top-3 dù có trong top-20); kiểu "evidence trong context nhưng abstain" chỉ còn 1 trường hợp (q01/dense)
  → 6b chọn **rerank cross-encoder** trên phương pháp tốt nhất (bm25), xem [analysis_6b.md](analysis_6b.md).
