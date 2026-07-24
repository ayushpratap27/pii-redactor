import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from redactor import PIIRedactor
from docx_processor import DocxProcessor
from evaluator import BenchmarkEvaluator

def main():
    parser = argparse.ArgumentParser(description="PII Redaction & Evaluation Tool")
    parser.add_argument("input_file", help="Path to input DOCX file")
    parser.add_argument("output_file", help="Path to output redacted DOCX file")
    parser.add_argument("--annotation", "-a", help="Path to ground truth JSON annotations file (default: data/annotations.json)")
    parser.add_argument("--evaluate", "-e", action="store_true", help="Run benchmark evaluation after redaction")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"\n[!] Error: Input file not found at '{args.input_file}'")
        sys.exit(1)

    print("==================================================")
    print("🔒 PII Redaction Engine")
    print(f"Input Document:  {args.input_file}")
    print(f"Output Document: {args.output_file}")
    print("==================================================")

    redactor = PIIRedactor(seed=42)
    processor = DocxProcessor(redactor=redactor)

    try:
        stats = processor.process_document(args.input_file, args.output_file)
    except Exception as e:
        print(f"\n[!] Error processing document: {e}")
        sys.exit(1)

    print("\n📊 Redaction Summary:")
    print(f"  Paragraphs Processed: {stats['total_paragraphs']}")
    print(f"  Tables Processed:     {stats['total_tables']}")
    print(f"  Total Spans Redacted: {stats['total_redacted']}")
    print(f"  Unique Entity Mapping:{stats['mapping_count']}")

    print("\nBreakdown by Category:")
    for cat, count in stats['category_counts'].items():
        print(f"  - {cat:15s}: {count}")

    print(f"\n✓ Successfully generated redacted file: {args.output_file}")

    if args.evaluate:
        annotation_path = args.annotation or os.path.join("data", "annotations.json")
        if not os.path.exists(annotation_path):
            print(f"\n[!] Annotation file not found at: {annotation_path}")
            return

        evaluator = BenchmarkEvaluator(redactor=redactor)
        metrics = evaluator.evaluate(annotation_path)

        overall = metrics["overall"]
        print("\n📈 Benchmark Evaluation Metrics:")
        print(f"  True Positives (TP):  {overall['tp']}")
        print(f"  False Positives (FP): {overall['fp']}")
        print(f"  False Negatives (FN): {overall['fn']}")
        print(f"  Precision:            {overall['precision']:.2%}")
        print(f"  Recall:               {overall['recall']:.2%}")
        print(f"  F1-Score:             {overall['f1_score']:.2%}")
        print(f"  Accuracy:             {overall['accuracy']:.2%}")

if __name__ == "__main__":
    main()
