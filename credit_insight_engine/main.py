"""
Main Entry Point - XML VERSION
Processes CTOS XML reports and generates credit behavior insights
"""

import sys
import json
from pathlib import Path
from typing import Any, List

from engine.output_aggregator import ConsoleOutputAggregator
from engine.credit_rule_engine import RuleEngine
from engine.data_input import extract_data_from_xml, normalize_data

def load_json(path: Path) -> Any:
    """Load JSON file"""
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def ensure_list(records):
    """Ensure records is a list"""
    if isinstance(records, list):
        return records
    if isinstance(records, dict) and "records" in records:
        return records["records"]
    return [records]

def severity_from_label(label: str) -> str:
    """Infer severity from label text"""
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
    """Main execution function"""
    base_dir = Path(__file__).resolve().parent
    
    # Create required directories
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "output").mkdir(exist_ok=True)

    # Default XML location (assuming sample report is in data folder)
    default_xml = base_dir / "data" / "sample_2.xml"
    input_path = Path(argv[1]).resolve() if len(argv) > 1 else default_xml

    # Validate input file
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        print(f"\nUsage: python main.py <path_to_xml_file>")
        sys.exit(1)
    
    if input_path.suffix.lower() != '.xml':
        print(f"⚠️  Warning: Expected .xml file, got {input_path.suffix}")
        print(f"Attempting to process anyway...")

    # Load rules
    rules_file = base_dir / "rules" / "rules.json"
    if not rules_file.exists():
        print(f"❌ Error: Rules file not found: {rules_file}")
        sys.exit(1)
    
    print("="*70)
    print("CTOS XML Credit Report Analyzer".center(70))
    print("="*70)
    print(f"\n📄 Processing XML report: {input_path.name}")
    print(f"📋 Using rules from: {rules_file.name}\n")
    
    try:
        # Extract and normalize data from XML
        print("🔍 Extracting data from XML...")
        extracted_data = extract_data_from_xml(str(input_path))
        
        if not extracted_data:
            print("❌ Error: Failed to extract data from XML")
            sys.exit(1)
        
        # Display extraction summary
        print(f"\n✅ Extraction complete:")
        print(f"   • Name: {extracted_data.get('name', 'N/A')}")
        print(f"   • IC: {extracted_data.get('ic_number', 'N/A')}")
        print(f"   • CTOS Score: {extracted_data.get('ctos_score', 'N/A')}")
        print(f"   • Loans: {extracted_data.get('numberofloans', 0)}")
        print(f"   • Total Outstanding: RM {extracted_data.get('total_outstanding', 0):,.2f}")
        
        print(f"\n🔄 Normalizing data...")
        normalized_data = normalize_data(extracted_data)
        
        records = normalized_data.get('records', [])
        personal_info = normalized_data.get('personal_info', {})
        
        print(f"✅ Normalized {len(records)} records")
        print(f"   • Loan records: {len(records) - 1}")
        print(f"   • Aggregate record: 1")
        
        # Initialize rule engine
        print(f"\n⚙️  Initializing rule engine...")
        engine = RuleEngine(str(rules_file))
        print(f"✅ Loaded {len(engine.rules)} rules")
        
        # Process normalized data structure
        print(f"\n🎯 Evaluating rules against records...")
        matches = engine.process_data(normalized_data)
        
        print(f"\n✅ Found {len(matches)} insights")
        
        # Add matches to aggregator
        aggregator = ConsoleOutputAggregator()
        for match in matches:
            aggregator.add_insight(match)
        
        # Display results
        aggregator.print_report()
        
        # Optionally save to JSON
        output_file = base_dir / "output" / f"report_{input_path.stem}.json"
        json_report = aggregator.generate_json_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON report saved to: {output_file}\n")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing report: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)