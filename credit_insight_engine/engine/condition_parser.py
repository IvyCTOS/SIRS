from typing import Any, Dict, Optional, Callable
from asteval import Interpreter
import logging
from datetime import datetime

class ParserError(Exception):
    """Custom exception for parser errors"""
    pass

class ConditionParser:
    def __init__(self):
        """Initialize parser with security settings and allowed operations"""
        self.aeval = Interpreter(
            use_numpy=False,
            minimal=True,
            max_time=0.1  # Limit evaluation time to prevent infinite loops
        )
        
        # Set up logging
        logging.basicConfig(
            filename=f'logs/parser_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
        
        # Register custom functions
        self.register_custom_functions()

    def register_custom_functions(self):
        """Register custom safe functions for use in conditions"""
        def safe_contains(item: Any, container: Any) -> bool:
            try:
                return item in container
            except TypeError:
                return False

        def safe_between(value: float, min_val: float, max_val: float) -> bool:
            try:
                return float(min_val) <= float(value) <= float(max_val)
            except (TypeError, ValueError):
                return False

        self.aeval.symtable['contains'] = safe_contains
        self.aeval.symtable['between'] = safe_between

    def _clean_value(self, value: Any) -> Any:
        """Clean and normalize input values"""
        if isinstance(value, str):
            # Remove percentage signs and convert to float if possible
            if '%' in value:
                try:
                    return float(value.replace('%', ''))
                except ValueError:
                    pass
        return value

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data dictionary for evaluation"""
        cleaned_data = {}
        for key, value in data.items():
            cleaned_data[key] = self._clean_value(value)
        return cleaned_data

    def validate_condition(self, condition: str) -> bool:
        """Validate condition syntax and security"""
        try:
            # Check for forbidden expressions
            forbidden = ['import', 'eval', 'exec', '__']
            if any(word in condition for word in forbidden):
                raise ParserError(f"Condition contains forbidden expressions: {condition}")
            
            # Try parsing the condition
            self.aeval.parse(condition)
            return True
        except Exception as e:
            self.logger.error(f"Invalid condition: {condition}. Error: {str(e)}")
            return False

    def parse_condition(self, condition: str) -> Optional[Callable]:
        """Parse condition string into executable function"""
        try:
            if not self.validate_condition(condition):
                raise ParserError(f"Invalid condition: {condition}")
            
            parsed = self.aeval.parse(condition)
            return lambda data: self.aeval.run(parsed, local_dict=data)
        except Exception as e:
            self.logger.error(f"Error parsing condition: {condition}. Error: {str(e)}")
            raise ParserError(f"Error parsing condition: {str(e)}")

    def evaluate(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate condition against provided data"""
        try:
            # Prepare data
            cleaned_data = self._prepare_data(data)
            
            # Parse and evaluate condition
            parsed_condition = self.parse_condition(condition)
            if parsed_condition is None:
                return False
            
            # Evaluate with null-safety
            result = parsed_condition(cleaned_data)
            return bool(result) if result is not None else False
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {condition} with data: {data}. Error: {str(e)}")
            return False

def main():
    # Example usage
    parser = ConditionParser()
    
    # Test data
    test_data = {
        'balance': 5000,
        'limit': 10000,
        'ratio': '80%',
        'status': 'active'
    }
    
    # Test conditions
    conditions = [
        "balance > limit * 0.8",
        "ratio > 75",
        "status == 'active'",
        "between(balance, 0, limit)"
    ]
    
    # Evaluate conditions
    for condition in conditions:
        result = parser.evaluate(condition, test_data)
        print(f"Condition: {condition} -> Result: {result}")

if __name__ == "__main__":
    main()