from jinja2 import Environment, BaseLoader, StrictUndefined, UndefinedError
from typing import Any, Dict
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from string import Template

class TemplateError(Exception):
    """Custom exception for template rendering errors"""
    pass

class TemplateRenderer:
    def __init__(self, templates_file: str = None):
        """Initialize template engine with custom filters and settings"""
        # CRITICAL FIX: Use StrictUndefined to catch missing variables
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            undefined=StrictUndefined  # ✅ Will raise error for missing variables
        )
        
        # Register custom filters
        self._register_filters()
        
        # Load templates if file provided
        self.templates = {}
        if templates_file:
            self.load_templates(templates_file)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def _register_filters(self):
        """Register custom filters for formatting values"""
        def format_currency(value: float) -> str:
            try:
                return f"RM {float(value):,.2f}"
            except (ValueError, TypeError):
                return "RM 0.00"

        def format_percentage(value: float) -> str:
            try:
                return f"{float(value):.1f}%"
            except (ValueError, TypeError):
                return "0.0%"

        def format_date(value: str) -> str:
            try:
                date = datetime.strptime(value, "%Y-%m-%d")
                return date.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                return value

        # Register filters
        self.env.filters['currency'] = format_currency
        self.env.filters['percentage'] = format_percentage
        self.env.filters['date'] = format_date

    def load_templates(self, template_file: str):
        """Load templates from JSON file"""
        try:
            with open(template_file, 'r') as file:
                self.templates = json.load(file)
        except Exception as e:
            self.logger.error(f"Error loading templates: {str(e)}")
            raise TemplateError(f"Failed to load templates: {str(e)}")

    def validate_template(self, template: str) -> bool:
        """Validate template syntax and required fields"""
        try:
            self.env.parse(template)
            return True
        except Exception as e:
            self.logger.error(f"Template validation error: {str(e)}")
            return False

    def _extract_variables(self, template_str: str) -> set:
        """Extract all variable names from template"""
        # Match both {{ var }} and {{var}} patterns
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        variables = set(re.findall(pattern, template_str))
        return variables

    def _validate_data(self, template_str: str, data: Dict[str, Any]) -> tuple:
        """
        Validate that all required variables exist in data
        Returns: (is_valid, missing_variables)
        """
        required_vars = self._extract_variables(template_str)
        missing_vars = required_vars - set(data.keys())
        
        return (len(missing_vars) == 0, missing_vars)

    def _add_default_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for common variables if missing"""
        defaults = {
            'Facility': 'facility',
            'loantype': 'loan',
            'Lender_Type': 'lender',
            'lendertype': 'lender',
            'balance': 0.0,
            'limit': 0.0,
            'creditutilizationratio': 0.0,
            'case_types': '',
            'case_details': ''
        }
        
        result = {**defaults, **data}
        return result

    def format_value(self, value: Any, format_type: str) -> str:
        """Format a value according to specified type"""
        if format_type not in self.env.filters:
            raise TemplateError(f"Unknown format type: {format_type}")
        
        try:
            return self.env.filters[format_type](value)
        except Exception as e:
            self.logger.error(f"Error formatting value: {str(e)}")
            return str(value)

    def render_template(self, template_string: str, data: Dict[str, Any]) -> str:
        """
        Render a template with provided data
        FIXED: Better variable validation and error handling
        
        Args:
            template_string: Template string with {{variable}} placeholders
            data: Dictionary of variable values
            
        Returns:
            Rendered template string
        """
        try:
            # If template_string is actually a template name (key in self.templates)
            if template_string in self.templates:
                template_data = self.templates[template_string]
                template_str = template_data['message']
                fallbacks = template_data.get('fallbacks', {})
            else:
                template_str = template_string
                fallbacks = {}

            # CRITICAL FIX: Validate required variables
            is_valid, missing_vars = self._validate_data(template_str, data)
            
            if not is_valid:
                self.logger.warning(f"Missing variables in template: {missing_vars}")
                self.logger.warning(f"Template: {template_str[:100]}...")
                self.logger.warning(f"Available data keys: {list(data.keys())}")
                
                # Add defaults for missing variables
                data = self._add_default_values(data)

            # Apply fallbacks for missing data
            render_data = {**fallbacks, **data}
            
            # Format numeric values appropriately
            formatted_data = self._format_values(render_data)

            # Create and render template
            template = self.env.from_string(template_str)
            result = template.render(**formatted_data)
            
            return result

        except UndefinedError as e:
            # Specific error for missing variables
            self.logger.error(f"Undefined variable in template: {str(e)}")
            self.logger.error(f"Template: {template_str}")
            self.logger.error(f"Available data: {list(data.keys())}")
            raise TemplateError(f"Missing required variable: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Template rendering error: {str(e)}")
            self.logger.error(f"Template: {template_str[:100]}...")
            self.logger.error(f"Data keys: {list(data.keys())}")
            raise TemplateError(f"Failed to render template: {str(e)}")

    def render_template_simple(self, template: str, data: Dict[str, Any]) -> str:
        """
        Render template with data, formatting numbers appropriately
        NOTE: This uses Python string.Template which expects $variable syntax
        For {{variable}} syntax, use render_template() instead
        """
        try:
            # Format numeric values
            formatted_data = self._format_values(data)

            # Use string Template for safe substitution
            # Note: string.Template uses $variable, not {{variable}}
            return Template(template).safe_substitute(formatted_data)
            
        except Exception as e:
            self.logger.error(f"Template rendering error: {e}")
            return template

    def _format_values(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Format values appropriately based on type and key name"""
        formatted = {}
        
        for key, value in data.items():
            if value is None:
                formatted[key] = ''
            elif isinstance(value, float):
                # Handle special formatting for known keys
                if key in ['creditutilizationratio', 'utilization']:
                    formatted[key] = f"{value:.1f}"
                elif key in ['balance', 'limit']:
                    formatted[key] = f"{value:,.2f}"
                elif 'ratio' in key.lower() or 'percentage' in key.lower():
                    formatted[key] = f"{value:.1f}"
                elif 'amount' in key.lower() or 'value' in key.lower():
                    formatted[key] = f"{value:,.2f}"
                else:
                    formatted[key] = f"{value:.2f}"
            elif isinstance(value, bool):
                formatted[key] = str(value)
            elif isinstance(value, (int, float)):
                formatted[key] = str(value)
            else:
                formatted[key] = str(value) if value is not None else ''
                
        return formatted


def main():
    # Example usage and testing
    template_renderer = TemplateRenderer()
    
    print("="*60)
    print("TEMPLATE RENDERER TESTING")
    print("="*60)
    
    # Test 1: Complete data
    print("\n[Test 1] Complete data:")
    data1 = {
        'loantype': 'Credit Card',
        'Facility': 'Credit Card',
        'Lender_Type': 'CIMB Bank',
        'creditutilizationratio': 65.14,
        'balance': 5000.75,
        'limit': 7000.00
    }
    
    template1 = "Your {{Facility}} with {{Lender_Type}} has a utilization rate of {{creditutilizationratio}}%"
    
    try:
        result = template_renderer.render_template(template1, data1)
        print(f"✓ Result: {result}")
    except TemplateError as e:
        print(f"✗ Error: {str(e)}")
    
    # Test 2: Missing variable (should add default)
    print("\n[Test 2] Missing variable:")
    data2 = {
        'Lender_Type': 'Alliance Bank',
        'creditutilizationratio': 85.0
        # Missing: Facility
    }
    
    template2 = "Your {{Facility}} with {{Lender_Type}} has {{creditutilizationratio}}% utilization"
    
    try:
        result = template_renderer.render_template(template2, data2)
        print(f"⚠  Result: {result}")
        print("  (Note: 'Facility' was missing but default was added)")
    except TemplateError as e:
        print(f"✗ Error: {str(e)}")
    
    # Test 3: Legal case template
    print("\n[Test 3] Legal case template:")
    data3 = {
        'legal_cases_active': 1,
        'case_types': 'SUMMONS - DIRECTED TO'
    }
    
    template3 = "You have {{legal_cases_active}} active legal case(s): {{case_types}}."
    
    try:
        result = template_renderer.render_template(template3, data3)
        print(f"✓ Result: {result}")
    except TemplateError as e:
        print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()