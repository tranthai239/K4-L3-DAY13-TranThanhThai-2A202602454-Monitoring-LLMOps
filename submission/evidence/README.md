# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Ba output text:

```text
pytest.txt
log-validator.txt
dashboard-validator.txt
```

Bộ evidence runtime theo yêu cầu CP4:

```text
01-pytest.png
02-log-validator.png
03-dashboard-validator.png
04-structured-log.png
05-pii-redaction.png
06-trace-list.png
07-trace-waterfall.png
08a-trace-metadata.png / 08b-generation-metadata.png
09-prompt-versions.png
10a-prompt-promote.png / 10b-prompt-rollback.png
11-dashboard-overview.png hoặc 11a/11b/11c...
12-incident-metric.png
13-incident-log.png
14-incident-trace.png
```

Ảnh Langfuse phải thuộc project cá nhân và thấy tên project/khoảng thời gian khi tiêu chí yêu cầu. Không mở/chụp trang API Keys. Không để lộ secret hoặc PII thô.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Incident trace](evidence/14-incident-trace.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
