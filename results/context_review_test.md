# Chấm context test (0/1/2) — AI soạn nháp, người dùng đã xác nhận 2026-11-16

Thang (BENCHMARK.md mục 2): 0 = không có evidence; 1 = có nhưng thiếu điều kiện hoặc nguồn; 2 = đủ evidence và nguồn.

| Query | Gold | dense_k3_b800 | Lý do | bm25_rerank_k3_b4000 | Lý do |
|---|---|---|---|---|---|
| q16 | p57 | 0 | ctx chỉ p063:c01; p056/p057 bị cắt do budget 800 | 0 | ctx p056:c03, p063:c01, p058:c02 — không có câu "refusal suppression" p57 |
| q17 | p63 | 0 | ctx chỉ p066:c04; p065/p064 bị cắt | 2 | p063:c04 có nguyên văn "enabled by RESOURCE CONTROL …", đủ nguồn |
| q18 | p72 | 0 | ctx chỉ p028:c03; p072:c02 bị cắt cả 3 lượt | 2 | p072:c01 (8-bit/4-bit) + p072:c02 (inherit vulnerabilities …) |
| q19 | p59 | 0 | ctx p059:c01 không có "rates exceeding 8%"; p059:c02 bị cắt | 2 | p059:c02 có "rates exceeding 8% for certain models" |
| q20 | p39 | 0 | ctx p039:c03; p039:c00 bị cắt cả 3 lượt | 2 | p039:c00 "Compromised clients can send malicious updates …" |

| Mức | dense_k3_b800 | bm25_rerank_k3_b4000 |
|---|---|---|
| 0 | 5/5 | 1/5 (q16) |
| 1 | 0/5 | 0/5 |
| 2 | 0/5 | 4/5 (q17–q20) |

Trace: `results/agent/<config>_test/traces.json`; lý do chi tiết từng câu trong `reviews_draft.json`.
