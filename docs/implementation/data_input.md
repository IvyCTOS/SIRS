# Data Input Module for Rule-Based Credit Behaviour Insight Engine

## Overview
The Data Input Module is responsible for ingesting structured data from CTOS credit reports in PDF format and converting it into a normalized JSON format suitable for rule evaluation.

## Objectives
- Extract relevant data from CTOS credit report PDFs.
- Normalize and clean the extracted data.
- Prepare the data for input into the Rule Engine.

## Steps for Implementation

### 1. PDF Parsing
- **Library Selection**: library for PDF parsing `PyPDF2`.
- **Implementation**:
  - Create a function to read the PDF file and extract text.
  - Identify and extract relevant sections of the credit report (e.g., Loan Information, Special Attention Account, etc.).

### 2. Data Structuring
- **Define Data Structure**: 
  - Create a schema for the JSON output that includes fields for each relevant section of the credit report.
- **Implementation**:
  - Develop functions to map extracted data to the defined JSON structure.
  - Ensure that the data is organized by report sections.

### 3. Data Normalization
- **Cleaning Data**: 
  - Implement functions to handle missing values, incorrect formats, and data type conversions.
- **Normalization Process**:
  - Standardize formats for dates, currency, and numerical values.
  - Remove any unnecessary whitespace or special characters.

### 4. Output Generation
- **JSON Output**: 
  - Create a function to output the cleaned and normalized data as a JSON file.
- **Validation**: 
  - Implement validation checks to ensure the output meets the expected schema.

## Example Code Snippet
```python
import pdfparser
import json

def extract_data_from_pdf(pdf_file):
    # ...code to extract data from PDF...
    return extracted_data

def normalize_data(extracted_data):
    # ...code to clean and normalize data...
    return normalized_data

def save_to_json(normalized_data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(normalized_data, json_file, indent=4)

# Example usage
pdf_file = 'path/to/ctos_credit_report.pdf'
extracted_data = extract_data_from_pdf(pdf_file)
normalized_data = normalize_data(extracted_data)
save_to_json(normalized_data, 'output/normalized_data.json')
```

## Testing
- **Unit Tests**: 
  - Write unit tests for each function to ensure they work as expected.
- **Integration Tests**: 
  - Test the entire data input process from PDF extraction to JSON output.

## Future Enhancements
- **Error Handling**: 
  - Implement robust error handling for file reading and data extraction processes.
- **Support for Multiple Formats**: 
  - Extend the module to support other input formats (e.g., CSV).
