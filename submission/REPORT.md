# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Báo cáo dùng 3 output text và bộ evidence runtime 01–14 theo yêu cầu CP4. Mọi đường dẫn đều tương đối từ thư mục `submission/`.

## 1. Thông tin học viên

- **Họ và tên:** TRẦN THANH THÁI
- **MSSV:** 2A202602454
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/tranthai239/K4-L3-DAY13-TranThanhThai-2A202602454-Monitoring-LLMOps
- **Commit SHA cuối:** Chưa điền — cập nhật sau commit cuối và push remote
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602454`

## 2. Evidence index

### 2.1. Ba output text

| Evidence | Đường dẫn |
|---|---|
| Pytest output | [evidence/pytest.txt](evidence/pytest.txt) |
| Log validator output | [evidence/log-validator.txt](evidence/log-validator.txt) |
| Dashboard validator output | [evidence/dashboard-validator.txt](evidence/dashboard-validator.txt) |

### 2.2. Evidence runtime 01–14

| Evidence | Đường dẫn | Nội dung chứng minh |
|---|---|---|
| 01 - Pytest | [evidence/01-pytest.png](evidence/01-pytest.png) | Lệnh test và số test pass |
| 02 - Log validator | [evidence/02-log-validator.png](evidence/02-log-validator.png) | Grading Scorecard và điểm validator |
| 03 - Dashboard validator | [evidence/03-dashboard-validator.png](evidence/03-dashboard-validator.png) | Dashboard contract đạt 6/6 panel |
| 04 - Structured log | [evidence/04-structured-log.png](evidence/04-structured-log.png) | Hai event structured log cùng `correlation_id` |
| 05 - PII redaction | [evidence/05-pii-redaction.png](evidence/05-pii-redaction.png) | PII test được thay bằng marker redaction |
| 06 - Trace list | [evidence/06-trace-list.png](evidence/06-trace-list.png) | Project Langfuse cá nhân có ít nhất 10 traces |
| 07 - Trace waterfall | [evidence/07-trace-waterfall.png](evidence/07-trace-waterfall.png) | Root `lab-agent-run` có child retrieval và generation |
| 08 - Trace metadata | [evidence/08-trace-metadata.png](evidence/08-trace-metadata.png) | Correlation ID, prompt metadata, token và cost |
| 09 - Prompt versions | [evidence/09-prompt-versions.png](evidence/09-prompt-versions.png) | Prompt v1/v2 và labels |
| 10a/10b - Prompt promote và rollback | [evidence/10a-prompt-promote.png](evidence/10a-prompt-promote.png), [evidence/10b-prompt-rollback.png](evidence/10b-prompt-rollback.png) | `production` được promote sang v2 rồi rollback về v1 |
| 11a–11e - Dashboard overview | [evidence/11a-dashboard-traces-cost.png](evidence/11a-dashboard-traces-cost.png), [11b](evidence/11b-dashboard-traces-cost.png), [11c](evidence/11c-dashboard-traces-cost.png), [11d](evidence/11d-dashboard-traces-cost.png), [11e](evidence/11e-dashboard-traces-cost.png) | Dashboard runtime: traffic, cost, tokens và latency |
| 12 - Incident metric | [evidence/12-incident-metric.png](evidence/12-incident-metric.png) | Latency P95 tăng bất thường |
| 13 - Incident log | [evidence/13-incident-log.png](evidence/13-incident-log.png) | Request chậm và `correlation_id=req-8343780c` |
| 14 - Incident trace | [evidence/14-incident-trace.png](evidence/14-incident-trace.png) | Cùng correlation ID và retrieval span 2.50s |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline / yêu cầu | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 100/100 | 100/100 | 83 records, 0 thiếu field, 0 thiếu enrichment, 38 correlation IDs, 0 PII leak |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Dashboard contract hợp lệ |
| `pytest` | 24 passed | 26 passed trong 1.98s | Có regression test cho PII trong generation trace |
| Số traces hợp lệ | Tối thiểu 10 | Tối thiểu 32 traces hiển thị trong Langfuse | Traces thuộc project cá nhân |
| Số PII leak | 0 | 0 | Validator không phát hiện PII thô |
| Latency P95 / TTFT | Baseline P95 khoảng 489ms, TTFT khoảng 50ms | Incident P95 khoảng 3.5s, request đại diện 3696ms và TTFT 50ms | P95 vượt challenge threshold 2000ms |
| Retrieval success rate | 100% | 100% trong request đại diện | Sự cố làm chậm retrieval, không làm retrieval thất bại |

Kết quả lệnh được lưu tại [pytest.txt](evidence/pytest.txt), [log-validator.txt](evidence/log-validator.txt) và [dashboard-validator.txt](evidence/dashboard-validator.txt).

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận header `x-request-id` hoặc tự sinh ID dạng `req-<8-hex>`. ID được bind vào structlog contextvars, truyền vào agent/trace và trả về qua response header.
- **Metadata trong structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Bảo vệ PII:** Dữ liệu được scrub trước khi serialization/export. Email, SĐT Việt Nam, CCCD và thẻ tín dụng được thay bằng marker `[REDACTED_*]`; `user_id` chỉ được ghi dưới dạng hash. Input/output gửi sang generation trace cũng dùng preview đã scrub.
- **Kiểm chứng:** Log validator đạt 100/100, không phát hiện PII leak; toàn bộ 25 tests pass.

## 5. Tracing và prompt versioning

- **Nguồn traces:** Project Langfuse cá nhân `day13-k4-l3b-2A202602454`, không dùng project chung.
- **Cấu trúc observation:** Root `lab-agent-run` kiểu agent → child `retrieval` kiểu span → child `generation` kiểu generation.
- **Nối trace với log:** Log và trace metadata cùng chứa `correlation_id`.
- **Prompt name:** `day13-chat`.
- **Baseline:** version 1, labels `baseline` và `production` sau rollback.
- **Candidate:** version 2, label `candidate` (`latest` do Langfuse tự gắn).
- **Trace baseline v1:** `114c494a9a2d40385aaf5eaadaf6c0e8`.
- **Trace candidate v2:** `680844ae87109fb59e348f62fcb30cf8`.
- **Promote và rollback:** Chuyển `production` từ v1 sang v2, chạy request xác nhận trace dùng `prompt_label=production` và `prompt_version=2`, sau đó chuyển `production` về v1. Trạng thái cuối: v1 có `baseline` + `production`; v2 có `candidate`.

## 6. Dashboard, SLO và alerts

- **Dashboard contract:** Latency (P50/P95/P99 và TTFT P95), Traffic (request count), Errors (error rate và retrieval success), Cost (USD/phút), Tokens (input/output), Quality (mean score). Cấu hình tại [config/dashboard.yaml](../config/dashboard.yaml).
- **SLO:** 99.5% request thành công với latency ≤ 3000ms trong cửa sổ 28 ngày. Cấu hình tại [config/slo.yaml](../config/slo.yaml).
- **Error budget:** `100% - 99.5% = 0.5%`. Với 10,000 requests, tối đa 50 requests được phép lỗi hoặc chậm hơn ngưỡng SLO.
- **Alerts:** `high_latency_p95` warning trong 5 phút, `high_error_rate` critical trong 3 phút, `low_retrieval_success` warning trong 5 phút. Cấu hình tại [config/alert_rules.yaml](../config/alert_rules.yaml), runbook tại [docs/alerts.md](../docs/alerts.md).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`.
- **Incident:** `rag_slow`.
- **Khoảng thời gian đại diện:** 2026-09-30 21:24:44 ICT (2026-09-30 14:24:44Z).
- **Triệu chứng từ metrics:** Latency P95 tăng lên khoảng 3.5s, vượt challenge threshold 2s. Root trace đại diện mất 3.70s.
- **Log và correlation ID:** Event `response_sent`, `correlation_id=req-8343780c`, `latency_ms=3696`, `ttft_ms=50`, `tool_name=retrieval`, `tool_success=true`, `cost_usd=0.002295`.
- **Trace và span gây ảnh hưởng:** Trace ID `beb9b781881a9943cb33ebb10abfa5de`; root `lab-agent-run` 3.70s; `retrieval` 2.50s; `generation` 0.16s.
- **Root cause:** Incident `rag_slow` thêm độ trễ 2.5 giây vào retrieval. Generation vẫn khoảng 0.16 giây, nên retrieval là bottleneck.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable` và xác nhận `rag_slow`, `tool_fail`, `cost_spike` đều `False`.
- **Preventive measure:** Alert `high_latency_p95` khi P95 > 3000ms trong 5 phút; runbook yêu cầu lọc log theo `correlation_id`, mở trace tương ứng và kiểm tra retrieval trước.

Chuỗi evidence:

```text
P95 ≈ 3.5s > 2s
→ response_sent, correlation_id=req-8343780c, latency_ms=3696
→ trace beb9b781881a9943cb33ebb10abfa5de
→ retrieval span=2.50s
→ root cause=rag_slow
```

## 8. Giải thích và tự đánh giá

- **Quyết định kỹ thuật quan trọng:** Scrub PII trước cả log serialization và trace export, thay vì chỉ che ở giao diện. Cách này ngăn dữ liệu nhạy cảm rời khỏi process qua hai kênh telemetry.
- **Lỗi/blocker đã gặp:** App từng dùng `local-fallback` dù Langfuse authentication thành công.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra `auth_check()` thành công nhưng `get_prompt(..., label="production")` trả 404. Fetch theo version cho thấy prompt tồn tại nhưng thiếu label `production`; gắn lại labels đúng cho v1 rồi chạy request mới và flush trace.
- **Luồng Metrics → Logs → Traces:** Metrics phát hiện thời điểm P95 tăng; log tại cùng thời điểm cung cấp request đại diện và `correlation_id`; trace dùng cùng ID phân rã thời gian theo root/retrieval/generation để xác định bottleneck.
- **Vai trò vận hành LLM:** Prompt version và labels hỗ trợ thử candidate, promote và rollback không sửa code. Token/cost giúp phát hiện model usage bất thường. SLO/error budget định nghĩa mức chấp nhận được; alert và runbook chuyển tín hiệu thành hành động điều tra.
- **Điều quan trọng nhất đã học:** Một metric chỉ báo có sự cố; correlation ID và distributed trace mới cho biết request nào bị ảnh hưởng và span nào là nguyên nhân.
- **Hạn chế còn lại:** Dashboard đang được chia thành 11a–11e và chưa thể hiện rõ đầy đủ sáu panel cùng threshold/SLO. Commit SHA chỉ điền sau commit cuối đã push.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có 3 file text và evidence runtime 01–14 theo yêu cầu CP4.
- [x] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README trên commit cuối.
- [x] Ba output text đã được tạo từ lần chạy mới nhất.
- [x] Không dùng evidence của học viên hoặc lớp khác.
- [ ] Không có secret, API key hoặc PII thô trong commit cuối.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
