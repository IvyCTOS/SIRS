# Project Requirements: Rule-Based Credit Behaviour Insight Engine

## 🧭 Project Title
Credit Behavior Insight Engine – A rule-based system for analyzing CTOS credit report data and generating personalized financial guidance and advice.

## 🎯 Project Objective
To build a Python-based rule engine that:
- Ingests structured data from CTOS credit reports.
- Applies predefined conditions to detect financial behaviors.
- Labels records into behavioral categories.
- Generates personalized insights and educational recommendations.
- Ensures compliance by avoiding financial product advice.

## 🧩 System Components
1. **Data Input**
   - **Format:** Flattened tables (e.g., JSON, CSV, Pandas DataFrames).
   - **Source:** CTOS credit report in PDF format.
   - **Pipeline:** 
     - A preprocessing module will parse the PDF report using tools like pdfparser.
     - Extracted data will be converted into structured JSON tables, segmented by report sections: 
       - Loan Information
       - Special Attention Account
       - Credit Application
       - External Trade Reference (ETR)
   - **Output:** Cleaned, normalized JSON tables ready for rule evaluation.

2. **Rule Engine**
   - **Input:** Field values from each section.
   - **Logic:** Evaluate compound conditions (e.g., balance >= limit).
   - **Output:** 
     - Label (e.g., 🔴 High Utilization)
     - Insight message (template with dynamic values)
     - Recommendation (pre-written guidance)

3. **Rule Storage**
   - **Format:** JSON or YAML file.
   - **Fields:** 
     - label
     - compound_type
     - condition
     - template
     - recommendation

4. **Condition Parser**
   - Safely evaluate logical expressions.
   - Support compound conditions (AND, OR).
   - Handle missing/null values gracefully.

5. **Template Renderer**
   - Replace placeholders (e.g., [loan_type]) with actual values.
   - Ensure formatting consistency (e.g., currency, percentages).

6. **Output Aggregator**
   - Group insights by label or section.
   - Optionally rank by severity or frequency.
   - Export as JSON, HTML, or PDF report.

## 🧠 Behavioral Labels & Compound Types
| Label | Compound Type | Compound Condition | Insight Template | Recommendation |
|-------|---------------|--------------------|-------------------|-----------------|
| 🔴 High Utilization | Revolving Credit Overuse | creditutilizationratio > 80 | Your [loantype] with [lendertype] has a utilization rate of [creditutilizationratio]% — well above the recommended threshold. | Credit utilization above 30% can signal financial stress to lenders. Aim to pay off balances early in the billing cycle, or request a credit limit increase if your income supports it. This helps improve your credit score and borrowing power. |
|  | Multiple Active Loans | numberofloans > 0 | You currently have [numberofloans] active loans, which may indicate over-reliance on credit. | Managing multiple loans can be challenging. Consider consolidating them into a single facility with better terms to reduce your monthly obligations and improve your credit profile. |
|  | Maxed Out Credit | balance >= limit | Your [loan_type] is fully utilized with RM [balance] out of RM [limit]. | Maxing out your credit lines can negatively impact your score. Try to reduce your balance and avoid using more than 30% of your available limit to maintain a healthy credit standing. |
| 🟠 Missed Payments | Long-Term Delinquency | mon_arrears >= 3 and inst_arrears >= 3 | Your [loantype] has missed payments for [monarrears] months, with [inst_arrears] installments overdue. | Missed payments can stay on your credit report for years. Reach out to your lender to negotiate a payment plan or restructuring. Setting up auto-debit or reminders can help prevent future delays. |
|  | Near Default | mon_arrears >= 6 | Your [loantype] is nearing default status with [mon_arrears] months of missed payments. | Contact your lender immediately to avoid default. Explore restructuring or hardship programs to regain control. |
|  | Recent Missed Payment | lastpaymentstatus == 'missed' and daysincepayment <= 30 | A payment was missed recently on your [loantype] with [lendertype]. | A recent missed payment can affect your score. Make the payment as soon as possible and consider setting up automatic payments to avoid future issues. |
|  | Repeated Missed Payments | missed_payments of last 6 months | Your [loantype] has had repeated missed payments in the last 6 months. | Consistent late payments can severely damage your credit. Set up auto-pay or reminders and prioritize clearing overdue amounts. |
|  | Settled After Arrears | previousstatus == "arrears" and currentstatus == "settled" | Your [loan_type] was previously in arrears but has now been settled. | Settling overdue accounts is a positive step. Continue making timely payments and monitor your credit report to ensure the account is updated correctly. |
| 🟡 Frequent Applications | High Application Volume | numapplicationslast12months > 0 | You've applied for [numapplicationslast12months] facilities in the past year. | Each credit application may trigger a hard inquiry, which can lower your score temporarily. Plan your credit needs ahead and apply only when necessary. Consider pre-qualification tools to check eligibility without affecting your score. |
|  | Multiple Pending Applications | numpendingapplications > 0 | You have [numpendingapplications] applications still pending. | Pending applications may indicate uncertainty. Review your financial needs and wait for current applications to be processed before submitting new ones. |
|  | Multiple Declined Applications | decline_rate > 50% | Half of your recent applications have been declined. | Frequent rejections can hurt your score. Review your credit profile and improve key areas before reapplying. |
|  | High-Risk Facility Applications | application_types contains any of ['short-term loan', 'payday loan', 'unsecured personal loan'] | You've applied for high-risk facilities like [application_types]. | Applying for high-risk facilities can signal financial distress. Evaluate your needs carefully and consider safer alternatives to maintain credit health. |
| 🟣 Thin Credit File | Few Account Types | distinct_account_types <= 1 | Your credit file shows limited diversity, mostly [loan_type] accounts. | A diverse credit mix shows lenders you can manage different types of credit responsibly. If eligible, consider opening a secured credit card or small installment loan and maintain consistent payments to build history. |
|  | No Installment History | No installment loans in file | Your credit file has 0 installment loan history. | Adding a small installment loan and repaying it on time can help diversify your credit and build a stronger profile. |
|  | No Revolving Behavior | no revolving account activity in last 6 months | No revolving account usage detected in recent months. | Using revolving credit responsibly helps build your score. Consider using a credit card for small purchases and paying it off monthly to demonstrate good credit behavior. |
|  | Non-Bank Dominance | nonbank_accounts / total_accounts > 0.7 | Most of your accounts are with non-bank lenders. | Bank-issued credit is often viewed more favorably. Consider adding bank-based credit products to strengthen your credit profile. |
| ⚪ Short Credit History | New Accounts Only | monthssinceapproval > 0 | Your oldest account is only [monthssinceapproval] months old. | A longer credit history contributes positively to your score. Keep existing accounts open and active to build a stronger credit timeline. |
|  | Recent Enquiries | recent_enquiries >= 3 in last 30 days | You've made multiple recent enquiries for [application_types]. | Frequent enquiries can lower your score. Limit applications and use pre-qualification tools to assess eligibility without impacting your credit. |
| ⚫ Legal Risk | Legal Action Taken | legal_action_flag == true | Legal action was initiated on your [facility] account on [legal_date]. | Legal actions and write-offs can severely impact creditworthiness. Review the details with a financial counselor or legal advisor. If possible, negotiate a settlement and request a ‘paid as agreed’ update on your credit file. |
|  | Written-Off Account | account_status == "written-off" and Balance > 0 | Your [facility] account has been written off with RM [Balance] outstanding. | Written-off accounts are serious derogatory marks. Contact your lender to explore settlement options and request updates to your credit report once resolved. |
|  | Multiple Reminder Letters | reminderlettercount >= 3 | [reminderlettercount] reminder letters have been sent for your [debt_type] account. | Multiple reminders suggest persistent delinquency. Act quickly to resolve the issue and prevent escalation to legal action or collections. |

## 🔐 Compliance Requirements
- No financial product recommendations.
- Avoid suggesting specific lenders or credit products.
- Ensure messages are educational and neutral.

## 📈 Future Enhancements
- Add feedback logging (e.g., user flags or ratings).
- Train ML models using labeled data for predictive insights.
- Integrate with UI for real-time recommendations.

## 🛠️ Technical Stack
- **Language:** Python 3.x
- **Libraries:** 
  - pandas for data handling
  - json or yaml for rule storage
  - asteval or expr-eval for safe condition parsing
  - jinja2 or custom logic for template rendering

## 📂 Folder Structure (Suggested)
```
credit_insight_engine/
├── data/                  # Sample input files
├── rules/                 # JSON/YAML rule definitions
├── engine/                # Core logic (parser, evaluator, renderer)
├── pdf_parser/            # PDF-to-JSON conversion pipeline
├── output/                # Generated reports
├── tests/                 # Unit tests
└── main.py                # Entry point
```