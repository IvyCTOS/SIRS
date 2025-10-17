# Template Renderer Module for Rule-Based Credit Behaviour Insight Engine

## Overview
The Template Renderer Module is responsible for converting insight templates into personalized messages by replacing placeholders with actual values from the credit report data, ensuring consistent formatting across all outputs.

## Objectives
- Replace template placeholders with actual values
- Format values consistently (currency, percentages, dates)
- Handle missing values gracefully
- Support multiple template formats
- Ensure output consistency

## Steps for Implementation

### 1. Template Engine Setup
- **Library Selection**:
  - Use `Jinja2` for template rendering
  - Configure template environment settings
- **Configuration**:
  - Define custom filters for formatting
  - Set up template loading paths
  - Configure error handling

### 2. Value Formatting
- **Format Types**:
  - Currency: `RM 1,234.56`
  - Percentages: `85.5%`
  - Dates: `DD/MM/YYYY`
  - Numbers: Thousand separators
- **Implementation**:
  - Create custom filters for each format type
  - Implement validation for each data type
  - Add default formatting rules

### 3. Placeholder Management
- **Placeholder Types**:
  - Simple replacements: `{loan_type}`
  - Formatted values: `{balance:currency}`
  - Conditional text: `{% if high_risk %}...{% endif %}`
- **Implementation**:
  - Define placeholder syntax rules
  - Create placeholder validation system
  - Implement fallback values

### 4. Template Storage
- **Storage Format**:
  - JSON template definitions
  - Template inheritance support
  - Reusable template snippets
- **Example Structure**:
```json
{
    "templates": {
        "high_utilization": {
            "message": "Your {loan_type} with {lender} has a utilization of {ratio:percentage}",
            "formats": {
                "ratio": "percentage",
                "balance": "currency"
            },
            "fallbacks": {
                "lender": "your bank",
                "loan_type": "credit facility"
            }
        }
    }
}
```

### 5. Error Handling
- **Error Types**:
  - Missing required values
  - Invalid format specifications
  - Template syntax errors
- **Implementation**:
  - Create custom error classes
  - Implement error logging
  - Provide fallback templates

## Example Interface
```python
class TemplateRenderer:
    def __init__(self):
        """Initialize template engine with custom filters and settings"""
        pass

    def render_template(self, template_name: str, data: dict) -> str:
        """Render a template with provided data"""
        pass

    def format_value(self, value: Any, format_type: str) -> str:
        """Format a value according to specified type"""
        pass

    def validate_template(self, template: str) -> bool:
        """Validate template syntax and required fields"""
        pass
```

## Testing
- **Unit Tests**:
  - Test each format type
  - Test placeholder replacement
  - Test error handling
  - Test template validation
- **Integration Tests**:
  - Test with actual rule engine output
  - Test template inheritance
  - Test complex templates

## Error Handling Examples
```python
# Example scenarios to handle:
templates = {
    "missing_value": "Balance: {balance:currency}",
    "invalid_format": "Rate: {rate:invalid}",
    "syntax_error": "Amount: {{amount}"
}
```

## Future Enhancements
- **Template Caching**:
  - Implement template compilation caching
  - Add template versioning
- **Advanced Features**:
  - Multi-language support
  - Dynamic template loading
  - Template customization based on user preferences
- **Performance Optimization**:
  - Batch rendering
  - Lazy loading of templates
  - Template precompilation

## Usage Examples
```python
# Basic usage
renderer = TemplateRenderer()
data = {
    'loan_type': 'Credit Card',
    'balance': 5000.75,
    'ratio': 0.856
}
message = renderer.render_template('high_utilization', data)

# With formatting
message = renderer.render_template(
    'Your {loan_type} balance is {balance:currency} ({ratio:percentage})',
    data
)
```