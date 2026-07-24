import json
from typing import Dict, Any
from redactor import PIIRedactor

class BenchmarkEvaluator:
    """Benchmark evaluation module calculating Precision, Recall, Accuracy, and F1-Score."""

    def __init__(self, redactor: PIIRedactor):
        self.redactor = redactor

    def evaluate(self, annotation_path: str) -> Dict[str, Any]:
        with open(annotation_path, "r", encoding="utf-8") as f:
            samples = json.load(f)

        category_stats: Dict[str, Dict[str, int]] = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for sample in samples:
            text = sample.get("text", "")
            gt_annotations = sample.get("annotations", [])
            predicted = self.redactor.detect_entities(text)

            gt_matched = [False] * len(gt_annotations)
            pred_matched = [False] * len(predicted)

            for p_idx, pred in enumerate(predicted):
                for g_idx, gt in enumerate(gt_annotations):
                    if gt_matched[g_idx]:
                        continue
                    is_offset_match = (pred["start"] == gt["start"] and pred["end"] == gt["end"])
                    is_text_match = (pred["text"].strip().lower() == gt["text"].strip().lower())
                    is_type_match = (pred["type"] == gt["entity_type"])

                    if (is_offset_match or is_text_match) and is_type_match:
                        gt_matched[g_idx] = True
                        pred_matched[p_idx] = True
                        cat = pred["type"]
                        if cat not in category_stats:
                            category_stats[cat] = {"tp": 0, "fp": 0, "fn": 0}
                        category_stats[cat]["tp"] += 1
                        total_tp += 1
                        break

            for p_idx, pred in enumerate(predicted):
                if not pred_matched[p_idx]:
                    cat = pred["type"]
                    if cat not in category_stats:
                        category_stats[cat] = {"tp": 0, "fp": 0, "fn": 0}
                    category_stats[cat]["fp"] += 1
                    total_fp += 1

            for g_idx, gt in enumerate(gt_annotations):
                if not gt_matched[g_idx]:
                    cat = gt["entity_type"]
                    if cat not in category_stats:
                        category_stats[cat] = {"tp": 0, "fp": 0, "fn": 0}
                    category_stats[cat]["fn"] += 1
                    total_fn += 1

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
        accuracy = total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 1.0

        by_cat = {}
        for cat, s in category_stats.items():
            tp, fp, fn = s["tp"], s["fp"], s["fn"]
            c_prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            c_rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            c_f1 = 2 * (c_prec * c_rec) / (c_prec + c_rec) if (c_prec + c_rec) > 0 else 1.0
            c_acc = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 1.0
            by_cat[cat] = {
                "tp": tp, "fp": fp, "fn": fn,
                "precision": round(c_prec, 4),
                "recall": round(c_rec, 4),
                "f1_score": round(c_f1, 4),
                "accuracy": round(c_acc, 4)
            }

        return {
            "overall": {
                "tp": total_tp, "fp": total_fp, "fn": total_fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4)
            },
            "by_category": by_cat
        }
