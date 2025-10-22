"""
Condition Parser Module - Production Ready
Safely evaluates rule conditions against normalized credit data records

Key Features:
- Safe evaluation using asteval (no exec/eval vulnerabilities)
- Comprehensive default values for all credit report variables
- Automatic type coercion and validation
- Detailed error logging and debugging support
"""

from typing import Dict, Any, Set, Tuple
from asteval import Interpreter
import logging
import re


class ParserError(Exception):
    """Custom exception for parser-related errors"""
    pass


class ConditionParser:
    """
    Safely evaluates boolean conditions against credit data records.
    
    Usage:
        parser = ConditionParser()
        result = parser.evaluate("creditutilizationratio > 80", {"creditutilizationratio": 85})
        # Returns: True
    """
    
    # Define all possible variables used in credit rules with their default values
    DEFAULT_VALUES = {
        # === Loan-Level Numeric Variables ===
        'creditutilizationratio': 0.0,
        'balance': 0.0,
        'limit': 0.0,
        'payment_conduct_code': 0,
        'mon_arrears': 0,
        'inst_arrears': 0,
        'utilization': 0.0,
        
        # === Portfolio/Aggregate Numeric Variables ===
        'numberofloans': 0,
        'numapplicationslast12months': 0,
        'numpendingapplications': 0,
        'numapprovedapplications': 0,
        'distinct_account_types': 0,
        'oldest_account_months': 0,
        'oldest_account_years': 0.0,
        'accounts_per_lender': 0,
        'secured_loan_ratio': 0.0,
        'recent_enquiries': 0,
        'application_decline_rate': 0.0,
        
        # === Trade Reference Variables ===
        'trade_ref_amount_overdue': 0.0,
        'trade_ref_reminder_count': 0,
        
        # === Legal Variables ===
        'legal_cases_settled': 0,
        'legal_cases_active': 0,
        'director_windingup_company': 0,
        
        # === Boolean Variables ===
        'has_credit_card': False,
        'has_installment_loan': False,
        'bankruptcy_active': False,
        'payment_conduct_all_zero': False,
        'is_revolving': False,
        'is_secured': False,
        
        # === String Variables ===
        'facility_type': '',
        'loantype': '',
        'loan_type': '',
        'lendertype': '',
        'lender': '',
        'account_type': '',
        'aging_bucket': '',
        'case_details': '',
        'case_types': '',
        'company_name': '',
        'lender_name': '',
        'status': '',
        
        # === Template Variables (for rendering) ===
        'Facility': '',
        'Lender_Type': '',
        'name': '',
        'ic_number': '',
        'ctos_score': 0
    }
    
    def __init__(self, debug: bool = False):
        """
        Initialize the condition parser
        
        Args:
            debug: Enable debug logging for condition evaluation
        """
        # Initialize asteval interpreter with security settings
        self.aeval = Interpreter(
            use_numpy=False,      # Don't load numpy (security)
            minimal=True,         # Minimal symbol table
            max_time=0.1         # Max 100ms per evaluation
        )
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Statistics for monitoring
        self.stats = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'missing_variables': {}
        }

    def _normalize_condition(self, condition: str) -> str:
        """
        Normalize condition syntax for Python evaluation
        
        Handles:
        - JavaScript-style booleans (true/false -> True/False)
        - Whitespace cleanup
        - Common syntax variations
        
        Args:
            condition: Raw condition string
            
        Returns:
            Normalized condition string
        """
        if not condition:
            return ""
        
        # Replace JavaScript-style booleans
        replacements = {
            '== true': '== True',
            '== false': '== False',
            '!= true': '!= True',
            '!= false': '!= False',
            ' true ': ' True ',
            ' false ': ' False '
        }
        
        normalized = condition
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Clean up whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized

    def _extract_variable_names(self, condition: str) -> Set[str]:
        """
        Extract all variable names from a condition string
        
        Args:
            condition: Condition string to parse
            
        Returns:
            Set of variable names found in the condition
        """
        # Match valid Python identifiers
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        variables = set(re.findall(pattern, condition))
        
        # Remove Python keywords and operators
        python_keywords = {
            'and', 'or', 'not', 'in', 'is', 
            'True', 'False', 'None',
            'if', 'else', 'elif', 'for', 'while'
        }
        
        return variables - python_keywords

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for evaluation by adding defaults and type coercion
        
        Args:
            data: Raw input data dictionary
            
        Returns:
            Prepared data with defaults and proper types
        """
        # Start with defaults
        prepared = self.DEFAULT_VALUES.copy()
        
        # Override with actual data
        for key, value in data.items():
            if value is not None:
                prepared[key] = value
        
        # Type coercion for numeric fields
        numeric_fields = [
            'creditutilizationratio', 'balance', 'limit', 'utilization',
            'secured_loan_ratio', 'application_decline_rate', 'oldest_account_years'
        ]
        
        for field in numeric_fields:
            if field in prepared and prepared[field] is not None:
                try:
                    prepared[field] = float(prepared[field])
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not convert {field}={prepared[field]} to float, using 0.0")
                    prepared[field] = 0.0
        
        # Integer fields
        integer_fields = [
            'payment_conduct_code', 'numberofloans', 'numapplicationslast12months',
            'numpendingapplications', 'distinct_account_types', 'oldest_account_months',
            'accounts_per_lender', 'recent_enquiries', 'trade_ref_reminder_count',
            'legal_cases_settled', 'legal_cases_active', 'director_windingup_company',
            'mon_arrears', 'inst_arrears', 'ctos_score'
        ]
        
        for field in integer_fields:
            if field in prepared and prepared[field] is not None:
                try:
                    prepared[field] = int(float(prepared[field]))
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not convert {field}={prepared[field]} to int, using 0")
                    prepared[field] = 0
        
        # Boolean fields
        boolean_fields = [
            'has_credit_card', 'has_installment_loan', 'bankruptcy_active',
            'payment_conduct_all_zero', 'is_revolving', 'is_secured'
        ]
        
        for field in boolean_fields:
            if field in prepared and prepared[field] is not None:
                prepared[field] = bool(prepared[field])
        
        return prepared

    def _validate_condition(self, condition: str, data: Dict[str, Any]) -> Tuple[bool, Set[str]]:
        """
        Validate that all required variables exist in the data
        
        Args:
            condition: Condition string to validate
            data: Data dictionary to check against
            
        Returns:
            Tuple of (is_valid, missing_variables)
        """
        required_vars = self._extract_variable_names(condition)
        available_vars = set(data.keys())
        missing_vars = required_vars - available_vars
        
        return (len(missing_vars) == 0, missing_vars)

    def evaluate(self, condition: str, data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition against provided data
        
        Args:
            condition: Boolean condition string (e.g., "creditutilizationratio > 80")
            data: Dictionary of variable values
            
        Returns:
            Boolean result of the condition evaluation
            
        Raises:
            ParserError: If the condition cannot be evaluated
            
        Examples:
            >>> parser = ConditionParser()
            >>> parser.evaluate("creditutilizationratio > 80", {"creditutilizationratio": 85})
            True
            >>> parser.evaluate("payment_conduct_code >= 3", {"payment_conduct_code": 1})
            False
        """
        self.stats['total_evaluations'] += 1
        
        try:
            # Step 1: Normalize the condition
            normalized_condition = self._normalize_condition(condition)
            
            if not normalized_condition:
                self.logger.warning("Empty condition provided")
                return False
            
            # Step 2: Prepare data with defaults
            prepared_data = self._prepare_data(data)
            
            # Step 3: Validate (optional, for debugging)
            if self.logger.isEnabledFor(logging.DEBUG):
                is_valid, missing = self._validate_condition(normalized_condition, prepared_data)
                if not is_valid:
                    self.logger.debug(f"Condition has missing variables (will use defaults): {missing}")
                
                required_vars = self._extract_variable_names(normalized_condition)
                var_values = {var: prepared_data.get(var, 'MISSING') for var in required_vars}
                self.logger.debug(f"Evaluating: {normalized_condition}")
                self.logger.debug(f"Variables: {var_values}")
            
            # Step 4: Load variables into interpreter
            for key, value in prepared_data.items():
                self.aeval.symtable[key] = value
            
            # Step 5: Evaluate the condition
            result = self.aeval(normalized_condition)
            
            # Step 6: Handle result
            if result is None:
                self.logger.warning(f"Condition returned None: {normalized_condition}")
                self.stats['failed_evaluations'] += 1
                return False
            
            # Convert to boolean
            bool_result = bool(result)
            self.stats['successful_evaluations'] += 1
            
            return bool_result
            
        except NameError as e:
            # Variable not found (shouldn't happen with defaults, but log it)
            self.logger.error(f"NameError in condition '{condition}': {e}")
            self.logger.error(f"Available variables: {list(data.keys())}")
            
            # Track missing variable
            var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
            self.stats['missing_variables'][var_name] = self.stats['missing_variables'].get(var_name, 0) + 1
            
            self.stats['failed_evaluations'] += 1
            return False
            
        except SyntaxError as e:
            # Invalid Python syntax
            self.logger.error(f"SyntaxError in condition '{condition}': {e}")
            self.stats['failed_evaluations'] += 1
            raise ParserError(f"Invalid condition syntax: {str(e)}")
            
        except Exception as e:
            # Other unexpected errors
            self.logger.error(f"Unexpected error evaluating condition '{condition}': {e}", exc_info=True)
            self.stats['failed_evaluations'] += 1
            raise ParserError(f"Failed to evaluate condition: {str(e)}")

    def test_condition(self, condition: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a condition and return detailed diagnostic information
        
        Useful for debugging rule definitions and understanding why conditions
        match or don't match.
        
        Args:
            condition: Condition string to test
            data: Data to test against
            
        Returns:
            Dictionary with evaluation results and diagnostic info
        """
        try:
            # Normalize condition
            normalized = self._normalize_condition(condition)
            
            # Prepare data
            prepared = self._prepare_data(data)
            
            # Extract variables
            required_vars = self._extract_variable_names(normalized)
            
            # Check for missing
            is_valid, missing = self._validate_condition(normalized, prepared)
            
            # Get actual values used
            var_values = {var: prepared.get(var) for var in required_vars}
            
            # Evaluate
            result = self.evaluate(condition, data)
            
            return {
                'success': True,
                'result': result,
                'condition': condition,
                'normalized_condition': normalized,
                'required_variables': required_vars,
                'variable_values': var_values,
                'missing_variables': missing,
                'used_defaults': not is_valid,
                'error': None
            }
            
        except ParserError as e:
            return {
                'success': False,
                'result': None,
                'condition': condition,
                'error': str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parser usage statistics
        
        Returns:
            Dictionary with evaluation statistics
        """
        success_rate = 0.0
        if self.stats['total_evaluations'] > 0:
            success_rate = (self.stats['successful_evaluations'] / 
                          self.stats['total_evaluations'] * 100)
        
        return {
            'total_evaluations': self.stats['total_evaluations'],
            'successful_evaluations': self.stats['successful_evaluations'],
            'failed_evaluations': self.stats['failed_evaluations'],
            'success_rate': f"{success_rate:.1f}%",
            'missing_variables': self.stats['missing_variables']
        }

    def reset_statistics(self):
        """Reset all statistics counters"""
        self.stats = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'missing_variables': {}
        }


# Convenience functions for testing
def quick_evaluate(condition: str, data: Dict[str, Any]) -> bool:
    """
    Quick one-off condition evaluation
    
    Args:
        condition: Condition to evaluate
        data: Data dictionary
        
    Returns:
        Boolean result
    """
    parser = ConditionParser()
    return parser.evaluate(condition, data)


# Public API
__all__ = ['ConditionParser', 'ParserError', 'quick_evaluate']