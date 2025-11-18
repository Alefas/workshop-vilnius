import os
import time
import html as _html

__all__ = ["build_html_report"]


def build_html_report(dataset_path: str, metrics: dict) -> str:
    """
    Build a standalone HTML dashboard with key metrics and a timing distribution (SVG histogram).
    Extracted from eval.py for reuse and cleaner structure.
    """
    ds_name = os.path.basename(dataset_path)

    # Prepare numbers with safe defaults
    def fmt(v, fmtstr="{:.2f}"):
        if v is None:
            return "N/A"
        try:
            return fmtstr.format(v)
        except Exception:
            return str(v)

    durations = metrics.get("durations_ms", []) or []
    avg_ms = float(metrics.get("avg_extract_ms", 0.0) or 0.0)

    # Build histogram data
    bins = 20
    width = 900
    height = 260
    pad_left = 50
    pad_bottom = 30
    plot_w = width - pad_left - 20
    plot_h = height - pad_bottom - 20

    if durations:
        dmin = min(durations)
        dmax = max(durations)
        # If all equal, widen a bit for visibility
        if dmax == dmin:
            dmax = dmin + 1.0
        bin_w = (dmax - dmin) / bins
        counts = [0] * bins
        for v in durations:
            idx = int((v - dmin) / bin_w)
            if idx >= bins:
                idx = bins - 1
            counts[idx] += 1
        max_count = max(counts) if counts else 1
    else:
        dmin = 0.0
        dmax = 1.0
        counts = [0] * bins
        max_count = 1

    # Build bars as SVG rects
    bar_svg = []
    if sum(counts) > 0:
        for i, c in enumerate(counts):
            x = pad_left + int(i * (plot_w / bins))
            bar_w = int(plot_w / bins) - 2
            h = int((c / max_count) * plot_h)
            y = 10 + (plot_h - h)
            bar_svg.append(
                f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="#4F46E5" opacity="0.8" />'
            )
    # Axis labels
    x_min_lbl = fmt(dmin, "{:.1f}")
    x_max_lbl = fmt(dmax, "{:.1f}")

    # Average line
    avg_x = None
    if durations and dmax > dmin:
        avg_ratio = (avg_ms - dmin) / (dmax - dmin)
        avg_x = pad_left + int(avg_ratio * plot_w)

    avg_line_svg = (
        f'<line x1="{avg_x}" y1="10" x2="{avg_x}" y2="{10+plot_h}" stroke="#EF4444" stroke-width="2" stroke-dasharray="4,3" />'
        if avg_x is not None else ""
    )

    # Cards
    def card(title, value, desc="", tooltip: str = ""):
        return (
            f'<div class="card" title="{_html.escape(tooltip)}">'
            f'<div class="card-title">{_html.escape(title)}</div>'
            f'<div class="card-value">{_html.escape(value)}</div>'
            f'<div class="card-desc">{_html.escape(desc)}</div>'
            f'</div>'
        )

    precision = metrics.get("precision", 0.0)
    recall = metrics.get("recall", 0.0)
    f1 = metrics.get("f1", 0.0)
    fn_rate = metrics.get("fn_rate_pos_percent")
    fp_rate = metrics.get("fp_rate_neg_percent")

    cards_html = "".join([
        card(
            "Dataset",
            ds_name,
            os.path.abspath(dataset_path),
            tooltip="Name of the dataset file used for evaluation"
        ),
        card(
            "Samples",
            str(metrics.get("count", 0)),
            tooltip="Total number of rows evaluated (regardless of label availability)"
        ),
        card(
            "Precision",
            fmt(precision, "{:.3f}"),
            tooltip="Overall match rate: (TP + TN) / (TP + FP + FN + TN). Proportion where predicted is_task matches the label"
        ),
        card(
            "Recall",
            fmt(recall, "{:.3f}"),
            tooltip="Recall (sensitivity) among positives: TP / (TP + FN)"
        ),
        card(
            "F1",
            fmt(f1, "{:.3f}"),
            tooltip="Harmonic mean of standard precision and recall: 2 * P * R / (P + R), with P = TP / (TP + FP)"
        ),
        card(
            "Avg task F1",
            fmt(metrics.get("avg_task_f1"), "{:.3f}"),
            tooltip="Average token-set F1 between predicted task text and gold_task over rows where gold_task is provided"
        ),
        card(
            "FN rate when gold=True",
            (fmt(fn_rate, "{:.2f}") + "%") if fn_rate is not None else "N/A",
            tooltip="Among actual tasks (gold=1), percentage predicted as non-task (False Negative rate)"
        ),
        card(
            "FP rate when gold=False",
            (fmt(fp_rate, "{:.2f}") + "%") if fp_rate is not None else "N/A",
            tooltip="Among actual non-tasks (gold=0), percentage predicted as task (False Positive rate)"
        ),
        card(
            "Avg extract time",
            fmt(avg_ms, "{:.2f}") + " ms",
            tooltip="Average runtime of extract_task per row in milliseconds"
        ),
    ])

    # Prepare variables for f-string template
    cards = cards_html
    avg_line = avg_line_svg
    bars = "\n        ".join(bar_svg)
    height_minus = height - 6
    x_max_x = width - 6

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Evaluation Report - { _html.escape(ds_name) }</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --card: #1f2937;
      --text: #e5e7eb;
      --subtext: #9ca3af;
      --primary: #4f46e5;
      --accent: #22d3ee;
    }}
    body {{
      margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\";
      background: linear-gradient(180deg, #0b1020, #0f172a);
      color: var(--text);
    }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }}
    .title {{ font-size: 28px; font-weight: 700; letter-spacing: .5px; }}
    .subtitle {{ color: var(--subtext); font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 16px 0 20px; }}
    .card {{ background: linear-gradient(180deg, #1f2937, #111827); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 14px; box-shadow: 0 10px 25px rgba(0,0,0,.3); }}
    .card-title {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--subtext); margin-bottom: 6px; }}
    /* Use inherit so light mode shows dark text instead of forced white */
    .card-value {{ font-size: 22px; font-weight: 700; color: inherit; }}
    .card-desc {{ font-size: 12px; color: var(--subtext); margin-top: 4px; word-break: break-all; }}
    .panel {{ background: linear-gradient(180deg, #111827, #0b1220); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px; margin-top: 14px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 18px 40px rgba(0,0,0,.35); }}
    .panel-title {{ font-size: 16px; font-weight: 600; margin-bottom: 10px; }}
    .axis {{ fill: var(--subtext); font-size: 11px; }}
  </style>
  <meta name=\"color-scheme\" content=\"dark light\" />
  <meta name=\"description\" content=\"Evaluation dashboard for task extraction\" />
  <meta name=\"generated\" content=\"{time.strftime('%Y-%m-%d %H:%M:%S')}\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"dns-prefetch\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"dns-prefetch\" href=\"https://fonts.gstatic.com\" />
  <style>@media (prefers-color-scheme: light) {{ body {{ background: #f9fafb; color: #111827; }} .card, .panel {{ background: #fff; }} .card-title, .subtitle, .axis {{ color: #4b5563; }} }}</style>
  <noscript>
    <style>
      .subtitle::after {{ content: " • (JS disabled)"; color: var(--subtext); }}
    </style>
  </noscript>
  <!-- Simple, dependency-free report -->
  <!-- Timing histogram rendered as inline SVG for portability -->
  <!-- Dataset: { _html.escape(ds_name) } -->
  <!-- Counts: tp={metrics.get('tp')} fp={metrics.get('fp')} fn={metrics.get('fn')} tn={metrics.get('tn')} -->
  <!-- Avg extract (ms): {fmt(avg_ms)} -->
  
</head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <div class=\"title\">Task Extraction Evaluation</div>
      <div class=\"subtitle\">Dataset: { _html.escape(ds_name) } • Generated { time.strftime('%Y-%m-%d %H:%M') }</div>
    </div>

    <div class=\"grid\">
      {cards}
    </div>

    <div class=\"panel\">
      <div class=\"panel-title\">Extract time distribution (ms)</div>
      <svg width=\"{width}\" height=\"{height}\" role=\"img\" aria-label=\"Histogram of extract times\">
        <rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"transparent\" />
        {avg_line}
        {bars}
        <!-- X axis labels -->
        <text x=\"{pad_left}\" y=\"{height_minus}\" class=\"axis\">{x_min_lbl} ms</text>
        <text x=\"{x_max_x}\" y=\"{height_minus}\" class=\"axis\" text-anchor=\"end\">{x_max_lbl} ms</text>
      </svg>
    </div>

    <div class=\"panel\" style=\"margin-top: 16px;\">
      <div class=\"panel-title\">Confusion summary</div>
      <div class=\"grid\">
        {card("True Positives", str(metrics.get("tp", 0)), tooltip="Predicted is_task=True and label=1")}
        {card("False Positives", str(metrics.get("fp", 0)), tooltip="Predicted is_task=True but label=0")}
        {card("False Negatives", str(metrics.get("fn", 0)), tooltip="Predicted is_task=False but label=1")}
        {card("True Negatives", str(metrics.get("tn", 0)), tooltip="Predicted is_task=False and label=0")}
      </div>
    </div>
  </div>
</body>
</html>
"""
    return html
