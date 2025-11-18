import argparse
import csv
from typing import List, Tuple, Optional

from task_extraction import extract_task


def read_csv(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def token_set(s: str) -> set:
    return {t.lower() for t in s.replace("/", " ").replace("-", " ").split() if t.strip()}


def f1_from_sets(pred: set, gold: set) -> float:
    if not pred and not gold:
        return 1.0
    if not pred or not gold:
        return 0.0
    inter = len(pred & gold)
    prec = inter / len(pred) if pred else 0.0
    rec = inter / len(gold) if gold else 0.0
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def evaluate(rows: List[dict], text_col: str, label_col: Optional[str], gold_task_col: Optional[str]) -> Tuple[dict, List[dict]]:
    tp = fp = fn = tn = 0
    task_f1_sum = 0.0
    task_f1_count = 0
    outputs: List[dict] = []

    for row in rows:
        text = row.get(text_col, "") or ""
        result = extract_task(text)

        pred = 1 if result["is_task"] else 0
        gold = None
        if label_col is not None and label_col in row and row[label_col] != "":
            try:
                gold = int(float(row[label_col]))
            except Exception:
                gold = None

        if gold is not None:
            if pred == 1 and gold == 1:
                tp += 1
            elif pred == 1 and gold == 0:
                fp += 1
            elif pred == 0 and gold == 1:
                fn += 1
            else:
                tn += 1

        # Task text overlap if gold task provided
        if gold_task_col and gold_task_col in row:
            gold_task = (row.get(gold_task_col) or "").strip()
            if gold_task:
                pf1 = f1_from_sets(token_set(result.get("task", "")), token_set(gold_task))
                task_f1_sum += pf1
                task_f1_count += 1

        out_row = dict(row)
        out_row.update({
            "pred_is_task": result["is_task"],
            "pred_confidence": result["confidence"],
            "pred_task": result["task"],
        })
        outputs.append(out_row)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    avg_task_f1 = task_f1_sum / task_f1_count if task_f1_count > 0 else None

    metrics = {
        "count": len(rows),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "avg_task_f1": avg_task_f1,
        "task_overlap_evaluated": task_f1_count,
    }
    return metrics, outputs


def main():
    ap = argparse.ArgumentParser(description="Evaluate task extraction on a CSV dataset")
    ap.add_argument("--input", required=True, help="Path to input CSV with at least a text column")
    ap.add_argument("--text-col", default="text", help="Column name for the input message text")
    ap.add_argument("--label-col", default="label", help="Binary label column (0/1) for task presence; set to '' to disable")
    ap.add_argument("--gold-task-col", default="gold_task", help="Reference task text column; set to '' to disable")
    ap.add_argument("--output", default="", help="Optional path to write predictions CSV")
    args = ap.parse_args()

    label_col = args.label_col if args.label_col else None
    gold_task_col = args.gold_task_col if args.gold_task_col else None

    rows = read_csv(args.input)
    metrics, outputs = evaluate(rows, args.text_col, label_col, gold_task_col)

    print("Examples:")
    for i, r in enumerate(outputs[:5]):
        print(f"- text={r.get(args.text_col, '')!r} -> is_task={r['pred_is_task']} conf={r['pred_confidence']:.2f} task={r['pred_task']!r}")
    print()

    print("Detection metrics:")
    print(f"count={metrics['count']} tp={metrics['tp']} fp={metrics['fp']} fn={metrics['fn']} tn={metrics['tn']}")
    print(f"precision={metrics['precision']:.3f} recall={metrics['recall']:.3f} f1={metrics['f1']:.3f}")
    if metrics["avg_task_f1"] is not None:
        print(f"avg_task_f1={metrics['avg_task_f1']:.3f} (over {metrics['task_overlap_evaluated']} examples with gold_task)")

    if args.output:
        fieldnames = list(outputs[0].keys()) if outputs else []
        with open(args.output, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(outputs)
        print(f"Predictions written to {args.output}")


if __name__ == "__main__":
    main()
