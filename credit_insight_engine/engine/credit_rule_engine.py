"""
FIXED Rule Engine - Correctly applies rules based on record context
Key fixes:
1. Payment conduct rules apply to ALL loan records, not just revolving
2. Trade reference and legal rules apply to aggregate records
3. Utilization rules ONLY apply to revolving credit
"""

from pathlib import Path
from typing import Dict, List, Any
import json
import logging

class RuleEngine:
    """
    Loads rule definitions from a JSON file and evaluates them against input records.
    """

    FIELD_ALIASES = {
        'Facility': 'loantype',
        'Lender_Type': 'lendertype',
        'creditutilizationratio': 'creditutilizationratio',
    }

    REVOLVING_FACILITIES = ['CRDTCARD', 'OVRDRAFT']
    INSTALLMENT_FACILITIES = ['HSLNFNCE', 'PCPASCAR', 'OTLNFNCE', 'MICROEFN']

    def __init__(self, rules_file: str):
        self.rules_file = Path(rules_file)
        self.logger = logging.getLogger(__name__)
        
        # Import here to avoid circular dependency
        from engine.condition_parser import ConditionParser
        from engine.template_renderer import TemplateRenderer
        
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

    def _detect_record_type(self, record: Dict[str, Any]) -> str:
        """
        Detect if record is a loan-level or aggregate/portfolio-level record
        """
        # Aggregate indicators are most reliable
        aggregate_indicators = [
            'numberofloans', 'numapplicationslast12months', 'distinct_account_types',
            'trade_ref_amount_overdue', 'legal_cases_settled', 'legal_cases_active'
        ]
        
        if any(indicator in record for indicator in aggregate_indicators):
            return 'aggregate'
        
        # If has facility_type, it's likely a loan record
        if 'facility_type' in record or 'loantype' in record:
            return 'loan'
        
        return 'loan'

    def _is_revolving_credit(self, record: Dict[str, Any]) -> bool:
        """Check if the loan record is revolving credit"""
        facility_type = (
            record.get('facility_type', '') or 
            record.get('loan_type', '') or 
            record.get('loantype', '')
        )
        
        return facility_type in self.REVOLVING_FACILITIES

    def _should_apply_rule(self, rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """
        CRITICAL FIX: Determine if a rule should be applied to a given record
        """
        label = rule.get('label', '')
        compound_type = rule.get('compound_type', '')
        field_mapping = rule.get('field_mapping', '').lower()
        
        record_type = self._detect_record_type(record)
        is_loan_record = (record_type == 'loan')
        is_aggregate = (record_type == 'aggregate')
        
        # RULE 1: Utilization rules ONLY for revolving credit loans
        if 'Utilization' in label or 'Utilization' in compound_type:
            if not is_loan_record:
                return False
            if not self._is_revolving_credit(record):
                return False
            return True
        
        # RULE 2: Payment conduct rules for ALL LOAN RECORDS (not just revolving)
        if ('Missed Payments' in label or 
            'Payment Conduct' in compound_type or 
            'Delinquency' in compound_type or
            'payment_conduct_code' in rule.get('condition', '')):
            return is_loan_record
        
        # RULE 3: Portfolio-level rules (aggregate only)
        portfolio_rules = [
            '🟡 Frequent Applications',
            '🟡 Pending Applications', 
            '🟡 High Decline Rate',
            '🟣 Thin Credit File',
            '⚪ Short Credit History',
            '⚪ Recent Enquiries',
            '🔵 Lender Concentration',
            '🔵 Secured Debt Heavy',
            '🟢 Low Application Rate'
        ]
        
        if any(portfolio_label in label for portfolio_label in portfolio_rules):
            return is_aggregate
        
        # RULE 4: Trade reference rules (aggregate only)
        if '⚪ Trade Reference' in label or 'trade_ref' in rule.get('condition', ''):
            return is_aggregate
        
        # RULE 5: Legal rules (aggregate only)
        if '⚫ Legal Risk' in label or 'legal_cases' in rule.get('condition', '') or 'bankruptcy' in rule.get('condition', ''):
            return is_aggregate
        
        # RULE 6: Positive pattern rules
        if '🟢' in label:
            if 'Payment History' in compound_type:
                return is_loan_record
            if 'Utilization' in label:
                return is_loan_record and self._is_revolving_credit(record)
            if 'Credit History' in label or 'Application' in label:
                return is_aggregate
        
        # Default: apply to loan records
        return is_loan_record

    def _apply_template_aliases(self, template: str) -> str:
        """Replace known template variable names with normalized keys"""
        if not template:
            return template
        
        for alias, real_key in self.FIELD_ALIASES.items():
            template = template.replace(f"{{{{{alias}}}}}", f"{{{{ {real_key} }}}}")
            template = template.replace(f"{{{{ {alias} }}}}", f"{{{{ {real_key} }}}}")
            template = template.replace(f"{{{alias}}}", f"{{{real_key}}}")
        
        return template

    def _build_render_context(self, record: Dict[str, Any], personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build rendering context with formatted values"""
        ctx = {**personal_info, **record}
        
        try:
            # Format numeric values
            if 'creditutilizationratio' in ctx:
                ctx['creditutilizationratio'] = float(ctx['creditutilizationratio'])
            if 'balance' in ctx:
                ctx['balance'] = float(ctx.get('balance', 0.0))
            if 'limit' in ctx:
                ctx['limit'] = float(ctx.get('limit', 0.0))
            
            # Add friendly aliases
            ctx['Facility'] = ctx.get('loantype', ctx.get('facility_type', ''))
            ctx['Lender_Type'] = ctx.get('lendertype', ctx.get('lender', ''))
            
            # Add years calculation
            if 'oldest_account_months' in ctx and ctx['oldest_account_months']:
                ctx['oldest_account_years'] = ctx['oldest_account_months'] / 12
                
        except Exception as e:
            self.logger.warning(f"Error building render context: {e}")
        
        return ctx

    def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process normalized data structure"""
        matches = []
        seen_insights = set()
        
        records = data.get('records', [])
        personal_info = data.get('personal_info', {})
        
        self.logger.info(f"Processing {len(records)} records")
        
        for record_idx, record in enumerate(records):
            record_type = self._detect_record_type(record)
            self.logger.debug(f"Record {record_idx}: type={record_type}")
            
            # Build rendering context
            render_ctx = self._build_render_context(record, personal_info)
            
            rules_evaluated = 0
            rules_skipped = 0
            
            for rule in self.rules:
                try:
                    # CRITICAL: Check if rule should apply
                    if not self._should_apply_rule(rule, record):
                        rules_skipped += 1
                        continue
                    
                    rules_evaluated += 1
                    
                    condition = rule.get('condition', '')
                    if not condition:
                        continue
                        
                    if self.parser.evaluate(condition, record):
                        # Rule matched
                        template = rule.get('template', '') or ''
                        template_for_render = self._apply_template_aliases(template)
                        message = self.renderer.render_template(template_for_render, render_ctx) if template_for_render else ''
                        
                        # Deduplication
                        insight_key = f"{rule.get('label')}:{rule.get('compound_type')}:{message}"
                        if insight_key in seen_insights:
                            continue
                            
                        seen_insights.add(insight_key)
                        
                        # Map priority to severity
                        priority = rule.get('priority', '').lower()
                        severity_map = {
                            'critical': 'critical',
                            'high': 'high',
                            'medium': 'medium',
                            'low': 'low',
                            'positive': 'positive'
                        }
                        severity = severity_map.get(priority, 'medium')
                        
                        insight = {
                            'label': rule.get('label', ''),
                            'type': rule.get('compound_type', ''),
                            'message': message,
                            'recommendation': rule.get('recommendation', ''),
                            'severity': severity,
                            'priority': priority,
                            'data_source': rule.get('data_source', ''),
                            'record_type': record_type,
                            'data': record
                        }
                        matches.append(insight)
                        
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.get('label')} on record {record_idx}: {e}")
                    continue
            
            self.logger.debug(f"Record {record_idx}: evaluated {rules_evaluated} rules, skipped {rules_skipped} rules")
                    
        self.logger.info(f"Found {len(matches)} unique insights from {len(records)} records")
        return matches

    def generate_report(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary report from insights"""
        label_counts = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'positive': 0}
        
        for insight in insights:
            label = insight.get('label', 'Unknown')
            severity = insight.get('severity', 'medium')
            
            label_counts[label] = label_counts.get(label, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        report = {
            'total_insights': len(insights),
            'label_counts': label_counts,
            'severity_counts': severity_counts,
            'insights': insights
        }
        
        return report


def save_report(report: Dict, output_file: str):
    """Save report to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f"✓ Report saved to: {output_file}")
    except Exception as e:
        print(f"✗ Error saving report: {e}")


__all__ = ['RuleEngine', 'save_report']