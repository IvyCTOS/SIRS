from jinja2 import Environment, BaseLoader, Template
from typing import Any, Dict, Optional
import json
import logging
from datetime import datetime
from pathlib import Path

class TemplateError(Exception):
    """Custom exception for template rendering errors"""
    pass

class TemplateRenderer:
    def __init__(self, templates_file: str = None):
        """Initialize template engine with custom filters and settings"""
        # Set up Jinja2 environment
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=True
        )
        
        # Register custom filters
        self._register_filters()
        
        # Load templates if file provided
        self.templates = {}
        if templates_file:
            self.load_templates(templates_file)
        
        # Set up logging
        logging.basicConfig(
            filename=f'logs/template_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO
        )
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

    def format_value(self, value: Any, format_type: str) -> str:
        """Format a value according to specified type"""
        if format_type not in self.env.filters:
            raise TemplateError(f"Unknown format type: {format_type}")
        
        try:
            return self.env.filters[format_type](value)
        except Exception as e:
            self.logger.error(f"Error formatting value: {str(e)}")
            return str(value)

    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render a template with provided data"""
        try:
            # Get template
            if template_name in self.templates:
                template_data = self.templates[template_name]
                template_str = template_data['message']
                fallbacks = template_data.get('fallbacks', {})
            else:
                template_str = template_name
                fallbacks = {}

            # Apply fallbacks for missing data
            render_data = {**fallbacks, **data}

            # Create and render template
            template = self.env.from_string(template_str)
            return template.render(**render_data)

        except Exception as e:
            self.logger.error(f"Template rendering error: {str(e)}")
            raise TemplateError(f"Failed to render template: {str(e)}")

def main():
    # Example usage
    template_renderer = TemplateRenderer()
    
    # Test data
    data = {
        'loan_type': 'Credit Card',
        'balance': 5000.75,
        'ratio': 85.6,
        'date': '2023-10-17'
    }
    
    # Test template rendering
    template = "Your {{loan_type}} balance is {{balance|currency}} with {{ratio|percentage}} utilization as of {{date|date}}"
    try:
        result = template_renderer.render_template(template, data)
        print(f"Rendered template: {result}")
    except TemplateError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()