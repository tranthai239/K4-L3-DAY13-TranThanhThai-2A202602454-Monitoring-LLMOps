from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_dashboard.py"


def test_generated_dashboard_contains_six_panels_and_scrubs_log_content(tmp_path: Path) -> None:
    logs = tmp_path / "logs.jsonl"
    output = tmp_path / "dashboard.html"
    logs.write_text(
        '\n'.join([
            '{"event":"request_received","ts":"2026-09-30T10:00:00Z","correlation_id":"req-safe"}',
            '{"event":"response_sent","ts":"2026-09-30T10:00:01Z","latency_ms":450,"ttft_ms":50,"tokens_in":20,"tokens_out":30,"cost_usd":0.001,"quality_score":0.9,"tool_success":true,"payload":{"answer_preview":"private@example.com"}}',
            '{"event":"request_received","ts":"2026-09-30T10:10:00Z"}',
            '{"event":"request_failed","ts":"2026-09-30T10:10:01Z","error_type":"TimeoutError"}',
            '{"event":"response_sent","ts":"2026-09-30T10:20:00Z","latency_ms":3696,"ttft_ms":50,"tokens_in":25,"tokens_out":40,"cost_usd":0.002,"quality_score":0.8,"tool_success":true,"correlation_id":"req-8343780c"}',
        ]) + '\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--logs", str(logs), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    page = output.read_text(encoding="utf-8")
    for expected in (
        "Latency percentiles and TTFT", "Request traffic", "Error rate and retrieval success",
        "Cost over time", "Input and output tokens", "Quality proxy", "3000 ms",
        "requests/min", "retrieval success", "50,000", "0.75", "Input / Output tokens",
        "3696 ms", "Last 1 day",
    ):
        if expected == "Input / Output tokens":
            assert "input / output tokens" in page
        elif expected == "3696 ms":
            assert "3696 ms" in page
        else:
            assert expected.lower() in page.lower()
    assert "private@example.com" not in page
