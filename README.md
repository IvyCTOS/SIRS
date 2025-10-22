# CTOS Credit Insight Engine

> Automated credit report analysis and personalized financial recommendations

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-2.1-green)](https://github.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository_url>
cd credit_insight_engine

# Install dependencies
pip install jinja2 asteval

# Run with sample data
python main.py
```

### Basic Usage

```bash
# Process default XML file
python main.py

# Process specific file
python main.py data/sample_2.xml

# Output
# ✓ Console: Formatted report
# ✓ File: output/report_sample_2.json
```

---

## 📋 Features

- ✅ **XML Parsing**: Extracts data from CTOS credit reports
- ✅ **24+ Rules**: Predefined credit risk evaluation rules
- ✅ **Smart Analysis**: Detects payment issues, utilization, legal risks
- ✅ **Personalized Messages**: Template-based recommendations
- ✅ **Multi-Level Severity**: Critical, High, Medium, Low, Positive
- ✅ **JSON Export**: Machine-readable output for integration

---

## 📊 Sample Output

```
======================================================================
                    Credit Behavior Insight Report
======================================================================
Generated: 2025-10-22 14:08:06
Total Insights: 9

Summary by Severity:
----------------------------------------------------------------------
  ⛔ Critical: 1
  🔴 High: 1
  🟡 Medium: 1
  ✅ Positive: 6

======================================================================
🟠 Missed Payments
======================================================================

1. Serious Delinquency
   ⛔ Your Other Term Loan with Perbadanan Tabung Pendidikan Tinggi 
      Nasional (PTPTN) has serious delinquency (code 8) indicating 
      60+ days overdue.

   💡 Recommendation:
      Accounts 60+ days overdue severely damage your credit. Reach 
      out to your lender immediately to negotiate a payment plan or 
      restructuring.
```

---

## 🏗️ Architecture

```
XML Report → Data Extraction → Rule Evaluation → Report Generation
                ↓                    ↓                   ↓
         Normalized Data      Condition Check      Console/JSON
```

**Key Components:**
- **Data Input**: XML parsing & normalization
- **Rule Engine**: Condition evaluation & rule matching
- **Template System**: Personalized message generation
- **Output**: Console reports & JSON export

---

## 📁 Project Structure

```
credit_insight_engine/
├── data/                   # Sample XML reports
│   ├── sample_xml.xml
│   └── sample_2.xml
├── rules/                  # Business rules
│   └── rules.json
├── engine/                 # Core modules
│   ├── data_input.py       # XML extraction
│   ├── condition_parser.py # Safe evaluation
│   ├── template_renderer.py# Message templating
│   └── credit_rule_engine.py # Rule evaluation
│   └── output_aggregator.py
├── output/                 # Report outputs
├── logs/                   # Log files
├── main.py                 # Entry point
└── README.md              # This file
```

---

## 🔧 Configuration

### Rules (`rules/rules.json`)

Define credit risk rules with conditions and recommendations:

```json
{
  "label": "🟠 Missed Payments",
  "compound_type": "Serious Delinquency",
  "condition": "payment_conduct_code >= 3",
  "template": "Your {{Facility}} with {{Lender_Type}} has...",
  "recommendation": "Contact your lender immediately...",
  "priority": "Critical"
}
```

**Available Variables:**
- Loan-level: `creditutilizationratio`, `payment_conduct_code`, `balance`, `limit`
- Portfolio: `numberofloans`, `legal_cases_active`, `oldest_account_months`
- Full list: See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#available-variables)

---

## 📖 Documentation

- **[Technical Documentation](TECHNICAL_DOCUMENTATION.md)** - Detailed module documentation
- **[Rule Configuration Guide](docs/RULE_CONFIGURATION.md)** - How to add/modify rules
- **[API Reference](docs/API_REFERENCE.md)** - Function signatures and examples

---

## 🎯 Use Cases

### Credit Risk Assessment
Automatically flag high-risk accounts with serious delinquencies, legal cases, or high utilization.

### Customer Advisory
Generate personalized recommendations for customers to improve credit scores.

### Portfolio Monitoring
Track credit health trends across customer portfolios with aggregate insights.

### Lending Decisions
Support underwriting decisions with structured credit behavior analysis.

---

## 🧪 Testing

```bash
# Test with sample reports
python main.py data/sample_xml.xml
python main.py data/sample_2.xml

# Expected output: 6-9 insights per report
```

**Sample Reports:**
- `sample_xml.xml`: Poor credit (Score 385, legal case, delinquencies)
- `sample_2.xml`: Fair credit (Score 506, mixed payment history)

---

## 🔒 Security

- **Safe Evaluation**: Uses asteval (no `exec`/`eval`)
- **Input Validation**: XML schema validation
- **No Data Storage**: Processes data in-memory only
- **Audit Trail**: Detailed logging of all operations

---

## 🐛 Troubleshooting

### Rule Not Triggering?
```python
# Test condition directly
from engine.condition_parser import ConditionParser
parser = ConditionParser(debug=True)
result = parser.evaluate("your_condition", record)
```

### Missing Variables?
Check `condition_parser.py` DEFAULT_VALUES or add to `template_renderer.py` defaults.

### Extraction Issues?
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**More Help:** See [Troubleshooting Guide](TECHNICAL_DOCUMENTATION.md#troubleshooting)

---

## 📈 Roadmap

- [ ] Support for additional file formats (PDF, CSV)
- [ ] Machine learning-based risk scoring
- [ ] Historical trend analysis
- [ ] REST API interface
- [ ] Web dashboard

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Code Standards:**
- Python 3.8+ syntax
- Type hints for function signatures
- Docstrings for all public methods
- Unit tests for new features

---

## 📄 License

Proprietary - Copyright © 2025 CTOS Data Systems Sdn Bhd

Unauthorized copying, modification, or distribution is prohibited.

---

## 🙏 Acknowledgments

- CTOS Data Systems for credit report specifications
- Bank Negara Malaysia for CCRIS standards
- Python community for excellent libraries (Jinja2, asteval)

---