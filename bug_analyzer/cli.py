import argparse
import json
import sys
from pathlib import Path

from .analyzer import BugReportAnalyzer

ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


def render(a) -> str:
    lines = [
        f"{ICON[a.severity.value]} {a.severity.value.upper()}  |  {a.category.value}  |  engine={a.engine}  |  confidence={a.confidence}",
        f"Summary: {a.summary}",
        f"Why: {a.severity_reason}",
        "\nLikely root causes:",
        *[f"  - {c}" for c in a.likely_root_causes],
        "\nTroubleshooting steps:",
        *[f"  {i}. {s}" for i, s in enumerate(a.troubleshooting_steps, 1)],
        f"\nLabels: {', '.join(a.suggested_labels)}",
    ]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="AI Bug Report Analyzer")
    p.add_argument("text", nargs="?", help="Bug report text (or use --file / stdin)")
    p.add_argument("-f", "--file", help="Path to a text file, or a .json file with a list of reports")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    p.add_argument("--no-llm", action="store_true", help="Force rule-based engine")
    args = p.parse_args(argv)

    analyzer = BugReportAnalyzer(use_llm=not args.no_llm)

    if args.file:
        path = Path(args.file)
        content = path.read_text(encoding="utf-8")
        reports = json.loads(content) if path.suffix == ".json" else [content]
    elif args.text:
        reports = [args.text]
    elif not sys.stdin.isatty():
        reports = [sys.stdin.read()]
    else:
        p.error("Provide report text, --file, or pipe via stdin")

    results = analyzer.analyze_many(reports)
    if args.json:
        print(json.dumps([r.model_dump(mode="json") for r in results], indent=2))
    else:
        print(("\n" + "=" * 70 + "\n").join(render(r) for r in results))


if __name__ == "__main__":
    main()
