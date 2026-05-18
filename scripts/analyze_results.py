from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path


STYLE_LABELS = {
    "description_to_rtl": "Description-to-RTL",
    "code_completion": "Code completion",
}


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/analyze_results.py runs/*/results.jsonl")

    run_paths = [Path(arg) for arg in sys.argv[1:]]
    run_records = [_load_run(path) for path in run_paths]
    task_styles = _load_task_styles(run_paths)

    tables_dir = Path("results/tables")
    figures_dir = Path("results/figures")
    summaries_dir = Path("results/summaries")
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    _write_run_summary_csv(tables_dir / "summary.csv", run_records)
    _write_run_summary_tex(tables_dir / "run_summary.tex", run_records)
    harness_summary = _harness_summary(run_records)
    _write_harness_summary_csv(tables_dir / "harness_summary.csv", harness_summary)
    _write_harness_summary_tex(tables_dir / "harness_summary.tex", harness_summary)

    style_summary = _style_summary(run_records, task_styles)
    _write_style_summary_csv(tables_dir / "style_summary.csv", style_summary)
    _write_style_summary_tex(tables_dir / "style_summary.tex", style_summary)

    failure_summary = _failure_summary(run_records)
    _write_failure_summary_csv(tables_dir / "failure_summary.csv", failure_summary)
    _write_failure_summary_tex(tables_dir / "failure_summary.tex", failure_summary)

    task_summary = _task_summary(run_records, task_styles)
    _write_task_summary_csv(tables_dir / "task_summary.csv", task_summary)
    _write_task_summary_tex(tables_dir / "task_summary.tex", task_summary)

    repair_outcomes = _repair_outcomes(run_records)
    _write_repair_outcomes_csv(tables_dir / "repair_outcomes.csv", repair_outcomes)
    _write_repair_outcomes_tex(tables_dir / "repair_outcomes.tex", repair_outcomes)

    _write_pass_rate_svg(figures_dir / "pass_rates.svg", run_records)
    _write_pass_rate_pdf(figures_dir / "pass_rates.pdf", run_records)
    _write_style_pdf(figures_dir / "style_pass_rates.pdf", style_summary)
    _write_failure_pdf(figures_dir / "failure_reasons.pdf", failure_summary)
    _write_repair_outcomes_pdf(figures_dir / "repair_outcomes.pdf", repair_outcomes)
    _write_notes(summaries_dir / "result_notes.txt", harness_summary, style_summary, failure_summary)

    print(tables_dir / "harness_summary.tex")
    print(tables_dir / "style_summary.tex")
    print(tables_dir / "failure_summary.tex")
    print(tables_dir / "repair_outcomes.tex")
    print(figures_dir / "pass_rates.pdf")


def _load_run(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise SystemExit(f"empty result file: {path}")
    return {"name": path.parent.name, "harness": rows[0]["harness"], "rows": rows}


def _load_task_styles(run_paths: list[Path]) -> dict[str, str]:
    dataset_path = run_paths[0].parent / "dataset.jsonl"
    if not dataset_path.exists():
        dataset_path = Path("datasets/cvdp/cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl")
    styles = {}
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        styles[row["id"]] = "description_to_rtl" if "cid003" in row["categories"] else "code_completion"
    return styles


def _reason(row: dict) -> str:
    return row.get("metadata", {}).get("verifier", {}).get("reason") or row.get("error") or "unknown"


def _write_run_summary_csv(path: Path, run_records: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["run", "harness", "tasks", "compiled", "simulated", "passed", "pass_rate", "failures_by_reason"])
        for record in sorted(run_records, key=lambda r: r["name"]):
            rows = record["rows"]
            total = len(rows)
            failures = Counter(_reason(row) for row in rows if not row["passed"])
            writer.writerow(
                [
                    record["name"],
                    record["harness"],
                    total,
                    sum(row["compiled"] for row in rows),
                    sum(row["simulated"] for row in rows),
                    sum(row["passed"] for row in rows),
                    f"{sum(row['passed'] for row in rows) / total:.3f}",
                    ";".join(f"{reason}:{count}" for reason, count in sorted(failures.items())),
                ]
            )


def _harness_summary(run_records: list[dict]) -> list[dict]:
    by_harness = defaultdict(list)
    for record in run_records:
        by_harness[record["harness"]].append(record)

    summary = []
    for harness, records in sorted(by_harness.items()):
        pass_counts = [sum(row["passed"] for row in record["rows"]) for record in records]
        compile_counts = [sum(row["compiled"] for row in record["rows"]) for record in records]
        total = len(records[0]["rows"])
        summary.append(
            {
                "harness": harness,
                "runs": len(records),
                "tasks": total,
                "mean_passed": _mean(pass_counts),
                "sd_passed": _sample_sd(pass_counts),
                "mean_pass_rate": _mean([count / total for count in pass_counts]),
                "sd_pass_rate": _sample_sd([count / total for count in pass_counts]),
                "mean_compiled": _mean(compile_counts),
                "mean_compile_rate": _mean([count / total for count in compile_counts]),
                "total_passed": sum(pass_counts),
                "total_trials": total * len(records),
            }
        )
    return summary


def _style_summary(run_records: list[dict], task_styles: dict[str, str]) -> list[dict]:
    counts = defaultdict(lambda: {"passed": 0, "trials": 0})
    for record in run_records:
        harness = record["harness"]
        for row in record["rows"]:
            style = task_styles[row["task_id"]]
            counts[(harness, style)]["passed"] += int(row["passed"])
            counts[(harness, style)]["trials"] += 1
    return [
        {"harness": harness, "style": style, **values, "pass_rate": values["passed"] / values["trials"]}
        for (harness, style), values in sorted(counts.items())
    ]


def _failure_summary(run_records: list[dict]) -> list[dict]:
    counts = defaultdict(Counter)
    for record in run_records:
        for row in record["rows"]:
            if not row["passed"]:
                counts[record["harness"]][_reason(row)] += 1
    return [
        {"harness": harness, "reason": reason, "count": count}
        for harness, counter in sorted(counts.items())
        for reason, count in sorted(counter.items())
    ]


def _task_summary(run_records: list[dict], task_styles: dict[str, str]) -> list[dict]:
    counts = defaultdict(lambda: defaultdict(lambda: {"passed": 0, "trials": 0, "repaired": 0}))
    for record in run_records:
        for row in record["rows"]:
            task = counts[row["task_id"]][record["harness"]]
            task["passed"] += int(row["passed"])
            task["trials"] += 1
            task["repaired"] += int(row["passed"] and row["attempts"] > 1)
    output = []
    for task_id, by_harness in sorted(counts.items()):
        output.append(
            {
                "task_id": task_id,
                "style": task_styles[task_id],
                "baseline_passed": by_harness["baseline"]["passed"],
                "baseline_trials": by_harness["baseline"]["trials"],
                "repair_passed": by_harness["sim_repair"]["passed"],
                "repair_trials": by_harness["sim_repair"]["trials"],
                "repair_after_feedback": by_harness["sim_repair"]["repaired"],
            }
        )
    return output


def _repair_outcomes(run_records: list[dict]) -> list[dict]:
    outcomes = []
    for record in sorted(run_records, key=lambda r: r["name"]):
        if record["harness"] != "sim_repair":
            continue
        initial_pass = sum(row["passed"] and row["attempts"] == 1 for row in record["rows"])
        repaired_pass = sum(row["passed"] and row["attempts"] > 1 for row in record["rows"])
        failed = sum(not row["passed"] for row in record["rows"])
        outcomes.append(
            {
                "run": record["name"],
                "initial_pass": initial_pass,
                "repaired_pass": repaired_pass,
                "failed": failed,
                "tasks": len(record["rows"]),
            }
        )
    outcomes.append(
        {
            "run": "total",
            "initial_pass": sum(row["initial_pass"] for row in outcomes),
            "repaired_pass": sum(row["repaired_pass"] for row in outcomes),
            "failed": sum(row["failed"] for row in outcomes),
            "tasks": sum(row["tasks"] for row in outcomes),
        }
    )
    return outcomes


def _write_harness_summary_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_run_summary_tex(path: Path, run_records: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Run & Harness & Compiled & Passed & Pass rate & Failures \\\\",
        "\\midrule",
    ]
    for record in sorted(run_records, key=lambda r: r["name"]):
        rows = record["rows"]
        total = len(rows)
        failures = Counter(_reason(row) for row in rows if not row["passed"])
        failure_text = ", ".join(f"{_reason_label(reason)}: {count}" for reason, count in sorted(failures.items())) or "--"
        lines.append(
            f"{record['name'].replace('_', '\\_')} & {_harness_label(record['harness'])} & "
            f"{sum(row['compiled'] for row in rows)}/{total} & {sum(row['passed'] for row in rows)}/{total} & "
            f"{100 * sum(row['passed'] for row in rows) / total:.1f}\\% & {failure_text} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_harness_summary_tex(path: Path, rows: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Harness & Runs & Tasks/run & Passed/run & Pass rate \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_harness_label(row['harness'])} & {row['runs']} & {row['tasks']} & "
            f"{row['mean_passed']:.2f} $\\pm$ {row['sd_passed']:.2f} & "
            f"{100 * row['mean_pass_rate']:.1f}\\% $\\pm$ {100 * row['sd_pass_rate']:.1f}\\% \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_style_summary_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["harness", "style", "passed", "trials", "pass_rate"])
        writer.writeheader()
        writer.writerows(rows)


def _write_style_summary_tex(path: Path, rows: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{llrr}",
        "\\toprule",
        "Harness & Task style & Passed/trials & Pass rate \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_harness_label(row['harness'])} & {STYLE_LABELS[row['style']]} & "
            f"{row['passed']}/{row['trials']} & {100 * row['pass_rate']:.1f}\\% \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_failure_summary_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["harness", "reason", "count"])
        writer.writeheader()
        writer.writerows(rows)


def _write_failure_summary_tex(path: Path, rows: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{llr}",
        "\\toprule",
        "Harness & Failure reason & Count \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(f"{_harness_label(row['harness'])} & {_reason_label(row['reason'])} & {row['count']} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_task_summary_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_task_summary_tex(path: Path, rows: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{llrrr}",
        "\\toprule",
        "Task & Style & Baseline & Repair & Fixed after feedback \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_short_task(row['task_id'])} & {STYLE_LABELS[row['style']]} & "
            f"{row['baseline_passed']}/{row['baseline_trials']} & "
            f"{row['repair_passed']}/{row['repair_trials']} & "
            f"{row['repair_after_feedback']} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_repair_outcomes_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["run", "initial_pass", "repaired_pass", "failed", "tasks"])
        writer.writeheader()
        writer.writerows(rows)


def _write_repair_outcomes_tex(path: Path, rows: list[dict]) -> None:
    lines = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Repair run & Initial pass & Fixed by repair & Failed & Tasks \\\\",
        "\\midrule",
    ]
    for row in rows:
        label = "Total" if row["run"] == "total" else row["run"].replace("_", "\\_")
        lines.append(f"{label} & {row['initial_pass']} & {row['repaired_pass']} & {row['failed']} & {row['tasks']} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_pass_rate_svg(path: Path, run_records: list[dict]) -> None:
    records = sorted(run_records, key=lambda r: (r["harness"], r["name"]))
    width, height = 640, 360
    left, bottom, top = 70, 300, 30
    bar_w, gap = 54, 24
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#222"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{width - 20}" y2="{bottom}" stroke="#222"/>',
    ]
    for pct in [0, 25, 50, 75, 100]:
        y = bottom - (bottom - top) * pct / 100
        parts.append(f'<line x1="{left - 5}" y1="{y:.1f}" x2="{width - 20}" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{pct}%</text>')
    x = left + 25
    colors = {"baseline": "#4C78A8", "sim_repair": "#F58518"}
    for record in records:
        rate = sum(row["passed"] for row in record["rows"]) / len(record["rows"])
        h = (bottom - top) * rate
        y = bottom - h
        color = colors.get(record["harness"], "#666")
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="sans-serif" font-size="12">{100 * rate:.1f}%</text>')
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{bottom + 18}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11" transform="rotate(35 {x + bar_w / 2:.1f},{bottom + 18})">{record["name"]}</text>'
        )
        x += bar_w + gap
    parts.append('<text x="320" y="22" text-anchor="middle" font-family="sans-serif" font-size="15">Pass rate by run</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _write_pass_rate_pdf(path: Path, run_records: list[dict]) -> None:
    plt = _plt()

    records = sorted(run_records, key=lambda r: (r["harness"], r["name"]))
    labels = [record["name"].replace("_", " ") for record in records]
    rates = [sum(row["passed"] for row in record["rows"]) / len(record["rows"]) for record in records]
    colors = ["#4C78A8" if record["harness"] == "baseline" else "#F58518" for record in records]

    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    bars = ax.bar(range(len(records)), rates, color=colors)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Pass rate")
    ax.set_xticks(range(len(records)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.025, f"{100 * rate:.1f}%", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _write_style_pdf(path: Path, rows: list[dict]) -> None:
    plt = _plt()
    harnesses = ["baseline", "sim_repair"]
    styles = ["description_to_rtl", "code_completion"]
    rates = {(row["harness"], row["style"]): row["pass_rate"] for row in rows}
    colors = {"baseline": "#4C78A8", "sim_repair": "#F58518"}

    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    x_positions = [0, 1]
    width = 0.34
    for offset, harness in [(-width / 2, "baseline"), (width / 2, "sim_repair")]:
        values = [rates[(harness, style)] for style in styles]
        bars = ax.bar([x + offset for x in x_positions], values, width=width, label=_harness_label(harness), color=colors[harness])
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{100 * value:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Pass rate")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([STYLE_LABELS[style] for style in styles], rotation=12, ha="right")
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _write_failure_pdf(path: Path, rows: list[dict]) -> None:
    plt = _plt()
    harnesses = ["baseline", "sim_repair"]
    reasons = sorted({row["reason"] for row in rows})
    counts = {(row["harness"], row["reason"]): row["count"] for row in rows}
    colors = {"compile_failed": "#E45756", "simulation_failed": "#72B7B2", "harness_failed": "#54A24B"}

    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    bottoms = [0, 0]
    for reason in reasons:
        values = [counts.get((harness, reason), 0) for harness in harnesses]
        bars = ax.bar([0, 1], values, bottom=bottoms, label=_reason_label(reason).replace("\\_", " "), color=colors.get(reason, "#888"))
        for i, (bar, value) in enumerate(zip(bars, values)):
            if value:
                ax.text(bar.get_x() + bar.get_width() / 2, bottoms[i] + value / 2, str(value), ha="center", va="center", fontsize=9)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    ax.set_ylabel("Failed trials")
    ax.set_xticks([0, 1])
    ax.set_xticklabels([_harness_label(harness) for harness in harnesses])
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _write_repair_outcomes_pdf(path: Path, rows: list[dict]) -> None:
    plt = _plt()
    run_rows = [row for row in rows if row["run"] != "total"]
    labels = [row["run"].replace("_", " ") for row in run_rows]
    initial = [row["initial_pass"] for row in run_rows]
    repaired = [row["repaired_pass"] for row in run_rows]
    failed = [row["failed"] for row in run_rows]

    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    x_positions = list(range(len(run_rows)))
    ax.bar(x_positions, initial, label="Initial pass", color="#4C78A8")
    ax.bar(x_positions, repaired, bottom=initial, label="Fixed by repair", color="#F58518")
    ax.bar(x_positions, failed, bottom=[a + b for a, b in zip(initial, repaired)], label="Failed", color="#BAB0AC")
    ax.set_ylim(0, 15)
    ax.set_ylabel("Tasks")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _write_notes(path: Path, harness_summary: list[dict], style_summary: list[dict], failure_summary: list[dict]) -> None:
    by_harness = {row["harness"]: row for row in harness_summary}
    baseline = by_harness["baseline"]
    repair = by_harness["sim_repair"]
    improvement = repair["mean_pass_rate"] - baseline["mean_pass_rate"]
    lines = [
        f"Baseline mean pass rate: {baseline['mean_pass_rate']:.3f}",
        f"Repair mean pass rate: {repair['mean_pass_rate']:.3f}",
        f"Absolute improvement: {improvement:.3f}",
        f"Baseline total passed: {baseline['total_passed']}/{baseline['total_trials']}",
        f"Repair total passed: {repair['total_passed']}/{repair['total_trials']}",
        "",
        "By style:",
    ]
    for row in style_summary:
        lines.append(f"{row['harness']} {row['style']}: {row['passed']}/{row['trials']} ({row['pass_rate']:.3f})")
    lines.append("")
    lines.append("Failures:")
    for row in failure_summary:
        lines.append(f"{row['harness']} {row['reason']}: {row['count']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _sample_sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _harness_label(harness: str) -> str:
    return {"baseline": "Single-shot", "sim_repair": "Simulation repair"}.get(harness, harness.replace("_", "\\_"))


def _reason_label(reason: str) -> str:
    return reason.replace("_", "\\_")


def _short_task(task_id: str) -> str:
    prefix = "cvdp\\_copilot\\_"
    escaped = task_id.replace("_", "\\_")
    if escaped.startswith(prefix):
        return escaped[len(prefix) :]
    return escaped


def _plt():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cvdp-ap")
    import matplotlib.pyplot as plt

    return plt


if __name__ == "__main__":
    main()
