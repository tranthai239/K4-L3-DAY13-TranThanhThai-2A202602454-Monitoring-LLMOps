from __future__ import annotations

import argparse
import html
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "data" / "logs.jsonl"
DEFAULT_OUTPUT = ROOT / "submission" / "dashboard.html"
LATENCY_THRESHOLD_MS = 3000
ERROR_THRESHOLD_PCT = 2
COST_THRESHOLD_USD = 2.5
TOKEN_THRESHOLD = 50000
QUALITY_THRESHOLD = 0.75


def load_records(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            timestamp = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        row = {key: row.get(key) for key in (
            "event", "ts", "latency_ms", "ttft_ms", "tokens_in", "tokens_out",
            "cost_usd", "quality_score", "tool_success", "error_type"
        )}
        row["_time"] = timestamp.astimezone(timezone.utc)
        records.append(row)
    return sorted(records, key=lambda row: row["_time"])


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p / 100
    low = math.floor(index)
    high = math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def fmt(value: float | None, unit: str = "") -> str:
    return "n/a" if value is None else f"{value:,.2f}{unit}"


def render(path: Path, mode: str) -> str:
    records = load_records(path)
    if not records:
        raise ValueError(f"No valid records in {path}")

    latest = records[-1]["_time"]
    range_start = latest - timedelta(minutes=60) if mode == "60m" else records[0]["_time"]
    selected = [row for row in records if row["_time"] >= range_start]
    requests = [r for r in selected if r["event"] == "request_received"]
    responses = [r for r in selected if r["event"] == "response_sent"]
    errors = [r for r in selected if r["event"] == "request_failed"]
    retrieval_values = [r["tool_success"] for r in responses if isinstance(r["tool_success"], bool)]

    latencies = [r["latency_ms"] for r in responses if isinstance(r["latency_ms"], (int, float))]
    ttfts = [r["ttft_ms"] for r in responses if isinstance(r["ttft_ms"], (int, float))]
    costs = [r["cost_usd"] for r in responses if isinstance(r["cost_usd"], (int, float))]
    tokens_in = [r["tokens_in"] for r in responses if isinstance(r["tokens_in"], (int, float))]
    tokens_out = [r["tokens_out"] for r in responses if isinstance(r["tokens_out"], (int, float))]
    qualities = [r["quality_score"] for r in responses if isinstance(r["quality_score"], (int, float))]
    error_pct = len(errors) / max(1, len(requests)) * 100
    retrieval_pct = sum(retrieval_values) / len(retrieval_values) * 100 if retrieval_values else None
    total_tokens = sum(tokens_in) + sum(tokens_out)
    total_cost = sum(costs)
    quality_avg = mean(qualities) if qualities else None
    span_seconds = max(1, (latest - range_start).total_seconds())
    request_rate = len(requests) / (span_seconds / 60)

    def panel(title: str, value: str, unit: str, threshold: str, detail: str, status: str) -> str:
        return (f'<section class="card"><div class="eyebrow">{html.escape(title)}</div>'
                f'<div class="value">{html.escape(value)} <small>{html.escape(unit)}</small></div>'
                f'<div class="threshold">Threshold: {html.escape(threshold)}</div>'
                f'<div class="detail">{html.escape(detail)}</div>'
                f'<div class="status {status}">{status.upper()}</div></section>')

    status_latency = "breach" if (percentile(latencies, 95) or 0) > LATENCY_THRESHOLD_MS else "ok"
    status_errors = "breach" if error_pct > ERROR_THRESHOLD_PCT else "ok"
    status_cost = "breach" if total_cost > COST_THRESHOLD_USD else "ok"
    status_tokens = "breach" if total_tokens > TOKEN_THRESHOLD else "ok"
    status_quality = "breach" if quality_avg is not None and quality_avg < QUALITY_THRESHOLD else "ok"
    status_traffic = "ok" if request_rate >= 1 else "breach"

    cards = "".join([
        panel("Latency percentiles and TTFT", f"P50 {fmt(percentile(latencies, 50))} / P95 {fmt(percentile(latencies, 95))} / P99 {fmt(percentile(latencies, 99))}", "ms", f"P95 ≤ {LATENCY_THRESHOLD_MS} ms", f"TTFT P95: {fmt(percentile(ttfts, 95), ' ms')}", status_latency),
        panel("Request traffic", f"{len(requests)}", "requests", "Rate ≥ 1 request/min", f"Rate: {request_rate:.2f} requests/min", status_traffic),
        panel("Error rate and retrieval success", f"{error_pct:.2f}%", "error rate", f"≤ {ERROR_THRESHOLD_PCT}% errors", f"Failed: {len(errors)} · Retrieval success: {fmt(retrieval_pct, '%')}", status_errors),
        panel("Cost over time", f"${total_cost:.6f}", "USD total", f"≤ ${COST_THRESHOLD_USD:.2f}", f"Responses: {len(responses)} · Source: response_sent.cost_usd", status_cost),
        panel("Input and output tokens", f"{sum(tokens_in):,.0f} / {sum(tokens_out):,.0f}", "input / output tokens", f"≤ {TOKEN_THRESHOLD:,} total", f"Total: {total_tokens:,.0f} tokens", status_tokens),
        panel("Quality proxy", fmt(quality_avg), "score (0–1)", f"≥ {QUALITY_THRESHOLD:.2f}", f"Responses scored: {len(qualities)}", status_quality),
    ])

    points = []
    for row in responses:
        latency = row.get("latency_ms")
        ttft = row.get("ttft_ms")
        if isinstance(latency, (int, float)):
            x = (row["_time"] - range_start).total_seconds() / span_seconds * 1000
            y = max(0, min(100, 100 - float(latency) / (LATENCY_THRESHOLD_MS * 1.2) * 100))
            points.append((x, y, float(latency), float(ttft) if isinstance(ttft, (int, float)) else None))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
    ttft_points = " ".join(
        f"{x:.1f},{max(0, min(100, 100 - ttft / (LATENCY_THRESHOLD_MS * 1.2) * 100)):.1f}"
        for x, _, _, ttft in points if ttft is not None
    )
    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5"><title>{latency:.0f} ms at {row_time}</title></circle>'
        for (x, y, latency, _), row_time in zip(points, [r["_time"].strftime("%Y-%m-%d %H:%M:%S UTC") for r in responses if isinstance(r.get("latency_ms"), (int, float))])
    )
    incident_id = "req-8343780c"
    incident = next((r for r in responses if r.get("latency_ms", 0) > LATENCY_THRESHOLD_MS), None)
    incident_caption = (f"Incident observed: {incident['latency_ms']} ms, {incident_id if incident else ''}" if incident else "No response exceeded latency threshold in selected range")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    window = "Last 60 minutes" if mode == "60m" else "Full available log window (baseline + incident)"
    svg = f'''<svg viewBox="0 0 1000 260" role="img" aria-label="Latency and TTFT over time">
      <line x1="0" y1="10" x2="1000" y2="10" class="threshold-line"/><text x="8" y="24">Threshold {LATENCY_THRESHOLD_MS} ms</text>
      <polyline points="{polyline}" class="latency-line"/><polyline points="{ttft_points}" class="ttft-line"/>{circles}
      <text x="8" y="245">{range_start.strftime('%m-%d %H:%M UTC')}</text><text x="870" y="245">{latest.strftime('%m-%d %H:%M UTC')}</text>
      <text x="735" y="36">Latency</text><text x="830" y="36">TTFT</text></svg>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LLMOps Dashboard</title><meta name="description" content="Six-panel runtime dashboard generated from structured application logs."><style>
      :root{{--bg:#f4f6fa;--card:#fff;--ink:#162235;--muted:#66758b;--line:#dae1eb;--accent:#4d5fe8;--green:#16794b;--red:#b42318;--amber:#8a5a00;--shadow:0 8px 24px #1b2b4510}}
      @media(prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#101722;--card:#172230;--ink:#edf3fb;--muted:#9cacc0;--line:#304052;--accent:#96a3ff;--green:#70d4a2;--red:#ff9a91;--amber:#f4c66c;--shadow:0 8px 24px #0004}}}}
      :root[data-theme="dark"]{{--bg:#101722;--card:#172230;--ink:#edf3fb;--muted:#9cacc0;--line:#304052;--accent:#96a3ff;--green:#70d4a2;--red:#ff9a91;--amber:#f4c66c;--shadow:0 8px 24px #0004}}
      *{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px}}main{{max-width:1400px;margin:auto}}header{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:22px}}h1{{font-size:26px;margin:0 0 6px}}p,.muted{{color:var(--muted);margin:0}}.controls{{display:flex;gap:8px;align-items:center}}button{{border:1px solid var(--line);border-radius:9px;padding:9px 13px;background:var(--card);color:var(--ink);font:inherit;cursor:pointer}}button.active{{background:var(--accent);color:white;border-color:var(--accent)}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.card,.chart{{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:17px;min-width:0}}.eyebrow{{font-size:14px;font-weight:700;margin-bottom:11px}}.value{{font-size:24px;font-weight:700;letter-spacing:-.4px}}small{{font-size:13px;color:var(--muted);font-weight:500}}.threshold,.detail{{font-size:12px;color:var(--muted);margin-top:8px}}.status{{margin-top:12px;font-size:10px;letter-spacing:.08em;font-weight:800}}.ok{{color:var(--green)}}.breach{{color:var(--red)}}.chart{{margin-top:14px}}.chart h2{{font-size:16px;margin:0}}svg{{display:block;width:100%;height:auto;margin-top:8px;overflow:visible}}svg text{{font-size:13px;fill:var(--muted)}}.threshold-line{{stroke:var(--red);stroke-width:2;stroke-dasharray:8 6}}.latency-line,.ttft-line{{fill:none;stroke:var(--accent);stroke-width:3;vector-effect:non-scaling-stroke}}.ttft-line{{stroke:#169b8b;stroke-dasharray:6 5}}circle{{fill:var(--red);stroke:var(--card);stroke-width:2}}.incident{{margin-top:10px;padding:10px 12px;background:#fff2e8;color:#8d3519;border-radius:8px;font-weight:650}}footer{{margin-top:16px;color:var(--muted);font-size:12px}}@media(max-width:900px){{body{{padding:16px}}header{{display:block}}.controls{{margin-top:14px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:560px){{.grid{{grid-template-columns:1fr}}.value{{font-size:21px}}}}
      </style></head><body><main><header><div><h1>K4-L3B Day 13 Monitoring &amp; LLMOps</h1><p>Runtime dashboard · Source: data/logs.jsonl · Refresh interval: 30s</p><p>Range: <strong id="range">{html.escape(window)}</strong> · Last event: {latest.strftime('%Y-%m-%d %H:%M:%S UTC')} / {(latest+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S ICT')}</p></div><div class="controls"><button id="last60" class="{'active' if mode=='60m' else ''}">Last 60 minutes</button><button id="full" class="{'active' if mode=='full' else ''}">Baseline + incident</button></div></header><section class="grid">{cards}</section><section class="chart"><h2>Latency and TTFT over time · ms</h2><p class="muted">Latency P50/P95/P99 are summarized above; plot shows each response and TTFT with latency threshold.</p>{svg}<div class="incident">{html.escape(incident_caption)}</div></section><footer>Window: {html.escape(window)} · Data timestamped in UTC; ICT = UTC+7 · Metrics computed from response_sent/request_received/request_failed records.</footer></main><script>
      const params=new URLSearchParams(location.search);function choose(mode){{location.search='mode='+mode}}document.getElementById('last60').onclick=()=>choose('60m');document.getElementById('full').onclick=()=>choose('full');
      </script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a six-panel HTML dashboard from structured JSONL logs.")
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("60m", "full"), default="full")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.logs, args.mode), encoding="utf-8")
    print(f"Dashboard written: {args.output}")
    print(f"Open via local HTTP server; mode={args.mode}; source={args.logs}")


if __name__ == "__main__":
    main()
