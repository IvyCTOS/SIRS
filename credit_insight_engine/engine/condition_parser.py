from typing import Dict, Any
from asteval import Interpreter
import logging

class ParserError(Exception):
    """Custom exception for parser errors"""
    pass

class ConditionParser:
    """Safely evaluates rule conditions against input data"""
    
    def __init__(self):
        """Initialize parser with security settings and allowed operations"""
        self.aeval = Interpreter(
            use_numpy=False,
            minimal=True,
            max_time=0.1
        )
        self.logger = logging.getLogger(__name__)

    def evaluate(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate condition against provided data"""
        try:
            # Set variables in interpreter's symbol table
            for key, value in data.items():
                self.aeval.symtable[key] = value

            # Evaluate the condition
            result = self.aeval(condition)
            return bool(result) if result is not None else False

        except Exception as e:
            self.logger.error(f"Error evaluating condition: {condition} with data: {data}. Error: {e}")
            raise ParserError(f"Failed to evaluate condition: {str(e)}")

# Expose classes
__all__ = ['ConditionParser', 'ParserError']