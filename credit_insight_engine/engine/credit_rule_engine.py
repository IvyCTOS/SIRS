"""
Rule Engine Module for Credit Behavior Insight Engine
Evaluates normalized credit data against predefined behavioral rules
"""

from pathlib import Path
from typing import Dict, List, Any
import json
import logging
from engine.condition_parser import ConditionParser, ParserError
from engine.template_renderer import TemplateRenderer


class RuleEngine:
    """
    Loads rule definitions from a JSON file and evaluates them against input records.
    Uses ConditionParser to safely evaluate conditions and TemplateRenderer to render messages.
    """

    # Add a small alias map for template variables -> normalized record keys
    FIELD_ALIASES = {
        'Facility': 'loantype',
        'Lender_Type': 'lendertype',
        'Loan_Type': 'loan_type',
        'Balance': 'balance',
        'Limit': 'limit',
        'CreditUtilizationRatio': 'creditutilizationratio',
        'creditutilizationratio': 'creditutilizationratio',
        'numberofloans': 'numberofloans',
        'numapplicationslast12months': 'numapplicationslast12months',
        'payment_conduct_code': 'mon_arrears',
        'paymentConductCode': 'mon_arrears'
    }

    def __init__(self, rules_file: str):
        self.rules_file = Path(rules_file)
        self.logger = logging.getLogger(__name__)
        self.parser = ConditionParser()
        self.renderer = TemplateRenderer()
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load and validate rules from JSON file"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('rules', [])
        except Exception as e:
            self.logger.error(f"Failed to load rules: {e}")
            raise

    def _apply_template_aliases(self, template: str) -> str:
        """Replace known template variable names (from rules) with normalized keys for rendering."""
        if not template:
            return template
        # replace both {{Var}} and {Var} occurrences
        for alias, real_key in self.FIELD_ALIASES.items():
            # Jinja style
            template = template.replace(f"{{{{{alias}}}}}", f"{{{{ {real_key} }}}}")
            template = template.replace(f"{{{{ {alias} }}}}", f"{{{{ {real_key} }}}}")
            # Python-style single braces
            template = template.replace(f"{{{alias}}}", f"{{{real_key}}}")
            template = template.replace(f"{{ {alias} }}", f"{{ {real_key} }}")
        return template

    def _build_render_context(self, record: Dict[str, Any], personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build rendering context, merging record + personal_info and adding formatted variants.
        Includes keys for both normalized names and some formatted display forms.
        """
        ctx = {**personal_info, **record}
        # Add formatted versions used in templates
        try:
            if 'creditutilizationratio' in ctx:
                ctx['creditutilizationratio'] = float(ctx['creditutilizationratio'])
            if 'balance' in ctx:
                ctx['balance'] = float(ctx.get('balance', 0.0))
            if 'limit' in ctx:
                ctx['limit'] = float(ctx.get('limit', 0.0))
            # Friendly aliases used by some templates
            ctx['Facility'] = ctx.get('loantype', '')
            ctx['Lender_Type'] = ctx.get('lendertype', '')
            # Also provide basic formatted strings
            ctx['balance_display'] = f"RM {ctx.get('balance', 0):,.2f}" if ctx.get('balance') is not None else ""
            ctx['limit_display'] = f"RM {ctx.get('limit', 0):,.2f}" if ctx.get('limit') is not None else ""
            ctx['creditutilizationratio_display'] = f"{ctx.get('creditutilizationratio', 0):.1f}"
        except Exception:
            pass
        return ctx

    def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process normalized data structure containing records and personal info"""
        matches = []
        seen_insights = set()  # Track unique insights
        
        # Extract records array and personal info
        records = data.get('records', [])
        personal_info = data.get('personal_info', {})
        
        self.logger.info(f"Processing {len(records)} records")
        
        # Process each record
        for record in records:
            # Merge personal info into record for template rendering
            record_with_info = {**record, **personal_info}
            
            # Build rendering context once per record
            render_ctx = self._build_render_context(record, personal_info)
            
            # Check each rule against the record
            for rule in self.rules:
                try:
                    condition = rule.get('condition', '')
                    if not condition:
                        continue
                        
                    if self.parser.evaluate(condition, record):
                        # Rule matched - prepare insight
                        template = rule.get('template', '') or ''
                        # Apply alias substitutions so templates refer to normalized keys
                        template_for_render = self._apply_template_aliases(template)
                        # Render with Jinja via TemplateRenderer
                        message = self.renderer.render_template(template_for_render, render_ctx) if template_for_render else ''
                        
                        # Create insight key for deduplication
                        insight_key = f"{rule.get('label')}:{message}"
                        if insight_key in seen_insights:
                            continue
                            
                        seen_insights.add(insight_key)
                        
                        insight = {
                            'label': rule.get('label', ''),
                            'type': rule.get('compound_type', ''),
                            'message': message,
                            'recommendation': rule.get('recommendation', ''),
                            'severity': 'high' if rule.get('priority', '').lower() in ('high', 'critical') or '🔴' in rule.get('label', '') else 'medium',
                            'data': record  # Include raw data if needed downstream
                        }
                        matches.append(insight)
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.get('label')}: {e}")
                    continue
                    
        self.logger.info(f"Found {len(matches)} unique matches")
        return matches


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