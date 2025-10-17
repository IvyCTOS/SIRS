"""
Rule Engine Module for Credit Behavior Insight Engine
Evaluates normalized credit data against predefined behavioral rules
"""

import json
from asteval import Interpreter
from typing import Dict, List, Tuple, Any


class RuleEngine:
    """
    Core rule engine for evaluating credit behavior rules
    """
    
    def __init__(self, rules_file: str, file_format: str = 'json'):
        """
        Initialize the rule engine
        
        Args:
            rules_file: Path to rules file
            file_format: Format of rules file ('json' or 'yaml')
        """
        self.rules_file = rules_file
        self.file_format = file_format
        self.rules = []
        self.evaluator = Interpreter()
        
        # Load rules on initialization
        self.load_rules()
    
    def load_rules(self) -> List[Dict]:
        """
        Load rules from JSON or YAML file
        
        Returns:
            List of rule dictionaries
        """
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as file:
                if self.file_format == 'json':
                    data = json.load(file)
                
                self.rules = data.get('rules', [])
                print(f"✓ Loaded {len(self.rules)} rules from {self.rules_file}")
                return self.rules
                
        except FileNotFoundError:
            print(f"✗ Error: Rules file not found: {self.rules_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON format in rules file: {e}")
            raise
        except Exception as e:
            print(f"✗ Error loading rules: {e}")
            raise
    
    def evaluate_rule(self, data: Dict, rule: Dict) -> bool:
        """
        Evaluate a single rule's condition against the data
        
        Args:
            data: Dictionary containing the data to evaluate
            rule: Rule dictionary containing the condition
            
        Returns:
            True if condition is met, False otherwise
        """
        condition = rule.get('condition', '')
        
        if not condition:
            return False
        
        try:
            # Evaluate the condition using asteval
            # Pass data as local variables for the condition
            result = self.evaluator(condition, data)
            return bool(result)
            
        except Exception as e:
            print(f"  Warning: Error evaluating condition '{condition}': {e}")
            return False
    
    def generate_insight(self, data: Dict, rule: Dict) -> Tuple[str, str, str]:
        """
        Generate insight message and recommendation from matched rule
        
        Args:
            data: Dictionary containing the data values
            rule: Matched rule dictionary
            
        Returns:
            Tuple of (label, insight_message, recommendation)
        """
        try:
            label = rule.get('label', '')
            compound_type = rule.get('compound_type', '')
            template = rule.get('template', '')
            recommendation = rule.get('recommendation', '')
            
            # Render template with data using string formatting
            # Handle missing keys gracefully
            insight_message = self._render_template(template, data)
            
            return label, compound_type, insight_message, recommendation
            
        except Exception as e:
            print(f"  Warning: Error generating insight: {e}")
            return '', '', '', ''
    
    def _render_template(self, template: str, data: Dict) -> str:
        """
        Render template string with data, handling missing keys
        
        Args:
            template: Template string with {placeholders}
            data: Dictionary with values
            
        Returns:
            Rendered string
        """
        try:
            # Use format_map with a defaultdict-like behavior
            return template.format(**data)
        except KeyError as e:
            # If a key is missing, return template with available data filled in
            print(f"  Warning: Missing key in template: {e}")
            # Try to fill in what we can
            import re
            result = template
            for key, value in data.items():
                pattern = '{' + key + '}'
                if pattern in result:
                    result = result.replace(pattern, str(value))
            return result
    
    def process_data_with_rules(self, data: Dict) -> Tuple[str, str, str, str]:
        """
        Process a single data record against all rules
        Returns the first matching rule's insight
        
        Args:
            data: Dictionary containing data to evaluate
            
        Returns:
            Tuple of (label, compound_type, insight, recommendation)
            Returns (None, None, None, None) if no rules match
        """
        for rule in self.rules:
            if self.evaluate_rule(data, rule):
                return self.generate_insight(data, rule)
        
        return None, None, None, None
    
    def process_all_records(self, records: List[Dict]) -> List[Dict]:
        """
        Process multiple data records against all rules
        
        Args:
            records: List of data dictionaries to evaluate
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        for idx, record in enumerate(records):
            label, compound_type, insight, recommendation = self.process_data_with_rules(record)
            
            if label:  # If a rule matched
                insights.append({
                    'record_index': idx,
                    'label': label,
                    'compound_type': compound_type,
                    'insight': insight,
                    'recommendation': recommendation,
                    'source_data': record
                })
        
        return insights
    
    def generate_report(self, insights: List[Dict]) -> Dict:
        """
        Generate a structured report from insights
        
        Args:
            insights: List of insight dictionaries
            
        Returns:
            Report dictionary with summary and details
        """
        # Group insights by label
        grouped = {}
        for insight in insights:
            label = insight['label']
            if label not in grouped:
                grouped[label] = []
            grouped[label].append(insight)
        
        # Count by severity/label
        label_counts = {label: len(items) for label, items in grouped.items()}
        
        report = {
            'total_insights': len(insights),
            'insights_by_label': grouped,
            'label_counts': label_counts,
            'all_insights': insights
        }
        
        return report


def save_report(report: Dict, output_file: str):
    """
    Save report to JSON file
    
    Args:
        report: Report dictionary
        output_file: Output file path
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f"✓ Report saved to: {output_file}")
    except Exception as e:
        print(f"✗ Error saving report: {e}")


# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("RULE ENGINE MODULE - DEMO")
    print("="*60)
    
    # Initialize rule engine
    print("\n[1] Loading rules...")
    engine = RuleEngine('rules/rules.json')
    
    # Example 1: Single record evaluation
    print("\n[2] Testing single record evaluation...")
    print("-"*60)
    
    sample_data = {
        'creditutilizationratio': 85,
        'loantype': 'Credit Card',
        'lendertype': 'Bank ABC'
    }
    
    print(f"Input data: {sample_data}")
    label, compound_type, insight, recommendation = engine.process_data_with_rules(sample_data)
    
    if label:
        print(f"\n✓ Rule matched!")
        print(f"Label: {label}")
        print(f"Type: {compound_type}")
        print(f"Insight: {insight}")
        print(f"Recommendation: {recommendation}")
    else:
        print("\n✗ No rules matched")
    
    # Example 2: Multiple records evaluation
    print("\n" + "="*60)
    print("[3] Testing multiple records evaluation...")
    print("-"*60)
    
    sample_records = [
        {
            'creditutilizationratio': 95,
            'loantype': 'Credit Card',
            'lendertype': 'CIMB Bank'
        },
        {
            'numberofloans': 7,
            'loantype': 'Various'
        },
        {
            'mon_arrears': 4,
            'inst_arrears': 4,
            'loantype': 'Personal Loan',
            'lendertype': 'Alliance Bank'
        },
        {
            'balance': 7000,
            'limit': 7000,
            'loan_type': 'Credit Card'
        },
        {
            'numapplicationslast12months': 5,
            'loantype': 'Various'
        }
    ]
    
    print(f"Processing {len(sample_records)} records...\n")
    insights = engine.process_all_records(sample_records)
    
    print(f"✓ Found {len(insights)} insights")
    
    # Display insights
    for idx, insight in enumerate(insights, 1):
        print(f"\n--- Insight {idx} ---")
        print(f"Label: {insight['label']}")
        print(f"Type: {insight['compound_type']}")
        print(f"Message: {insight['insight']}")
        print(f"Action: {insight['recommendation'][:100]}...")
    
    # Generate and save report
    print("\n" + "="*60)
    print("[4] Generating report...")
    print("-"*60)
    
    report = engine.generate_report(insights)
    
    print(f"\nReport Summary:")
    print(f"  Total Insights: {report['total_insights']}")
    print(f"  Unique Labels: {len(report['label_counts'])}")
    print(f"\nInsights by Label:")
    for label, count in report['label_counts'].items():
        print(f"  {label}: {count}")
    
    # Save report
    save_report(report, 'output/insights_report.json')
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)