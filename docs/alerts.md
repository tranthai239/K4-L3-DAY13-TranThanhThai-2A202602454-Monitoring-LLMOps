# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-2A202602454`

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 từ `response_sent.latency_ms`, SLO yêu cầu P95 ≤ 3000ms
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn bình thường trước khi nhận câu trả lời, trải nghiệm xấu đi rõ rệt
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Latency** → xác nhận P95/P99 và khoảng thời gian tăng bất thường.
  2. Lọc `data/logs.jsonl` trong khoảng thời gian đó, tìm các dòng `response_sent` có `latency_ms > 3000`, lấy một `correlation_id`.
  3. Mở trace cùng `correlation_id` trên Langfuse → so sánh span `retrieval` và `generation` để xác định bước nào gây chậm.
- Mitigation tạm thời: Nếu span `retrieval` chậm → kiểm tra vector store/RAG. Nếu span `generation` chậm → rollback prompt về version cũ hoặc giảm concurrency. Nếu do incident scenario → tắt scenario bằng `/incidents/{name}/disable`.
- Owner: `student-2A202602454`

## Alert 2

- Tên: `high_error_rate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: error rate từ tỷ lệ `request_failed / request_received`, SLO yêu cầu error rate ≤ 2%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` kéo dài liên tục trong 3 phút
- Ảnh hưởng tới người dùng: Người dùng nhận lỗi 500 thay vì câu trả lời, không thể sử dụng dịch vụ
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors** → xác nhận error rate và phân bố `error_type`.
  2. Lọc `data/logs.jsonl` tìm các dòng `request_failed`, kiểm tra `error_type` và `tool_success`, lấy một `correlation_id`.
  3. Mở trace cùng `correlation_id` trên Langfuse → xác định span nào bị lỗi (retrieval timeout, generation error, v.v.).
- Mitigation tạm thời: Nếu lỗi do retrieval (`RuntimeError: Vector store timeout`) → tắt incident bằng `/incidents/tool_fail/disable`. Nếu lỗi do prompt → rollback `production` label về version cũ trên Langfuse. Kiểm tra `/health` để xác nhận hệ thống phục hồi.
- Owner: `student-2A202602454`

## Alert 3

- Tên: `low_retrieval_success`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success rate từ `tool_success`, SLO yêu cầu ≥ 90%
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90%` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Câu trả lời không dựa trên tài liệu phù hợp, chất lượng giảm đáng kể dù không báo lỗi trực tiếp
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors** → kiểm tra `tool_success_rate_pct` và panel **Quality** → xem `quality_score` có giảm theo không.
  2. Lọc `data/logs.jsonl` tìm các dòng `response_sent` có `tool_success: false`, lấy `correlation_id`.
  3. Mở trace cùng `correlation_id` trên Langfuse → kiểm tra span `retrieval` để xem lỗi cụ thể (timeout, empty result, exception).
- Mitigation tạm thời: Kiểm tra vector store connectivity. Nếu do incident scenario → tắt bằng `/incidents/tool_fail/disable` hoặc `/incidents/rag_slow/disable`. Xem xét tăng timeout cho retrieval nếu lỗi là do latency.
- Owner: `student-2A202602454`
