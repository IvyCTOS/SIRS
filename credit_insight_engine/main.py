import sys
import json
from pathlib import Path
from typing import Any, Dict, List

from output.output_aggregator import ConsoleOutputAggregator
from engine.credit_rule_engine import RuleEngine

# Pipeline orchestrator for the Credit Behavior Insight Engine
# Assumes modules implemented under engine/ as:
# - engine.data_input: extract_data_from_pdf(pdf_path), normalize_data(extracted)
# - engine.credit_rule_engine: RuleEngine(rules_file) with .process_data(record) -> List[(label, message, recommendation)]
# - engine.template_renderer: TemplateRenderer(templates_file) (optional)
# - output.output_aggregator: ConsoleOutputAggregator() with add_insight() and print_report()

def load_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def ensure_list(records):
    if isinstance(records, list):
        return records
    # common schema: {"records": [...]} or single record dict
    if isinstance(records, dict) and "records" in records:
        return records["records"]
    return [records]

def severity_from_label(label: str) -> str:
    if not label:
        return "medium"
    if "🔴" in label or "High" in label or "high" in label.lower():
        return "high"
    if "🟠" in label or "Missed" in label or "medium" in label.lower():
        return "high"
    if "🟡" in label:
        return "medium"
    if "🟣" in label or "⚪" in label:
        return "low"
    return "medium"

def main(argv: List[str]):
    # base dir = directory where this main.py lives
    base_dir = Path(__file__).resolve().parent

    # Ensure runtime folders exist
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "output").mkdir(exist_ok=True)

    # Resolve input / rules / templates paths relative to base_dir if not absolute
    input_path = Path(argv[1]).resolve() if len(argv) > 1 else None
    default_rules = base_dir.parent.joinpath("rules", "rules.json")  # project-level rules folder
    default_templates = base_dir.parent.joinpath("rules", "templates.json")

    rules_file = Path(argv[2]).resolve() if len(argv) > 2 else default_rules
    templates_file = Path(argv[3]).resolve() if len(argv) > 3 else default_templates

    # Optional modules
    data_records = []
    try:
        if input_path and input_path.exists():
            if input_path.suffix.lower() == ".pdf":
                try:
                    from engine.data_input import extract_data_from_pdf, normalize_data
                    extracted = extract_data_from_pdf(str(input_path))
                    normalized = normalize_data(extracted)
                    data_records = ensure_list(normalized)
                except Exception as e:
                    print(f"Error extracting PDF data: {e}")
                    return
            elif input_path.suffix.lower() in (".json", ".txt"):
                data = load_json(input_path)
                data_records = ensure_list(data)
            else:
                print("Unsupported input file type. Provide .pdf or .json")
                return
        else:
            # No input provided — use a small example record for demo
            data_records = [{
                "creditutilizationratio": 85,
                "loantype": "Credit Card",
                "lendertype": "Bank ABC",
                "balance": 5000,
                "limit": 6000
            }]
    except Exception as e:
        print(f"Error loading input: {e}")
        return

    # Initialize engine and aggregator
    try:
        engine = RuleEngine(str(rules_file))
    except Exception as e:
        print(f"Failed to load rules from {rules_file}: {e}")
        return

    aggregator = ConsoleOutputAggregator()

    # Process each record
    for idx, record in enumerate(data_records, start=1):
        try:
            matches = engine.process_data(record)  # expected: list of (label, message, recommendation)
            if not matches:
                continue
            for match in matches:
                # match may be tuple (label, message, recommendation) or dict
                if isinstance(match, (list, tuple)) and len(match) >= 2:
                    label = match[0] or ""
                    message = match[1] or ""
                    recommendation = match[2] if len(match) > 2 else ""
                elif isinstance(match, dict):
                    label = match.get("label", "")
                    message = match.get("message", match.get("template_message", ""))
                    recommendation = match.get("recommendation", "")
                else:
                    continue

                insight = {
                    "label": label,
                    "type": record.get("compound_type", ""),  # try to attach compound_type if present
                    "message": message,
                    "recommendation": recommendation,
                    "severity": severity_from_label(label)
                }
                aggregator.add_insight(insight)
        except Exception as e:
            print(f"Error processing record #{idx}: {e}")

    # Final output to console
    aggregator.print_report()


if __name__ == "__main__":
    main(sys.argv)