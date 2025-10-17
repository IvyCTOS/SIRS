# Credit Behavior Insight Engine

A rule-based system for analyzing CTOS credit report data and generating personalized financial guidance and advice.

## 🎯 Project Overview

This engine analyzes credit report data to:
- Detect financial behaviors based on predefined rules
- Generate personalized insights
- Provide educational recommendations
- Maintain compliance with financial advisory regulations

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- pip package manager

### Installation
```bash
# Clone the repository
git clone [repository-url]

# Navigate to project directory
cd SIRS

# Install required packages
pip install -r requirements.txt
```

## 📦 Project Structure
```
credit_insight_engine/
├── data/                  # Sample input files
├── rules/                 # JSON/YAML rule definitions
├── engine/               
│   ├── data_input.py     # PDF parsing and data normalization
│   ├── rule_engine.py    # Core rule evaluation logic
│   └── condition_parser.py # Safe condition evaluation
├── output/                # Generated reports
├── tests/                 # Unit tests
└── main.py               # Entry point
```

## 🛠️ Usage

```python
from engine.rule_engine import RuleEngine
from engine.condition_parser import ConditionParser

# Initialize the engine
rule_engine = RuleEngine('rules/rules.json')

# Process credit report data
insights = rule_engine.process_data(credit_data)
```

## 🧪 Testing

Run the test suite:
```bash
python -m unittest discover tests
```

## 📝 Documentation

Detailed documentation is available in the `docs` folder:
- [Project Requirements](docs/prp_base.md)
- [Implementation Plan](docs/implementation/implementation_plan.md)
- [Data Input Module](docs/implementation/data_input.md)
- [Rule Engine](docs/implementation/rule_engine.md)
- [Condition Parser](docs/implementation/condition_parser.md)

## 🔒 Compliance

This system:
- Avoids making specific financial product recommendations
- Provides educational guidance only
- Maintains data privacy and security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.