import sys
import json
from pathlib import Path
from typing import Any, List

from output.output_aggregator import ConsoleOutputAggregator
from engine.credit_rule_engine import RuleEngine
from engine.data_input import extract_data_from_pdf, normalize_data

def load_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def ensure_list(records):
    if isinstance(records, list):
        return records
    if isinstance(records, dict) and "records" in records:
        return records["records"]
    return [records]

def severity_from_label(label: str) -> str:
    if not label:
        return "medium"
    if "🔴" in label or "High" in label or "high" in label.lower():
        return "high"
    if "🟠" in label or "Missed" in label or "missed" in label.lower():
        return "high"
    if "🟡" in label:
        return "medium"
    if "🟣" in label or "⚪" in label:
        return "low"
    return "medium"

def main(argv: List[str]):
    base_dir = Path(__file__).resolve().parent
    
    # Create required directories
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "output").mkdir(exist_ok=True)

    # Default PDF location (assuming sample report is in data folder)
    default_pdf = base_dir / "data" / "Blanked-New-Sample-Score-Report.pdf"
    input_path = Path(argv[1]).resolve() if len(argv) > 1 else default_pdf

    # Load rules
    rules_file = base_dir / "rules" / "rules.json"
    
    print(f"Processing PDF report: {input_path}")
    
    try:
        # Extract and normalize data
        extracted_data = extract_data_from_pdf(str(input_path))
        normalized_data = normalize_data(extracted_data)
        
        print("\nProcessing normalized records...")
        print(f"Found {len(normalized_data.get('records', []))} records to process")
        
        # Initialize rule engine
        engine = RuleEngine(str(rules_file))
        
        # Process normalized data structure
        matches = engine.process_data(normalized_data)
        
        print(f"\nFound {len(matches)} matching rules")
        
        # Add matches to aggregator
        aggregator = ConsoleOutputAggregator()
        for match in matches:
            aggregator.add_insight(match)
            
        # Display results
        aggregator.print_report()
        
    except Exception as e:
        print(f"Error processing report: {str(e)}")
        raise

if __name__ == "__main__":
    main(sys.argv)