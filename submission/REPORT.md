# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:**TRẦN THANH THÁI
- **MSSV:**2A202602454
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-<MSSV>`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 100/100 | | 4 mục PASSED (schema, correlation ID, enrichment, PII) |
| `validate_dashboard.py` | 6/6 panel | | HỢP LỆ: 6/6 panel có trong dashboard contract |
| `pytest` | 24 passed | | 24 passed in 1.55s |
| Số traces hợp lệ | 10 | | Langfuse kết nối thành công, traces đã gửi |
| Số PII leak | 0 | | Không phát hiện PII rò rỉ |
| Latency P95 / TTFT P95 | ~489ms / ~50ms | | Dựa trên load_test 10 requests |
| Retrieval success rate | 100% | | Tất cả 10 requests đều tool_success: true |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận header `x-request-id` hoặc tự sinh `req-<8-hex>`. ID được bind vào structlog contextvars và trả về qua response header.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` đăng ký trước `JsonlFileProcessor` trong chuỗi structlog. Dùng regex che email, SĐT VN, CCCD, thẻ tín dụng.
- **Cách kiểm chứng kết quả:** `validate_logs.py` đạt 100/100. Pytest 24 passed.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Vào Langfuse → project `day13-k4-l3b-2A202602454` → tab Traces.
- **Cấu trúc root/retrieval/generation observations:** Root `lab-agent-run` (agent) → child `retrieval` (span) → child `generation` (generation, có model, tokens, cost).
- **Cách nối trace với log:** Cả trace metadata và log đều chứa cùng `correlation_id`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1, labels: `baseline` + `production`
- **Version/label candidate:** Version 2, label: `candidate`
- **Trace ID của mỗi version:** (Điền sau khi chạy workload)
- **Cách promote và rollback `production`:** Trên Langfuse UI, chọn version mới → gắn label `production`. Rollback: chọn version cũ → gắn lại label `production`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Latency (P50/P95/P99 + TTFT), Traffic (request count), Errors (error rate + retrieval success), Cost (sum/minute), Tokens (in/out), Quality (mean score).
- **SLO và lý do chọn:** 99.5% request thành công với latency ≤ 3000ms trong 28 ngày. Ngưỡng gấp ~6 lần baseline P95.
- **Cách tính error budget:** 100% - 99.5% = 0.5%. Với 10,000 request → tối đa 50 request lỗi/chậm.
- **Ba alert và runbook tương ứng:** (1) `high_latency_p95` warning 5m, (2) `high_error_rate` critical 3m, (3) `low_retrieval_success` warning 5m. Chi tiết tại `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
