"""
FIXED Rule Engine - Uses rule groups for proper application logic
Key improvements:
1. Rule application based on rule 'group' metadata (more robust)
2. Payment conduct rules apply to ALL loan records
3. Score rules apply to aggregate records  
4. Proper handling of all rule groups from rules.json
5. ✅ NEW: Recommendations are now rendered through Jinja2 templates
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
        ✅ IMPROVED: Determine if a rule should be applied based on rule group and condition
        Uses the 'group' field from rules.json for more robust logic
        """
        rule_id = rule.get('id', '')
        rule_group = rule.get('group', '')
        condition = rule.get('condition', '')
        
        record_type = self._detect_record_type(record)
        is_loan_record = (record_type == 'loan')
        is_aggregate = (record_type == 'aggregate')
        
        # ===== GROUP-BASED RULE APPLICATION =====
        
        # 1. UTILIZATION rules - only for revolving credit loans
        if rule_group == 'utilization':
            return is_loan_record and self._is_revolving_credit(record)
        
        # 2. PAYMENT_CONDUCT rules - ALL loan records (not just revolving)
        elif rule_group == 'payment_conduct':
            return is_loan_record
        
        # 3. CREDIT_APPLICATIONS rules - aggregate only
        elif rule_group == 'credit_applications':
            return is_aggregate
        
        # 4. CREDIT_PROFILE rules - aggregate only
        elif rule_group == 'credit_profile':
            return is_aggregate
        
        # 5. LEGAL_FINANCIAL rules - check specific conditions
        elif rule_group == 'legal_financial':
            # Trade reference rules
            if 'trade_ref' in condition:
                return is_aggregate
            # Legal/bankruptcy rules
            elif any(keyword in condition for keyword in ['legal_cases', 'bankruptcy', 'director_windingup']):
                return is_aggregate
            else:
                return is_aggregate
        
        # 6. PORTFOLIO_HEALTH rules - aggregate only
        elif rule_group == 'portfolio_health':
            return is_aggregate
        
        # 7. POSITIVE_BEHAVIORS rules - context-dependent
        elif rule_group == 'positive_behaviors':
            # Check what the rule evaluates
            if 'payment_conduct_all_zero' in condition:
                # Payment history - loan level
                return is_loan_record
            elif 'creditutilizationratio' in condition and ('is_revolving' in condition or 'revolving' in rule_id.lower()):
                # Utilization - revolving loans only
                return is_loan_record and self._is_revolving_credit(record)
            elif 'ctos_score' in condition:
                # Score rules - aggregate only
                return is_aggregate
            elif any(keyword in condition for keyword in ['oldest_account_months', 'numapplicationslast12months', 'legal_cases', 'distinct_account_types']):
                # Portfolio metrics - aggregate only
                return is_aggregate
            else:
                # Default for positive behaviors - aggregate
                return is_aggregate
        
        # 8. RISK_AMPLIFICATION rules - compound rules
        elif rule_group == 'risk_amplification':
            # Check if it involves loan-level metrics
            if 'creditutilizationratio' in condition and 'payment_conduct_code' in condition:
                # Utilization + payment - loan level for revolving
                return is_loan_record and self._is_revolving_credit(record)
            elif 'creditutilizationratio' in condition and 'numapplicationslast12months' in condition:
                # Utilization + applications - aggregate (uses both loan and portfolio data)
                return is_aggregate
            elif 'legal_cases_active' in condition:
                # Legal + financial - aggregate
                return is_aggregate
            else:
                # Default compound rules to aggregate
                return is_aggregate
        
        # 9. EARLY_WARNINGS rules - context-dependent
        elif rule_group == 'early_warnings':
            # Check what variables the rule uses
            if 'ctos_score' in condition:
                # Score rules - aggregate only
                return is_aggregate
            elif 'creditutilizationratio' in condition and is_loan_record:
                # Utilization warnings - loan level for revolving
                return self._is_revolving_credit(record)
            elif 'numapplicationslast12months' in condition:
                # Application warnings - aggregate
                return is_aggregate
            elif 'payment_conduct_code' in condition and 'oldest_account_months' in condition:
                # Payment pattern warnings - loan level
                return is_loan_record
            else:
                # Default warnings to loan level
                return is_loan_record
        
        # Default: If no group specified or unknown group, use condition analysis
        else:
            self.logger.warning(f"Unknown rule group '{rule_group}' for rule {rule_id}, using fallback logic")
            # Fallback: check if condition uses aggregate variables
            aggregate_vars = ['numberofloans', 'numapplicationslast12months', 'ctos_score', 
                            'legal_cases', 'trade_ref', 'distinct_account_types']
            if any(var in condition for var in aggregate_vars):
                return is_aggregate
            else:
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
        """Build rendering context - PRESERVE numeric types"""
        ctx = {**personal_info, **record}
        
        try:
            # ✅ KEEP numeric values as-is (don't convert to strings)
            # Jinja2 filters need numeric types
            
            # Add friendly aliases (keep originals too)
            if 'loantype' not in ctx:
                ctx['loantype'] = ctx.get('facility_type', '')
            if 'Facility' not in ctx:
                ctx['Facility'] = ctx.get('loantype', ctx.get('facility_type', ''))
            if 'Lender_Type' not in ctx:
                ctx['Lender_Type'] = ctx.get('lendertype', ctx.get('lender', ''))
            
            # Ensure oldest_account_years is calculated if not present
            if 'oldest_account_years' not in ctx and 'oldest_account_months' in ctx:
                if ctx['oldest_account_months']:
                    ctx['oldest_account_years'] = ctx['oldest_account_months'] / 12
                else:
                    ctx['oldest_account_years'] = 0.0
                
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
                        # Rule matched - render both message AND recommendation
                        template = rule.get('template', '') or ''
                        template_for_render = self._apply_template_aliases(template)
                        message = self.renderer.render_template(template_for_render, render_ctx) if template_for_render else ''
                        
                        # ✅ NEW: Render recommendation through Jinja2 too
                        recommendation_template = rule.get('recommendation', '') or ''
                        recommendation_for_render = self._apply_template_aliases(recommendation_template)
                        recommendation = self.renderer.render_template(recommendation_for_render, render_ctx) if recommendation_for_render else ''
                        
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
                            'recommendation': recommendation,  # ✅ Now fully rendered
                            'severity': severity,
                            'priority': priority,
                            'data_source': rule.get('data_source', ''),
                            'record_type': record_type,
                            'rule_id': rule.get('id', ''),
                            'rule_group': rule.get('group', ''),
                            'impact_score': rule.get('impact_score', 0),
                            'data': record
                        }
                        matches.append(insight)
                        
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.get('id')} ({rule.get('label')}) on record {record_idx}: {e}")
                    continue
            
            self.logger.debug(f"Record {record_idx}: evaluated {rules_evaluated} rules, skipped {rules_skipped} rules")
                    
        self.logger.info(f"Found {len(matches)} unique insights from {len(records)} records")
        return matches

    def generate_report(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary report from insights"""
        label_counts = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'positive': 0}
        group_counts = {}
        total_impact = 0
        
        for insight in insights:
            label = insight.get('label', 'Unknown')
            severity = insight.get('severity', 'medium')
            group = insight.get('rule_group', 'unknown')
            impact = insight.get('impact_score', 0)
            
            label_counts[label] = label_counts.get(label, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            group_counts[group] = group_counts.get(group, 0) + 1
            
            # Sum impact scores (negative for positive insights)
            if severity != 'positive':
                total_impact += impact
        
        # Calculate overall risk level
        if total_impact >= 200:
            risk_level = "CRITICAL"
        elif total_impact >= 150:
            risk_level = "HIGH"
        elif total_impact >= 100:
            risk_level = "MODERATE"
        elif total_impact >= 50:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        report = {
            'total_insights': len(insights),
            'label_counts': label_counts,
            'severity_counts': severity_counts,
            'group_counts': group_counts,
            'total_impact_score': total_impact,
            'risk_level': risk_level,
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