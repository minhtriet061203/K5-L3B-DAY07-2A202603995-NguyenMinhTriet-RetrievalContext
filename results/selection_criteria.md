# Tiêu chí chọn cấu hình (chốt trước khi chạy 6a/6b và trước test)

Ngày chốt: 2026-11-16 (ghi trước khi chạy bất kỳ cấu hình b4000 / cải thiện #2 nào; split test chưa được chạy).

## Phạm vi

- Chỉ chọn trên **dev** (15 câu có đáp án q01–q15, 2 câu thiếu evidence u01–u02).
- Split test chỉ chạy sau khi có `results/selected_config.json`; không chỉnh gì dựa trên kết quả test.

## Ràng buộc cứng (loại nếu vi phạm)

1. Abstention trên câu dev thiếu evidence = **2/2**.
2. Citation ids in context = **100%** (n/n).
3. **0** error (lỗi API / vector store).

## Xếp hạng (theo thứ tự ưu tiên)

1. Số câu dev có đáp án được **answered VÀ context cuối chứa gold evidence** (n/15) — cao hơn tốt hơn.
2. **Context Evidence Rate** (n/15) — cao hơn tốt hơn.
3. **Ít token hơn** (prompt + completion trên toàn dev), rồi **median latency thấp hơn**.

## Chấm tay trước khi chốt

- 2 cấu hình đứng đầu theo xếp hạng tự động được chấm tay trên dev
  (answer_grade 0/1/2, abstention_correct, citation_support theo từng citation).
- Nếu kết quả chấm tay (tổng answer_grade, rồi số citation hỗ trợ) đảo thứ tự hai cấu hình,
  chọn theo chấm tay và ghi rõ lý do trong `results/selected_config.json`.
