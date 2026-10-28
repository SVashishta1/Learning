"""dashboard.py: turn results/history.jsonl into results/dashboard.html (a chart of every score over every run).

python dashboard.py      then open results/dashboard.html in your browser. No extra packages needed.
"""
import html
import json
from pathlib import Path

RESULTS = Path(__file__).with_name("results")
COLORS = ["#2a78d6", "#d64f2a", "#2aa84a", "#9b59b6", "#c99a06", "#127c8a"]


def build(history: list[dict]) -> str:
    metrics = sorted({m for run in history for m in run["scores"]})
    w, h, pad = 760, 300, 45
    x = lambda i: pad + (w - 2 * pad) * (i / max(len(history) - 1, 1))
    y = lambda v: h - pad - (h - 2 * pad) * v                       # score 0..1 -> pixels (1 at the top)
    svg = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Eval scores over runs">']
    for v in (0, 0.25, 0.5, 0.75, 1):                               # grid lines
        svg.append(f'<line x1="{pad}" x2="{w - pad}" y1="{y(v)}" y2="{y(v)}" class="grid"/>'
                   f'<text x="{pad - 8}" y="{y(v) + 4}" text-anchor="end">{v:.2f}</text>')
    for i, run in enumerate(history):
        svg.append(f'<text x="{x(i)}" y="{h - pad + 18}" text-anchor="middle">#{i + 1} {html.escape(run["system"])} {html.escape(run["version"])}</text>')
    for color, metric in zip(COLORS * 3, metrics):
        points = [(x(i), y(run["scores"][metric])) for i, run in enumerate(history) if metric in run["scores"]]
        svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" '
                   f'points="{" ".join(f"{px:.1f},{py:.1f}" for px, py in points)}"/>')
        svg += [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{color}"/>' for px, py in points]
    svg.append("</svg>")
    legend = "".join(f'<span><i style="background:{c}"></i>{m}</span>' for c, m in zip(COLORS * 3, metrics))
    head = "".join(f"<th>{m}</th>" for m in metrics)
    rows = "".join(
        f"<tr><td>#{i + 1}</td><td>{html.escape(r['timestamp'])}</td><td>{html.escape(r['commit'])}</td>"
        f"<td>{html.escape(r['system'])} {html.escape(r['version'])}</td><td>{html.escape(r['model'])}</td>"
        + "".join(f"<td>{r['scores'][m]:.3f}</td>" if m in r["scores"] else "<td>-</td>" for m in metrics)
        + f"<td>{r['passed']}/{r['cases']}</td><td>${r['cost_usd']}</td></tr>" for i, r in enumerate(history))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Eval Dashboard</title>
<style>
:root {{ --bg:#ffffff; --fg:#1d1d1f; --muted:#6e6e73; --line:#e3e3e8; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#16171a; --fg:#ececf0; --muted:#9a9aa3; --line:#2c2d33; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; margin:0; padding:16px; }}
main {{ max-width:860px; margin:auto; }} svg {{ width:100%; height:auto; }}
svg text {{ fill:var(--muted); font-size:11px; }} .grid {{ stroke:var(--line); }}
.legend span {{ margin-right:14px; white-space:nowrap; }} .legend i {{ display:inline-block; width:10px; height:10px;
border-radius:2px; margin-right:5px; }} .table {{ overflow-x:auto; }}
table {{ border-collapse:collapse; font-size:13px; }} td, th {{ border-bottom:1px solid var(--line); padding:4px 8px; text-align:left; }}
</style></head><body><main>
<h1>Northwind assistant: eval scores over time</h1>
<p>{len(history)} runs from <code>results/history.jsonl</code>. Higher is better (1.0 = perfect).</p>
{''.join(svg)}<p class="legend">{legend}</p>
<div class="table"><table><tr><th>run</th><th>time (UTC)</th><th>commit</th><th>system</th><th>model</th>{head}<th>passed</th><th>cost</th></tr>{rows}</table></div>
</main></body></html>"""


if __name__ == "__main__":
    history_file = RESULTS / "history.jsonl"
    if not history_file.exists():
        raise SystemExit("No results yet. Run `python run_evals.py` first.")
    history = [json.loads(line) for line in history_file.open(encoding="utf-8") if line.strip()]
    out = RESULTS / "dashboard.html"
    out.write_text(build(history), encoding="utf-8")
    print(f"Wrote {out} with {len(history)} runs. Open it in your browser.")
