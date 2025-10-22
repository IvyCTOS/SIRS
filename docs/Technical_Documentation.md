# CTOS Credit Insight Engine - Technical Documentation

**Version:** 2.1  
**Last Updated:** October 22, 2025  
**Author:** Ivy Chung  
**Status:** Phase 1 MVP

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture & Design](#2-architecture--design)
3. [Installation & Setup](#3-installation--setup)
4. [Core Modules](#4-core-modules)
5. [Data Flow & Processing](#5-data-flow--processing)
6. [Configuration Management](#6-configuration-management)
7. [Rule Development Guide](#7-rule-development-guide)

---

## 1. System Overview

### 1.1 Purpose

The **CTOS Credit Insight Engine** is an intelligent credit analysis system that:

- 📥 **Ingests** XML credit reports from CTOS
- 🔍 **Analyzes** credit behavior patterns
- 🎯 **Evaluates** 24+ predefined risk rules
- 💡 **Generates** personalized insights and recommendations
- 📊 **Exports** structured reports (console + JSON)

### 1.2 Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **XML Parsing** | Namespace-aware extraction | Handles complex CTOS XML structure |
| **Safe Evaluation** | asteval-based (no exec/eval) | Security-first approach |
| **Template Engine** | Jinja2-powered messages | Personalized, context-aware output |
| **Rule Matching** | Context-aware evaluation | Applies right rules to right data |
| **Multi-Severity** | 5-level classification | Clear priority and urgency |
| **Extensible** | JSON-based rules | Easy to add/modify without code changes |

### 1.3 Supported Data Sources

```
┌─────────────────────────────────────────┐
│         CTOS XML Report                 │
├─────────────────────────────────────────┤
│ ✓ CCRIS (Bank Negara Malaysia)         │
│   - Loan accounts                      │
│   - Payment conduct history            │
│   - Credit applications                │
│                                        │
│ ✓ Legal Records (Sections D1-D4)       │
│   - Bankruptcy proceedings             │
│   - Summons and civil suits            │
│   - Director winding-up cases          │
│                                        │
│ ✓ Trade References (Section E)         │
│   - Overdue accounts                   │
│   - Aging buckets                      │
│   - Reminder letters                   │
│                                        │
│ ✓ FICO Score                           │
│   - Overall credit score (300-850)     │
│   - Contributing factors               │
└─────────────────────────────────────────┘
```

### 1.4 System Capabilities

**What It Does:**
- ✅ Detects payment delinquencies (1-210+ days)
- ✅ Calculates credit utilization ratios
- ✅ Identifies legal risks (summons, bankruptcy)
- ✅ Evaluates credit history length
- ✅ Flags frequent credit applications
- ✅ Recognizes positive payment patterns
- ✅ Assesses account diversity

**What It Doesn't Do:**
- ❌ Real-time credit monitoring (batch processing only)
- ❌ Direct database integration (file-based)
- ❌ Automated lending decisions (advisory only)
- ❌ Credit score calculation (uses existing CTOS score)

---

## 2. Architecture & Design

### 2.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  XML File    │    │  rules.json  │    │  Logs Dir    │    │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
└─────────┼───────────────────┼───────────────────┼─────────────┘
          │                   │                   │
          v                   v                   v
┌────────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  1. Data Input Module (data_input.py)                   │  │
│  │     - XMLParser: Namespace handling                      │  │
│  │     - Extractors: Loans, legal, trade refs              │  │
│  │     - Normalizer: Unified data structure                 │  │
│  └───────────────────────┬─────────────────────────────────┘  │
│                          │                                      │
│                          v                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  2. Rule Engine (credit_rule_engine.py)                 │  │
│  │     - RuleLoader: JSON parsing                           │  │
│  │     - RecordClassifier: Loan vs Aggregate                │  │
│  │     - RuleMatcher: Contextual filtering                  │  │
│  │     - Deduplicator: Unique insights                      │  │
│  └───────────┬─────────────────────┬───────────────────────┘  │
│              │                     │                            │
│              v                     v                            │
│  ┌──────────────────┐  ┌──────────────────────┐              │
│  │ 3. Condition     │  │ 4. Template          │              │
│  │    Parser        │  │    Renderer          │              │
│  │                  │  │                      │              │
│  │ - asteval        │  │ - Jinja2 engine      │              │
│  │ - Type coercion  │  │ - Value formatting   │              │
│  │ - Safe eval      │  │ - Variable defaults  │              │
│  └──────────────────┘  └──────────────────────┘              │
│                          │                                      │
│                          v                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  5. Output Aggregator (output_aggregator.py)           │  │
│  │     - Grouper: By label/severity                         │  │
│  │     - Formatter: Console & JSON                          │  │
│  │     - Sorter: Priority-based ordering                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             v
┌────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   Console    │    │  JSON File   │    │   Logs       │    │
│  │   Report     │    │   Export     │    │   (errors)   │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Patterns Used

#### 2.2.1 Strategy Pattern (Rule Evaluation)

```python
# Different strategies for different record types
class RuleEngine:
    def _should_apply_rule(self, rule, record):
        if "Utilization" in rule['label']:
            return self._is_revolving_credit(record)
        elif "Payment Conduct" in rule['type']:
            return self._is_loan_record(record)
        elif "Legal Risk" in rule['label']:
            return self._is_aggregate_record(record)
```

#### 2.2.2 Template Method Pattern (Data Extraction)

```python
class CTOSReportParser:
    def extract_data_from_xml(self):
        # Template method
        self._parse_xml()
        personal_info = self._extract_personal_info()
        loans = self._extract_loans()
        legal = self._extract_legal_cases()
        return self._normalize(personal_info, loans, legal)
```

#### 2.2.3 Builder Pattern (Report Generation)

```python
aggregator = ConsoleOutputAggregator()
for insight in insights:
    aggregator.add_insight(insight)  # Build step-by-step

report = aggregator.generate_json_report()  # Final build
```

### 2.3 Data Model

```
┌────────────────────────────────────────────────────────┐
│                   Normalized Data                      │
├────────────────────────────────────────────────────────┤
│  {                                                     │
│    "records": [                                        │
│      // LOAN RECORDS (per account)                    │
│      {                                                 │
│        "facility_type": "CRDTCARD",                   │
│        "lender": "Malayan Banking Berhad",            │
│        "balance": 3362.0,                             │
│        "limit": 5000.0,                               │
│        "creditutilizationratio": 67.2,                │
│        "payment_conduct_code": 0,                     │
│        "payment_conduct_all_zero": true,              │
│        "conduct_codes": [0,0,0,0,0,0,0,0,0,0,0,0],   │
│        "date_opened": "28-02-2019",                   │
│        "is_revolving": true,                          │
│        "account_type": "revolving"                    │
│      },                                                │
│      ... more loan records ...                        │
│                                                        │
│      // AGGREGATE RECORD (portfolio-level)            │
│      {                                                 │
│        "numberofloans": 5,                            │
│        "numapplicationslast12months": 1,              │
│        "numpendingapplications": 0,                   │
│        "distinct_account_types": 3,                   │
│        "oldest_account_months": 80,                   │
│        "oldest_account_years": 6.67,                  │
│        "creditutilizationratio": 37.4,                │
│        "trade_ref_amount_overdue": 0.0,               │
│        "legal_cases_active": 0,                       │
│        "legal_cases_settled": 0,                      │
│        "case_types": "",                              │
│        "bankruptcy_active": false,                    │
│        "has_credit_card": true,                       │
│        "has_installment_loan": true,                  │
│        "accounts_per_lender": 2,                      │
│        "lender_name": "Malayan Banking Berhad",       │
│        "secured_loan_ratio": 33.1                     │
│      }                                                 │
│    ],                                                  │
│    "personal_info": {                                  │
│      "name": "NOOR KEDUA",                            │
│      "ic_number": "932213246548",                     │
│      "ctos_score": 506                                │
│    }                                                   │
│  }                                                     │
└────────────────────────────────────────────────────────┘
```
---

## 3. Installation & Setup

### 3.1 Dependencies

```bash
# Core dependencies
pip install jinja2==3.1.2      # Template engine
pip install asteval==0.9.31    # Safe evaluation

# Optional (development)
pip install pytest==7.4.0      # Testing
pip install black==23.7.0      # Code formatting
pip install pylint==2.17.4     # Linting
```

### 3.2 Installation Steps

```bash
# 1. Clone repository
git clone <repository_url>
cd credit_insight_engine

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python main.py data/sample_xml.xml

# Expected output: Report with 7 insights
```

### 3.3 Project Structure Setup

```bash
credit_insight_engine/
├── data/                      # Input XML files
│   ├── sample_xml.xml
│   └── sample_2.xml
├── rules/                     # Configuration
│   └── rules.json
├── engine/                    # Core modules
│   ├── __init__.py
│   ├── data_input.py
│   ├── condition_parser.py
│   ├── template_renderer.py
│   └── credit_rule_engine.py
│   └── output_aggregator.py
├── output/                    # Output 
│   ├── sample_output.json
├── logs/                      # Generated logs
├── output/                    # Generated reports
├── tests/                     # Unit tests
│   ├── test_parser.py
│   ├── test_rules.py
│   └── test_output.py
├── docs/                      # Documentation
│   ├── TECHNICAL_DOCUMENTATION.md
│   └── API_REFERENCE.md
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .gitignore
└── README.md
```

### 3.4 Configuration

**1. Logging Configuration:**

```python
# In main.py or config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/engine.log'),
        logging.StreamHandler()
    ]
)
```

**2. Environment Variables (optional):**

## 4. Core Modules

## 4.1 Data Input Module (`engine/data_input.py`)

### Purpose
Extracts and normalizes credit data from CTOS XML reports.

### Class Diagram

```
┌─────────────────────────────────────┐
│      CTOSReportParser               │
├─────────────────────────────────────┤
│ - xml_file: str                     │
│ - root: ElementTree                 │
│ - ns: Dict[str, str]               │
│ - logger: Logger                    │
├─────────────────────────────────────┤
│ + __init__(xml_file)                │
│ + extract_data_from_xml() → Dict   │
│                                     │
│ # Private Methods                   │
│ - _extract_name() → str            │
│ - _extract_ic() → str              │
│ - _extract_ctos_score() → int      │
│ - _extract_loans_from_ccris() → [] │
│ - _parse_account() → Dict          │
│ - _extract_legal_cases() → []      │
│ - _extract_trade_references() → [] │
│ - _calculate_oldest_account() → int│
└─────────────────────────────────────┘
```

### Key Methods

#### 4.1.1 `extract_data_from_xml()`

**Purpose:** Main orchestrator method that extracts all data.

**Flow:**
```python
def extract_data_from_xml(self) -> Dict:
    # 1. Parse XML file
    tree = ET.parse(self.xml_file)
    self.root = tree.getroot()
    
    # 2. Extract personal info
    name = self._extract_name()
    ic_number = self._extract_ic()
    ctos_score = self._extract_ctos_score()
    
    # 3. Extract accounts
    loans = self._extract_loans_from_ccris()
    
    # 4. Extract legal records
    legal_cases = self._extract_legal_cases()
    
    # 5. Calculate aggregates
    total_outstanding = sum(l['balance'] for l in loans)
    creditutilizationratio = self._calculate_revolving_util(loans)
    
    # 6. Return structured data
    return {
        'name': name,
        'ic_number': ic_number,
        'ctos_score': ctos_score,
        'loans': loans,
        'legal_cases': legal_cases,
        'total_outstanding': total_outstanding,
        'creditutilizationratio': creditutilizationratio,
        ...
    }
```

**Error Handling:**
```python
try:
    extracted_data = extract_data_from_xml(xml_file)
except FileNotFoundError:
    logger.error(f"XML file not found: {xml_file}")
except ET.ParseError as e:
    logger.error(f"XML parsing error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

#### 4.1.2 `_parse_account()`

**Purpose:** Parses a single loan account from XML.

**Implementation:**
```python
def _parse_account(self, account_elem, is_special_attention=False) -> Dict:
    # Extract basic account info
    approval_date = self._get_text(account_elem, 'ns:approval_date')
    
    # Get lender name (text content, not attribute!)
    lender_type_elem = account_elem.find('ns:lender_type', self.ns)
    lender = lender_type_elem.text.strip() if lender_type_elem is not None else 'Unknown'
    
    limit = float(self._get_text(account_elem, 'ns:limit', '0'))
    
    # Extract facility details
    sub_account = account_elem.find('.//ns:sub_account', self.ns)
    facility_elem = sub_account.find('ns:facility', self.ns)
    facility_type = facility_elem.get('code', 'UNKNOWN')
    
    # Extract payment conduct history (last 12 months)
    cr_positions = sub_account.findall('.//ns:cr_position', self.ns)
    conduct_codes = []
    
    for pos in cr_positions[:12]:
        inst_arrears = int(self._get_text(pos, 'ns:inst_arrears', '0'))
        conduct_code = min(inst_arrears, 8)  # Cap at 8
        conduct_codes.append(conduct_code)
    
    # Pad to 12 months
    while len(conduct_codes) < 12:
        conduct_codes.append(0)
    
    payment_conduct_code = max(conduct_codes)
    payment_conduct_all_zero = all(code == 0 for code in conduct_codes)
    
    # Get latest balance
    latest_position = cr_positions[0]
    balance = float(self._get_text(latest_position, 'ns:balance', '0'))
    
    # Calculate utilization
    utilization = (balance / limit * 100) if limit > 0 else 0
    
    return {
        'facility_type': facility_type,
        'lender': lender,
        'balance': balance,
        'limit': limit,
        'utilization': utilization,
        'date_opened': approval_date,
        'payment_conduct_code': payment_conduct_code,
        'payment_conduct_all_zero': payment_conduct_all_zero,
        'conduct_codes': conduct_codes,
        'is_special_attention': is_special_attention
    }
```

**XML Structure Example:**
```xml
<account>
  <approval_date>28-02-2019</approval_date>
  <lender_type code="Maybank">Malayan Banking Berhad</lender_type>
  <limit>5000</limit>
  <sub_accounts>
    <sub_account>
      <facility code="CRDTCARD">Credit Card</facility>
      <cr_positions>
        <cr_position>
          <balance>3362</balance>
          <inst_arrears>0</inst_arrears>
          <position_date>31-07-2025</position_date>
        </cr_position>
        <!-- ... more months ... -->
      </cr_positions>
    </sub_account>
  </sub_accounts>
</account>
```

#### 4.1.3 Normalization (`normalize_data()`)

**Purpose:** Converts extracted data into engine-ready format.

**Key Transformations:**

1. **Loan Records:**
```python
for loan in loans:
    facility_type = loan['facility_type']
    is_revolving = facility_type in ['CRDTCARD', 'OVRDRAFT']
    
    loan_records.append({
        'Facility': _map_facility_type(facility_type),
        'facility_type': facility_type,
        'loantype': _map_facility_type(facility_type),
        'Lender_Type': loan['lender'],
        'lendertype': loan['lender'],
        'balance': loan['balance'],
        'limit': loan['limit'],
        'creditutilizationratio': loan['utilization'] if is_revolving else 0,
        'payment_conduct_code': loan['payment_conduct_code'],
        'payment_conduct_all_zero': loan['payment_conduct_all_zero'],
        'is_revolving': is_revolving,
        'account_type': 'revolving' if is_revolving else 'installment'
    })
```

2. **Aggregate Record:**
```python
# Calculate lender concentration
from collections import Counter
lender_counts = Counter(loan['lender'] for loan in loans)
accounts_per_lender = max(lender_counts.values()) if lender_counts else 0
lender_name = max(lender_counts, key=lender_counts.get) if lender_counts else ''

# Calculate secured loan ratio
secured_balance = sum(
    loan['balance'] 
    for loan in loans 
    if loan['facility_type'] in ['HSLNFNCE', 'PCPASCAR']
)
total_balance = sum(loan['balance'] for loan in loans)
secured_loan_ratio = (secured_balance / total_balance * 100) if total_balance > 0 else 0

# Build case_types for legal cases
active_cases = [c for c in legal_cases if not c['is_settled']]
case_types = ', '.join(c['case_type'] for c in active_cases) if active_cases else ''

aggregate_record = {
    'numberofloans': len(loans),
    'numapplicationslast12months': extracted_data['numapplicationslast12months'],
    'numpendingapplications': extracted_data['numpendingapplications'],
    'distinct_account_types': len(set(l['facility_type'] for l in loans)),
    'oldest_account_months': extracted_data['oldest_account_months'],
    'oldest_account_years': extracted_data['oldest_account_months'] / 12,
    'creditutilizationratio': extracted_data['creditutilizationratio'],
    'legal_cases_active': len([c for c in legal_cases if not c['is_settled']]),
    'legal_cases_settled': len([c for c in legal_cases if c['is_settled']]),
    'case_types': case_types,
    'bankruptcy_active': any('BANKRUPTCY' in c['case_type'] and not c['is_settled'] for c in legal_cases),
    'accounts_per_lender': accounts_per_lender,
    'lender_name': lender_name,
    'secured_loan_ratio': secured_loan_ratio,
    'has_credit_card': any(l['facility_type'] == 'CRDTCARD' for l in loans),
    'has_installment_loan': any(l['facility_type'] in ['HSLNFNCE', 'PCPASCAR', 'OTLNFNCE'] for l in loans),
    ...
}
```

**Output Structure:**
```python
{
    'records': [
        loan_record_1,
        loan_record_2,
        ...,
        aggregate_record
    ],
    'personal_info': {
        'name': 'NOOR KEDUA',
        'ic_number': '93xxxxxx',
        'ctos_score': 506
    }
}
```

### Best Practices

✅ **DO:**
- Always use namespaces when accessing XML elements
- Extract full lender names (text content, not code attribute)
- Cap conduct codes at 8 (CCRIS standard)
- Handle empty/missing values gracefully
- Log extraction progress

❌ **DON'T:**
- Don't assume XML structure (always check for None)
- Don't skip error handling
- Don't hardcode namespaces
- Don't ignore special attention accounts

---

## 4.2 Condition Parser (`engine/condition_parser.py`)

### Purpose
Safely evaluates boolean conditions using asteval (no `exec`/`eval` vulnerabilities).

### Architecture

```
┌────────────────────────────────────────┐
│      ConditionParser                   │
├────────────────────────────────────────┤
│  Input: "balance > 5000 and limit > 0" │
│         + {balance: 6000, limit: 10000}│
├────────────────────────────────────────┤
│  1. Normalize                          │
│     - Convert true/false → True/False  │
│     - Clean whitespace                 │
│                                        │
│  2. Prepare Data                       │
│     - Add defaults for missing vars    │
│     - Type coercion (str→float/int)    │
│                                        │
│  3. Evaluate (asteval)                 │
│     - Load variables into symtable     │
│     - Execute condition (max 100ms)    │
│     - Return boolean result            │
├────────────────────────────────────────┤
│  Output: True                          │
└────────────────────────────────────────┘
```

### Implementation Details

#### 4.2.1 Initialization

```python
class ConditionParser:
    def __init__(self, debug: bool = False):
        # Initialize asteval with security settings
        self.aeval = Interpreter(
            use_numpy=False,     # Don't load numpy (security)
            minimal=True,        # Minimal symbol table
            max_time=0.1        # Max 100ms per evaluation
        )
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Statistics tracking
        self.stats = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'missing_variables': {}
        }
```

#### 4.2.2 Default Values

**Complete variable list:**

```python
DEFAULT_VALUES = {
    # Loan-Level Numeric
    'creditutilizationratio': 0.0,
    'balance': 0.0,
    'limit': 0.0,
    'payment_conduct_code': 0,
    'mon_arrears': 0,
    'inst_arrears': 0,
    'utilization': 0.0,
    
    # Portfolio/Aggregate Numeric
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
    
    # Trade Reference
    'trade_ref_amount_overdue': 0.0,
    'trade_ref_reminder_count': 0,
    
    # Legal
    'legal_cases_settled': 0,
    'legal_cases_active': 0,
    'director_windingup_company': 0,
    
    # Boolean
    'has_credit_card': False,
    'has_installment_loan': False,
    'bankruptcy_active': False,
    'payment_conduct_all_zero': False,
    'is_revolving': False,
    'is_secured': False,
    
    # String
    'facility_type': '',
    'loantype': '',
    'lendertype': '',
    'case_details': '',
    'case_types': '',
    'company_name': '',
    'lender_name': '',
    'aging_bucket': '',
    
    # Personal Info (for templates)
    'Facility': '',
    'Lender_Type': '',
    'name': '',
    'ic_number': '',
    'ctos_score': 0
}
```

#### 4.2.3 Evaluation Process

```python
def evaluate(self, condition: str, data: Dict[str, Any]) -> bool:
    self.stats['total_evaluations'] += 1
    
    try:
        # Step 1: Normalize condition syntax
        normalized = self._normalize_condition(condition)
        # "creditutilizationratio > 80 and has_credit_card == true"
        # becomes:
        # "creditutilizationratio > 80 and has_credit_card == True"
        
        # Step 2: Prepare data with defaults and type coercion
        prepared = self._prepare_data(data)
        # {
        #   'creditutilizationratio': 85.5,  # float coercion
        #   'has_credit_card': True,          # bool coercion
        #   'balance': 0.0,                   # default added
        #   ...
        # }
        
        # Step 3: Load variables into asteval interpreter
        for key, value in prepared.items():
            self.aeval.symtable[key] = value
        
        # Step 4: Evaluate condition
        result = self.aeval(normalized)
        
        # Step 5: Convert to boolean
        bool_result = bool(result)
        self.stats['successful_evaluations'] += 1
        
        return bool_result
        
    except NameError as e:
        # Variable not found (shouldn't happen with defaults)
        self.logger.error(f"NameError: {e}")
        self.stats['failed_evaluations'] += 1
        return False
        
    except SyntaxError as e:
        # Invalid Python syntax in condition
        self.logger.error(f"SyntaxError in condition: {e}")
        raise ParserError(f"Invalid condition syntax: {str(e)}")
        
    except Exception as e:
        # Other errors
        self.logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ParserError(f"Failed to evaluate: {str(e)}")
```

#### 4.2.4 Type Coercion

**Automatic type conversion:**

```python
def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    prepared = self.DEFAULT_VALUES.copy()
    
    # Override with actual data
    for key, value in data.items():
        if value is not None:
            prepared[key] = value
    
    # Numeric fields → float
    numeric_fields = [
        'creditutilizationratio', 'balance', 'limit', 
        'secured_loan_ratio', 'oldest_account_years'
    ]
    for field in numeric_fields:
        if field in prepared:
            try:
                prepared[field] = float(prepared[field])
            except (ValueError, TypeError):
                prepared[field] = 0.0
    
    # Integer fields → int
    integer_fields = [
        'payment_conduct_code', 'numberofloans', 
        'legal_cases_active', 'ctos_score'
    ]
    for field in integer_fields:
        if field in prepared:
            try:
                prepared[field] = int(float(prepared[field]))
            except (ValueError, TypeError):
                prepared[field] = 0
    
    # Boolean fields → bool
    boolean_fields = [
        'has_credit_card', 'bankruptcy_active', 
        'payment_conduct_all_zero'
    ]
    for field in boolean_fields:
        if field in prepared:
            prepared[field] = bool(prepared[field])
    
    return prepared
```

### Usage Examples

**Example 1: Simple Comparison**
```python
parser = ConditionParser()

result = parser.evaluate(
    "creditutilizationratio > 80",
    {"creditutilizationratio": 85.5}
)
# Returns: True
```

**Example 2: Compound Condition**
```python
result = parser.evaluate(
    "payment_conduct_code >= 1 and payment_conduct_code <= 2",
    {"payment_conduct_code": 2}
)
# Returns: True
```

**Example 3: Boolean Check**
```python
result = parser.evaluate(
    "has_credit_card == false and has_installment_loan == true",
    {"has_credit_card": False, "has_installment_loan": True}
)
# Returns: True
```

**Example 4: Missing Variable (uses default)**
```python
result = parser.evaluate(
    "balance > 5000",
    {}  # Empty data
)
# Uses default: balance = 0.0
# Returns: False
```

### Testing Conditions

**Use the test_condition method for debugging:**

```python
parser = ConditionParser(debug=True)

result = parser.test_condition(
    "creditutilizationratio > 50 and creditutilizationratio <= 80",
    {"creditutilizationratio": 65}
)

print(result)
# {
#     'success': True,
#     'result': True,
#     'condition': 'creditutilizationratio > 50 and creditutilizationratio <= 80',
#     'normalized_condition': 'creditutilizationratio > 50 and creditutilizationratio <= 80',
#     'required_variables': {'creditutilizationratio'},
#     'variable_values': {'creditutilizationratio': 65.0},
#     'missing_variables': set(),
#     'used_defaults': False,
#     'error': None
# }
```

---

## 4.3 Template Renderer (`engine/template_renderer.py`)

### Purpose
Renders personalized messages using Jinja2 templates with automatic value formatting.

### Key Features

```
┌─────────────────────────────────────────┐
│     Template Renderer Features          │
├─────────────────────────────────────────┤
│ ✓ Jinja2 template engine                │
│ ✓ Variable substitution                 │
│ ✓ Automatic number formatting           │
│ ✓ Custom filters (currency, %)          │
│ ✓ Missing variable detection            │
│ ✓ Default value injection               │
│ ✓ StrictUndefined mode                  │
└─────────────────────────────────────────┘
```

### Implementation

#### 4.3.1 Initialization

```python
class TemplateRenderer:
    def __init__(self, templates_file: str = None):
        # Initialize Jinja2 with strict mode
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            undefined=StrictUndefined  # Raises error for missing vars
        )
        
        # Register custom filters
        self._register_filters()
        
        # Load template library (optional)
        self.templates = {}
        if templates_file:
            self.load_templates(templates_file)
        
        self.logger = logging.getLogger(__name__)
```

#### 4.3.2 Custom Filters

```python
def _register_filters(self):
    """Register custom Jinja2 filters"""
    
    # Currency formatting
    def format_currency(value: float) -> str:
        try:
            return f"RM {float(value):,.2f}"
        except (ValueError, TypeError):
            return "RM 0.00"
    
    # Percentage formatting
    def format_percentage(value: float) -> str:
        try:
            return f"{float(value):.1f}%"
        except (ValueError, TypeError):
            return "0.0%"
    
    # Date formatting
    def format_date(value: str) -> str:
        try:
            date = datetime.strptime(value, "%Y-%m-%d")
            return date.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return value
    
    # Register
    self.env.filters['currency'] = format_currency
    self.env.filters['percentage'] = format_percentage
    self.env.filters['date'] = format_date
```

**Usage in templates:**
```jinja2
Balance: {{ balance|currency }}
# Output: "Balance: RM 5,000.50"

Utilization: {{ creditutilizationratio|percentage }}
# Output: "Utilization: 67.2%"

Date: {{ approval_date|date }}
# Output: "Date: 28/02/2019"
```

#### 4.3.3 Value Formatting

**Automatic formatting based on field name:**

```python
def _format_values(self, data: Dict[str, Any]) -> Dict[str, str]:
    formatted = {}
    
    for key, value in data.items():
        if value is None:
            formatted[key] = ''
            
        elif isinstance(value, float):
            # Utilization/ratios → 1 decimal
            if key in ['creditutilizationratio', 'utilization']:
                formatted[key] = f"{value:.1f}"
            
            # Amounts → 2 decimals with commas
            elif key in ['balance', 'limit']:
                formatted[key] = f"{value:,.2f}"
            
            # Percentages → 1 decimal
            elif 'ratio' in key.lower() or 'percentage' in key.lower():
                formatted[key] = f"{value:.1f}"
            
            # Other amounts
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
```

**Examples:**
```python
# Input
data = {
    'balance': 5000.5,
    'creditutilizationratio': 67.234,
    'secured_loan_ratio': 75.5,
    'trade_ref_amount_overdue': 6000
}

# After formatting
{
    'balance': '5,000.50',
    'creditutilizationratio': '67.2',
    'secured_loan_ratio': '75.5',
    'trade_ref_amount_overdue': '6,000.00'
}
```

#### 4.3.4 Template Rendering

```python
def render_template(self, template_string: str, data: Dict[str, Any]) -> str:
    try:
        # Validate required variables
        is_valid, missing_vars = self._validate_data(template_string, data)
        
        if not is_valid:
            self.logger.warning(f"Missing variables: {missing_vars}")
            # Add defaults for missing variables
            data = self._add_default_values(data)
        
        # Format numeric values
        formatted_data = self._format_values(data)
        
        # Create and render template
        template = self.env.from_string(template_string)
        result = template.render(**formatted_data)
        
        return result
        
    except UndefinedError as e:
        # Specific error for missing variables
        self.logger.error(f"Undefined variable: {str(e)}")
        self.logger.error(f"Template: {template_string}")
        self.logger.error(f"Available data: {list(data.keys())}")
        raise TemplateError(f"Missing required variable: {str(e)}")
        
    except Exception as e:
        self.logger.error(f"Template rendering error: {str(e)}")
        raise TemplateError(f"Failed to render template: {str(e)}")
```

### Usage Examples

**Example 1: Basic Substitution**
```python
renderer = TemplateRenderer()

template = "Your {{Facility}} with {{Lender_Type}} has {{creditutilizationratio}}% utilization."

data = {
    'Facility': 'Credit Card',
    'Lender_Type': 'Maybank',
    'creditutilizationratio': 67.2
}

message = renderer.render_template(template, data)
# Output: "Your Credit Card with Maybank has 67.2% utilization."
```

**Example 2: With Filters**
```python
template = "Balance: {{balance|currency}}, Ratio: {{ratio|percentage}}"

data = {
    'balance': 5000.50,
    'ratio': 67.234
}

message = renderer.render_template(template, data)
# Output: "Balance: RM 5,000.50, Ratio: 67.2%"
```

**Example 3: Conditional**
```python
template = """
Your account has {{balance|currency}} outstanding.
{% if balance > 5000 %}
This is above the recommended limit.
{% endif %}
"""

data = {'balance': 6000}

message = renderer.render_template(template, data)
# Output includes conditional message
```

---

## 4.4 Rule Engine (`engine/credit_rule_engine.py`)

### Purpose
Core logic that evaluates rules against records and generates insights.

### Architecture

```
┌──────────────────────────────────────────────────────┐
│              RuleEngine Workflow                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. Load Rules (from rules.json)                    │
│     ↓                                                │
│  2. For each record:                                │
│     ↓                                                │
│  3. Detect Record Type                              │
│     ├─→ Loan Record (has facility_type)            │
│     └─→ Aggregate Record (has numberofloans)        │
│     ↓                                                │
│  4. Filter Applicable Rules                         │
│     ├─→ Utilization rules → Revolving credit only   │
│     ├─→ Payment rules → All loans                   │
│     └─→ Legal/Trade → Aggregate only                │
│     ↓                                                │
│  5. Evaluate Condition (ConditionParser)            │
│     ↓                                                │
│  6. Render Template (TemplateRenderer)              │
│     ↓                                                │
│  7. Deduplicate Insights                            │
│     ↓                                                │
│  8. Return Matched Insights                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Key Methods

#### 4.4.1 `_detect_record_type()`

```python
def _detect_record_type(self, record: Dict[str, Any]) -> str:
    """
    Detect if record is loan-level or aggregate/portfolio-level
    
    Returns:
        'loan' or 'aggregate'
    """
    # Aggregate indicators (most reliable)
    aggregate_indicators = [
        'numberofloans',
        'numapplicationslast12months',
        'distinct_account_types',
        'trade_ref_amount_overdue',
        'legal_cases_settled',
        'legal_cases_active'
    ]
    
    if any(indicator in record for indicator in aggregate_indicators):
        return 'aggregate'
    
    # Loan indicators
    if 'facility_type' in record or 'loantype' in record:
        return 'loan'
    
    return 'loan'  # Default
```

#### 4.4.2 `_should_apply_rule()` - CRITICAL LOGIC

```python
def _should_apply_rule(self, rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
    """
    CRITICAL: Determines if a rule should be applied to a record
    
    Rules are contextual - they apply only to appropriate record types.
    """
    label = rule.get('label', '')
    compound_type = rule.get('compound_type', '')
    condition = rule.get('condition', '')
    
    record_type = self._detect_record_type(record)
    is_loan = (record_type == 'loan')
    is_aggregate = (record_type == 'aggregate')
    
    # RULE 1: Utilization rules → Revolving credit loans ONLY
    if 'Utilization' in label or 'Utilization' in compound_type:
        if not is_loan:
            return False
        if not self._is_revolving_credit(record):
            return False
        return True
    
    # RULE 2: Payment conduct → ALL LOAN RECORDS
    if ('Missed Payments' in label or 
        'Payment Conduct' in compound_type or
        'payment_conduct_code' in condition):
        return is_loan
    
    # RULE 3: Portfolio-level rules → Aggregate ONLY
    portfolio_rules = [
        '🟡 Frequent Applications',
        '🟡 Pending Applications',
        '🟣 Thin Credit File',
        '⚪ Short Credit History',
        '🔵 Lender Concentration',
        '🟢 Long Credit History',
        '🟢 Low Application Rate'
    ]
    if any(portfolio_label in label for portfolio_label in portfolio_rules):
        return is_aggregate
    
    # RULE 4: Trade reference → Aggregate ONLY
    if '⚪ Trade Reference' in label or 'trade_ref' in condition:
        return is_aggregate
    
    # RULE 5: Legal → Aggregate ONLY
    if '⚫ Legal Risk' in label or 'legal_cases' in condition:
        return is_aggregate
    
    # RULE 6: Positive patterns
    if '🟢' in label:
        if 'Payment History' in compound_type:
            return is_loan  # Per-loan perfect history
        if 'Utilization' in label:
            return is_loan and self._is_revolving_credit(record)
        if 'Credit History' in label or 'Application' in label:
            return is_aggregate
    
    # Default: apply to loan records
    return is_loan
```

**Why this matters:**

```
❌ WRONG: Applying "High Utilization" to aggregate record
   - Aggregate has overall utilization, not per-account
   
✅ CORRECT: Applying "High Utilization" to CRDTCARD loan
   - Individual credit card can have high utilization

❌ WRONG: Applying "Legal Risk" to loan record
   - Legal cases are person-level, not loan-level
   
✅ CORRECT: Applying "Legal Risk" to aggregate
   - One person has legal cases (affects all loans)
```

#### 4.4.3 `process_data()` - Main Workflow

```python
def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process normalized data and return matched insights
    
    Args:
        data: {
            'records': [loan1, loan2, ..., aggregate],
            'personal_info': {name, ic, score}
        }
    
    Returns:
        List of matched insights
    """
    matches = []
    seen_insights = set()  # For deduplication
    
    records = data.get('records', [])
    personal_info = data.get('personal_info', {})
    
    self.logger.info(f"Processing {len(records)} records")
    
    for record_idx, record in enumerate(records):
        record_type = self._detect_record_type(record)
        self.logger.debug(f"Record {record_idx}: type={record_type}")
        
        # Build rendering context (merge personal_info + record)
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
                
                # Evaluate condition
                condition = rule.get('condition', '')
                if not condition:
                    continue
                
                if self.parser.evaluate(condition, record):
                    # Rule matched! Generate insight
                    
                    # Render template
                    template = rule.get('template', '')
                    template_with_aliases = self._apply_template_aliases(template)
                    message = self.renderer.render_template(
                        template_with_aliases, 
                        render_ctx
                    )
                    
                    # Deduplication key
                    insight_key = f"{rule['label']}:{rule['compound_type']}:{message}"
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
                    
                    # Build insight
                    insight = {
                        'label': rule.get('label', ''),
                        'type': rule.get('compound_type', ''),
                        'message': message,
                        'recommendation': rule.get('recommendation', ''),
                        'severity': severity,
                        'priority': priority,
                        'data_source': rule.get('data_source', ''),
                        'record_type': record_type,
                        'data': record  # Include original data
                    }
                    
                    matches.append(insight)
                    
            except Exception as e:
                self.logger.error(
                    f"Error evaluating rule {rule.get('label')} "
                    f"on record {record_idx}: {e}"
                )
                continue
        
        self.logger.debug(
            f"Record {record_idx}: evaluated {rules_evaluated} rules, "
            f"skipped {rules_skipped} rules"
        )
    
    self.logger.info(
        f"Found {len(matches)} unique insights from {len(records)} records"
    )
    
    return matches
```

### Rule Matching Examples

**Example 1: High Utilization (Loan-Level)**

```python
# Rule
{
    "label": "🔴 High Utilization",
    "condition": "creditutilizationratio > 80",
    "template": "Your {{Facility}} with {{Lender_Type}} has {{creditutilizationratio}}% utilization"
}

# Loan Record (CRDTCARD)
{
    "facility_type": "CRDTCARD",
    "lender": "Maybank",
    "creditutilizationratio": 85.5,
    "balance": 4275,
    "limit": 5000
}

# Result: MATCH ✅
# - Record type: loan
# - Is revolving: True (CRDTCARD)
# - Condition: 85.5 > 80 → True
# - Insight generated with lender name
```

**Example 2: Legal Risk (Aggregate-Level)**

```python
# Rule
{
    "label": "⚫ Legal Risk",
    "condition": "legal_cases_active > 0",
    "template": "You have {{legal_cases_active}} active legal case(s): {{case_types}}"
}

# Aggregate Record
{
    "numberofloans": 5,
    "legal_cases_active": 1,
    "case_types": "SUMMONS - DIRECTED TO"
}

# Result: MATCH ✅
# - Record type: aggregate
# - Condition: 1 > 0 → True
# - Insight generated with case details
```

**Example 3: Payment Conduct (Loan-Level)**

```python
# Rule
{
    "label": "🟠 Missed Payments",
    "condition": "payment_conduct_code >= 3",
    "template": "Your {{Facility}} with {{Lender_Type}} has serious delinquency (code {{payment_conduct_code}})"
}

# Loan Record (PTPTN)
{
    "facility_type": "OTLNFNCE",
    "lender": "Perbadanan Tabung Pendidikan Tinggi Nasional (PTPTN)",
    "payment_conduct_code": 8,
    "balance": 15397
}

# Result: MATCH ✅
# - Record type: loan
# - Condition: 8 >= 3 → True
# - Full lender name included in message
```

---

## 5. Data Flow & Processing

### 5.1 Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: INPUT                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  sample_xml.xml (CTOS Credit Report)                           │
│  ├─ Personal Info (Name, IC, Score)                           │
│  ├─ Accounts (5 loan accounts)                                │
│  ├─ Legal Cases (1 summons)                                   │
│  └─ Applications (1 approved)                                  │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: EXTRACTION (data_input.py)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Parse XML → Extract Data                                      │
│  ├─ Name: "NOOR KEDUA"                                        │
│  ├─ IC: "93xxxxxxx"                                        │
│  ├─ Score: 506                                                │
│  ├─ Loans: [                                                  │
│  │   {type: CRDTCARD, lender: Maybank, bal: 3362, ...},     │
│  │   {type: PCPASCAR, lender: CIMB, bal: 10011, ...},       │
│  │   {type: OTLNFNCE, lender: PTPTN, bal: 15397, ...},      │
│  │   {type: CRDTCARD, lender: HSBC, bal: 1318, ...},        │
│  │   {type: BUYNPAYL, lender: StanChart, bal: 137, ...}     │
│  │ ]                                                          │
│  └─ Legal: [{type: SUMMONS, plaintiff: HLIB, ...}]           │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: NORMALIZATION (normalize_data)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Create Loan Records (5)                                        │
│  ├─ Record 1: Maybank CRDTCARD                                │
│  │   {facility_type: CRDTCARD, lender: Maybank,              │
│  │    balance: 3362, limit: 5000, utilization: 67.2,         │
│  │    payment_conduct_code: 0, all_zero: true, ...}          │
│  │                                                            │
│  ├─ Record 2: CIMB Car Loan                                  │
│  ├─ Record 3: PTPTN Education Loan                           │
│  ├─ Record 4: HSBC Credit Card                               │
│  └─ Record 5: StanChart BNPL                                 │
│                                                                 │
│  Create Aggregate Record (1)                                    │
│  └─ Record 6: Portfolio Summary                               │
│     {numberofloans: 5, oldest_months: 80,                     │
│      legal_cases_active: 0, case_types: "",                   │
│      has_credit_card: true, accounts_per_lender: 2, ...}      │
│                                                                 │
│  Output: {records: [R1, R2, R3, R4, R5, R6],                  │
│           personal_info: {name, ic, score}}                    │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: RULE EVALUATION (credit_rule_engine.py)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For Record 1 (Maybank CRDTCARD):                              │
│  ├─ Test "High Utilization" (67.2 > 80?) → NO                │
│  ├─ Test "Moderate Utilization" (67.2 > 50?) → YES ✓         │
│  │   Insight: "Your Credit Card with Maybank shows 67.2%..."  │
│  ├─ Test "Missed Payments" (code 0 >= 1?) → NO               │
│  ├─ Test "Excellent History" (all_zero?) → YES ✓             │
│  │   Insight: "Your Credit Card with Maybank shows excellent.."│
│  └─ Test "Low Utilization" (67.2 < 30?) → NO                 │
│                                                                 │
│  For Record 2 (CIMB Car Loan):                                 │
│  ├─ Skip "Utilization" rules (not revolving)                  │
│  ├─ Test "Missed Payments" (code 0 >= 1?) → NO               │
│  └─ Test "Excellent History" (all_zero?) → YES ✓             │
│                                                                 │
│  For Record 3 (PTPTN Education):                               │
│  ├─ Test "Serious Delinquency" (code 8 >= 3?) → YES ✓        │
│  │   Insight: "Your Other Term Loan with PTPTN has serious..." │
│  └─ Other rules...                                             │
│                                                                 │
│  For Record 6 (Aggregate):                                     │
│  ├─ Test "Long Credit History" (80 >= 60?) → YES ✓           │
│  │   Insight: "Your credit history spans 6.67 years..."       │
│  ├─ Test "Low Application Rate" (1 <= 1?) → YES ✓            │
│  │   Insight: "You've made 1 application(s) in past year..."  │
│  └─ Test "Legal Risk" (0 > 0?) → NO                           │
│                                                                 │
│  Total Insights: 9                                             │
│  ├─ Critical: 1 (PTPTN delinquency)                           │
│  ├─ High: 1 (HSBC late payments)                              │
│  ├─ Medium: 1 (Maybank utilization)                           │
│  └─ Positive: 6 (excellent histories, long history, low apps) │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: OUTPUT AGGREGATION (output_aggregator.py)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Group by Label:                                               │
│  ├─ 🟠 Moderate Utilization: [1 insight]                      │
│  ├─ 🟠 Missed Payments: [2 insights]                          │
│  ├─ 🟢 Positive Pattern: [3 insights]                         │
│  ├─ 🟢 Long Credit History: [1 insight]                       │
│  └─ 🟢 Low Application Rate: [1 insight]                      │
│                                                                 │
│  Sort by Severity:                                             │
│  1. Critical (⛔)                                              │
│  2. High (🔴)                                                 │
│  3. Medium (🟡)                                               │
│  4. Low (🔵)                                                  │
│  5. Positive (✅)                                             │
│                                                                 │
│  Format Output:                                                │
│  ├─ Console: Rich formatted report                            │
│  └─ JSON: Machine-readable export                             │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: OUTPUT                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Console Report (stdout)                                        │
│  ├─ Header (name, score, date)                                │
│  ├─ Summary (severity counts)                                  │
│  ├─ Insights by category                                       │
│  │   ├─ Message                                                │
│  │   └─ Recommendation                                         │
│  └─ Footer                                                     │
│                                                                 │
│  JSON File (output/report_sample_2.json)                       │
│  {                                                             │
│    "generated_at": "2025-10-22T14:08:06",                     │
│    "total_insights": 9,                                        │
│    "severity_counts": {...},                                   │
│    "insights_by_label": {...}                                  │
│  }                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Record Processing Logic

**Decision Tree:**

```
For each record in normalized data:
│
├─ Is this a loan record?
│  │  (has facility_type or loantype)
│  │
│  ├─ YES → Loan Record
│  │  │
│  │  ├─ Is revolving credit? (CRDTCARD, OVRDRAFT)
│  │  │  ├─ YES → Apply utilization rules
│  │  │  └─ NO  → Skip utilization rules
│  │  │
│  │  ├─ Apply payment conduct rules (ALL loans)
│  │  ├─ Apply positive pattern rules (if all_zero = true)
│  │  └─ Skip aggregate rules (legal, trade, etc.)
│  │
│  └─ NO → Aggregate Record
│     │  (has numberofloans, legal_cases, etc.)
│     │
│     ├─ Apply portfolio rules (applications, history)
│     ├─ Apply legal risk rules
│     ├─ Apply trade reference rules
│     ├─ Apply concentration rules
│     └─ Skip loan-specific rules
```

---

## 6. Configuration Management

### 6.1 rules.json Structure

**Complete schema:**

```json
{
  "rules": [
    {
      "label": "🟠 Missed Payments",           // Category with emoji
      "compound_type": "Serious Delinquency",  // Specific type
      "condition": "payment_conduct_code >= 3", // Python expression
      "template": "Your {{Facility}} with {{Lender_Type}} has...", // Jinja2
      "recommendation": "Accounts 60+ days overdue...",  // Action advice
      "data_source": "CCRIS",                  // Data origin
      "field_mapping": "Code 3=61-90 days...", // Documentation
      "priority": "Critical"                   // Severity level
    }
  ],
  "metadata": {
    "version": "2.1",
    "last_updated": "2025-10-22",
    "total_rules": 24
  }
}
```

### 6.2 Rule Components Explained

| Component | Required | Purpose | Example |
|-----------|----------|---------|---------|
| `label` | ✅ Yes | Category identifier (with emoji) | "🟠 Missed Payments" |
| `compound_type` | ✅ Yes | Specific insight type | "Serious Delinquency" |
| `condition` | ✅ Yes | Boolean expression | "payment_conduct_code >= 3" |
| `template` | ✅ Yes | Message template | "Your {{Facility}} has..." |
| `recommendation` | ✅ Yes | Actionable advice | "Contact your lender..." |
| `data_source` | ❌ No | Origin of data | "CCRIS", "Legal Records" |
| `field_mapping` | ❌ No | Field documentation | "Code 3=61-90 days..." |
| `priority` | ✅ Yes | Severity | "Critical", "High", "Medium", "Low", "Positive" |

### 6.3 Available Variables Reference

**Comprehensive list with descriptions:**

#### Loan-Level Variables

```python
# Numeric
creditutilizationratio  # Percentage (0-100)
balance                 # Outstanding amount (RM)
limit                   # Credit limit (RM)
utilization            # Same as creditutilizationratio
payment_conduct_code    # Max arrears (0-8)
mon_arrears            # Months in arrears
inst_arrears           # Installments in arrears

# Boolean
payment_conduct_all_zero  # True if all 12 months = 0
is_revolving              # True for CRDTCARD, OVRDRAFT
is_secured                # True if collateral exists

# String
facility_type          # CRDTCARD, PCPASCAR, etc.
loantype               # Friendly name (Credit Card, Car Loan)
Facility               # Same as loantype (for templates)
lendertype             # Lender name
Lender_Type            # Same as lendertype (for templates)
account_type           # "revolving" or "installment"
```

#### Aggregate/Portfolio Variables

```python
# Numeric
numberofloans              # Total active accounts
numapplicationslast12months # Applications in past year
numpendingapplications     # Currently pending
distinct_account_types     # Unique facility types
oldest_account_months      # Age of oldest account
oldest_account_years       # oldest_months / 12
accounts_per_lender        # Max accounts with one lender
secured_loan_ratio         # % of secured debt
recent_enquiries           # Enquiries in 30 days
application_decline_rate   # % declined (if available)

# Trade References
trade_ref_amount_overdue   # Total overdue (RM)
trade_ref_reminder_count   # Number of reminders

# Legal
legal_cases_settled        # Count of settled cases
legal_cases_active         # Count of active cases
director_windingup_company # Count of D4 cases

# Boolean
has_credit_card           # Has CRDTCARD account
has_installment_loan      # Has term loan
bankruptcy_active         # Active bankruptcy proceeding

# String
case_types               # List of active case types
case_details             # Bankruptcy details
company_name             # D4 company name
lender_name              # Most common lender
aging_bucket             # Trade ref aging category
```

#### Personal Info (For Templates)

```python
name           # Customer name
ic_number      # NRIC
ctos_score     # 300-850
```

### 6.4 Condition Syntax Guide

**Supported Operators:**

```python
# Comparison
>   Greater than
<   Less than
>=  Greater than or equal
<=  Less than or equal
==  Equal to
!=  Not equal to

# Logical
and  Both conditions true
or   Either condition true
not  Negate condition

# Membership
in      Value in list
not in  Value not in list

# Grouping
()  Parentheses for precedence
```

**Examples:**

```python
# Simple comparison
"creditutilizationratio > 80"

# Range check
"creditutilizationratio > 50 and creditutilizationratio <= 80"

# Multiple conditions
"payment_conduct_code >= 1 and payment_conduct_code <= 2"

# Boolean check
"has_credit_card == false"

# Complex
"(legal_cases_active > 0 or bankruptcy_active == true) and ctos_score < 500"

# String check (if supported)
"facility_type == 'CRDTCARD'"

# Membership (if implemented)
"payment_conduct_code in [1, 2, 3]"
```

### 6.5 Template Syntax Guide

**Jinja2 features supported:**

```jinja2
{# Variable substitution #}
Your {{Facility}} with {{Lender_Type}}

{# Filters #}
Balance: {{balance|currency}}
Utilization: {{creditutilizationratio|percentage}}

{# Conditionals (if needed) #}
{% if balance > 5000 %}
Your balance is high.
{% endif %}

{# Math (basic) #}
{{ balance / 1000 }} thousand

{# Formatting #}
{{ "%.1f" % creditutilizationratio }}%
```

**Best practices:**

✅ DO:
- Use `{{Facility}}` and `{{Lender_Type}}` (title case) for loan records
- Include specific numbers: `{{creditutilizationratio}}%`
- Keep messages concise and actionable

❌ DON'T:
- Use complex logic in templates (put in condition instead)
- Assume variables exist (check if added to defaults)
- Use technical jargon (write for end users)

---

## 7. Rule Development Guide

### 7.1 Adding a New Rule - Complete Walkthrough

**Scenario:** Add a rule to flag customers with high debt-to-income ratio.

#### Step 1: Define the Business Logic

```
Rule Name: High Debt-to-Income
Trigger: Monthly debt payments > 60% of estimated income
Target: Aggregate record (portfolio-level)
Severity: High
Message: "Your debt payments consume {{debt_to_income_ratio}}% of your income..."
```

#### Step 2: Determine Required Variables

```python
# New variable needed:
debt_to_income_ratio = (total_monthly_payments / monthly_income) * 100

# Calculation:
total_monthly_payments = sum(inst_amount for all active loans)
monthly_income = # Need to add this (user input or estimation)
```

#### Step 3: Add Variable to Parser Defaults

```python
# In condition_parser.py
DEFAULT_VALUES = {
    # ... existing ...
    'debt_to_income_ratio': 0.0,  # ADD THIS
    'monthly_income': 0.0,         # ADD THIS
    'total_monthly_payment': 0.0,  # ADD THIS
}
```

#### Step 4: Extract/Calculate Data

**Option A: If data exists in XML:**

```python
# In data_input.py
def _extract_monthly_income(self) -> float:
    # Extract from XML if available
    income_elem = self.root.find('.//ns:monthly_income', self.ns)
    return float(income_elem.text) if income_elem is not None else 0.0
```

**Option B: Calculate from existing data:**

```python
# In normalize_data() function
total_monthly_payment = sum(
    loan.get('inst_amount', 0) 
    for loan in loans 
    if loan.get('inst_amount', 0) > 0
)

# Estimate income from credit utilization (rough)
# OR require as input parameter
monthly_income = estimated_income  # From user input

debt_to_income_ratio = (
    (total_monthly_payment / monthly_income * 100) 
    if monthly_income > 0 else 0
)

aggregate_record['debt_to_income_ratio'] = debt_to_income_ratio
aggregate_record['monthly_income'] = monthly_income
aggregate_record['total_monthly_payment'] = total_monthly_payment
```

#### Step 5: Add Rule to rules.json

```json
{
  "label": "🔴 High Debt",
  "compound_type": "Debt-to-Income Concern",
  "condition": "debt_to_income_ratio > 60",
  "template": "Your debt payments consume {{debt_to_income_ratio}}% of your income, significantly above the recommended 40% threshold.",
  "recommendation": "High debt-to-income ratios can make it difficult to obtain new credit. Focus on paying down high-interest debts first, starting with credit cards. Consider consolidating loans for lower monthly payments.",
  "data_source": "Calculated",
  "field_mapping": "Calculate: (Sum of all monthly payments / Monthly income) * 100",
  "priority": "High"
}
```

#### Step 6: Add Template Defaults

```python
# In template_renderer.py
defaults = {
    # ... existing ...
    'debt_to_income_ratio': '0.0',
    'monthly_income': '0.00',
    'total_monthly_payment': '0.00'
}
```

#### Step 7: Test the Rule

```python
# Create test data
test_data = {
    'records': [
        # ... loan records ...
        {
            'numberofloans': 3,
            'debt_to_income_ratio': 75.5,  # High ratio
            'monthly_income': 4000,
            'total_monthly_payment': 3020
        }
    ],
    'personal_info': {...}
}

# Run engine
engine = RuleEngine('rules/rules.json')
insights = engine.process_data(test_data)

# Verify
high_debt = [i for i in insights if i['label'] == '🔴 High Debt']
assert len(high_debt) == 1
assert '75.5%' in high_debt[0]['message']
```

#### Step 8: Document the Rule

```markdown
### High Debt Rule

**Purpose:** Flag customers with unsustainable debt loads

**Condition:** `debt_to_income_ratio > 60`

**Applies To:** Aggregate record

**Calculation:**
```python
debt_to_income_ratio = (
    sum(loan['inst_amount'] for all loans) / monthly_income
) * 100
```

**Threshold Rationale:**
- 0-40%: Healthy
- 40-60%: Moderate concern
- 60%+: High risk

**Data Requirements:**
- Monthly income (user input or estimation)
- Installment amounts from all active loans
```

### 7.2 Rule Testing Checklist

Before deploying a new rule:

- [ ] Condition syntax is valid Python
- [ ] All variables exist in DEFAULT_VALUES
- [ ] Template variables are defined
- [ ] Tested with matching data (expect True)
- [ ] Tested with non-matching data (expect False)
- [ ] Tested with missing variables (uses defaults)
- [ ] Message is clear and actionable
- [ ] Recommendation is specific and helpful
- [ ] Correct severity level assigned
- [ ] Applies to correct record type (loan vs aggregate)
- [ ] No duplicate rules exist
- [ ] Documented in rules guide

### 7.3 Common Rule Patterns

#### Pattern 1: Threshold Rule

```json
{
  "label": "🟡 Pattern Name",
  "compound_type": "Type",
  "condition": "numeric_variable > threshold",
  "template": "Your {{variable}} is {{value}}, which is above {{threshold}}",
  "recommendation": "Advice here...",
  "priority": "Medium"
}
```

#### Pattern 2: Range Rule

```json
{
  "condition": "variable > lower_bound and variable <= upper_bound",
  "template": "Your {{variable}} of {{value}} falls in the moderate range"
}
```

#### Pattern 3: Boolean Flag

```json
{
  "condition": "has_something == true and related_variable > 0",
  "template": "You have {{related_variable}} {{things}}"
}
```

#### Pattern 4: Negative Detection

```json
{
  "condition": "has_something == false",
  "template": "Your profile lacks {{something}}",
  "recommendation": "Consider adding {{something}} to improve..."
}
```

#### Pattern 5: Composite Score

```json
{
  "condition": "(score_a * 0.4 + score_b * 0.6) > threshold",
  "template": "Your composite score is..."
}
```

---

---

## Appendix A: Facility Type Reference

| Code | Name | Category | Collateral |
|------|------|----------|------------|
| CRDTCARD | Credit Card | Revolving | Clean |
| OVRDRAFT | Overdraft | Revolving | Clean/Secured |
| HSLNFNCE | Housing Loan | Installment | Property |
| PCPASCAR | Car Loan | Installment | Vehicle |
| OTLNFNCE | Other Term Loan | Installment | Varies |
| MICROEFN | Micro Enterprise Fund | Installment | Clean |
| BUYNPAYL | Buy Now Pay Later | Installment | Clean |

---

## Appendix B: Payment Conduct Code Reference

| Code | Meaning | Days Late | Severity |
|------|---------|-----------|----------|
| 0 | Current | 0 | ✅ Good |
| 1 | Slight delay | 1-30 | ⚠️ Minor |
| 2 | Moderate delay | 31-60 | ⚠️ Moderate |
| 3 | Serious | 61-90 | ❌ High |
| 4 | Very serious | 91-120 | ❌ High |
| 5 | Extremely serious | 121-150 | ❌ Critical |
| 6 | Severe | 151-180 | ❌ Critical |
| 7 | Very severe | 181-210 | ❌ Critical |
| 8 | Maximum | 210+ | ❌ Critical |

---

## Appendix C: CTOS Score Interpretation

| Score Range | Rating | Meaning |
|-------------|--------|---------|
| 300-399 | Poor | High credit risk, significant payment issues |
| 400-499 | Fair | Moderate risk, some delinquencies |
| 500-599 | Fair | Manageable risk, minor issues |
| 600-699 | Good | Low risk, good payment history |
| 700-799 | Very Good | Very low risk, excellent history |
| 800-850 | Excellent | Minimal risk, pristine credit |

---

## Appendix D: Glossary

**Aggregate Record**: Portfolio-level summary record containing overall metrics (total loans, legal cases, etc.)

**asteval**: Python library for safe mathematical expression evaluation without exec/eval vulnerabilities

**CCRIS**: Central Credit Reference Information System - Bank Negara Malaysia's credit reporting system

**Conduct Code**: Numeric indicator (0-8) representing payment timeliness

**CTOS**: Credit Tip-Off Service - Malaysia's credit reporting agency

**Jinja2**: Python templating engine for generating text output

**Loan Record**: Individual account-level record for a specific loan/credit facility

**Normalization**: Process of converting raw extracted data into standardized format

**Revolving Credit**: Credit facility with no fixed repayment schedule (e.g., credit cards)

**Special Attention Account**: Account flagged by CCRIS for issues (written off, legal action, etc.)

**Template**: String with placeholders ({{variable}}) for dynamic message generation

**Utilization Ratio**: Percentage of credit limit currently in use (balance / limit * 100)

---

## Appendix E: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-15 | Initial release with PDF parsing |
| 2.0 | 2025-10-20 | Migrated to XML parsing, improved extraction |
| 2.1 | 2025-10-22 | Added full lender names, case_types, payment_conduct_all_zero, BUYNPAYL support |

---

**Document Status:** Phase 1 MVP 
**Last Review Date:** October 22, 2025   

---

*End of Technical Documentation*