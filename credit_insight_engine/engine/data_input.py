import PyPDF2
import json
import re
from datetime import datetime
from typing import Dict, List, Any

class CTOSReportParser:
    """Parser for CTOS Credit Reports"""
    
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.raw_text = ""
        self.pages = []
        
    def extract_data_from_pdf(self):
        """Extract all text from PDF and organize by pages"""
        extracted_data = {
            'personal_info': {},
            'credit_snapshot': {},
            'ctos_score': {},
            'loan_information': [],
            'special_attention_accounts': [],
            'credit_applications': [],
            'legal_cases': [],
            'trade_references': [],
            'directorships': [],
            'address_records': []
        }
        
        try:
            with open(self.pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    self.pages.append(text)
                    self.raw_text += text + "\n"
                
                # Extract each section
                extracted_data['personal_info'] = self._extract_personal_info()
                extracted_data['credit_snapshot'] = self._extract_credit_snapshot()
                extracted_data['ctos_score'] = self._extract_ctos_score()
                extracted_data['loan_information'] = self._extract_loan_information()
                extracted_data['credit_applications'] = self._extract_credit_applications()
                extracted_data['legal_cases'] = self._extract_legal_cases()
                extracted_data['trade_references'] = self._extract_trade_references()
                extracted_data['directorships'] = self._extract_directorships()
                extracted_data['address_records'] = self._extract_address_records()
                
        except Exception as e:
            print(f"Error reading PDF: {e}")
            
        return extracted_data
    
    def _extract_personal_info(self) -> Dict:
        """Extract personal identification information"""
        personal_info = {}
        
        try:
            # Extract Name
            name_match = re.search(r'Name.*?Nama\s+([A-Z\s]+)', self.raw_text)
            if name_match:
                personal_info['name'] = name_match.group(1).strip()
            
            # Extract New ID
            id_match = re.search(r'New ID.*?ID Baru\s+(\d+)', self.raw_text)
            if id_match:
                personal_info['new_id'] = id_match.group(1).strip()
            
            # Extract Date of Birth
            dob_match = re.search(r'Date of Birth.*?Tarikh Lahir\s+(\d{2}-\d{2}-\d{4})', self.raw_text)
            if dob_match:
                personal_info['date_of_birth'] = dob_match.group(1).strip()
            
            # Extract Nationality
            nationality_match = re.search(r'Nationality.*?Kewarganegaraan\s+([A-Z]+)', self.raw_text)
            if nationality_match:
                personal_info['nationality'] = nationality_match.group(1).strip()
            
            # Extract Address
            address_match = re.search(r'Address 1.*?Alamat 1\s+(.*?)(?=Source:|Address 2)', self.raw_text, re.DOTALL)
            if address_match:
                personal_info['address'] = address_match.group(1).strip()
                
        except Exception as e:
            print(f"Error extracting personal info: {e}")
            
        return personal_info
    
    def _extract_ctos_score(self) -> Dict:
        """Extract CTOS Score and reasons"""
        score_info = {}
        
        try:
            # Extract Score Value
            score_match = re.search(r'(?:300|400|500|600|700|800)\s+(\d{3})\s+(?:300|400|500|600|700|800)', self.raw_text)
            if score_match:
                score_info['score'] = int(score_match.group(1))
            
            # Extract reasons affecting score
            reasons = []
            reason_section = re.search(r'What is affecting my Score\?(.*?)(?:Credit Info at a Glance|$)', self.raw_text, re.DOTALL)
            if reason_section:
                reason_text = reason_section.group(1)
                # Extract numbered reasons
                reason_matches = re.finditer(r'\d+\.\s+(.*?)(?=\d+\.|Apakah|$)', reason_text, re.DOTALL)
                for match in reason_matches:
                    reason = match.group(1).strip()
                    # Clean up the reason text
                    reason = re.sub(r'\s+', ' ', reason)
                    if reason and len(reason) > 10:
                        reasons.append(reason)
            
            score_info['reasons_affecting_score'] = reasons
            
        except Exception as e:
            print(f"Error extracting CTOS score: {e}")
            
        return score_info
    
    def _extract_credit_snapshot(self) -> Dict:
        """Extract credit summary information"""
        snapshot = {}
        
        try:
            # Extract bankruptcy status
            bankruptcy_match = re.search(r'Bankruptcy Proceedings Record.*?(?:YES|NO)', self.raw_text)
            if bankruptcy_match:
                snapshot['bankruptcy_proceedings'] = 'YES' in bankruptcy_match.group(0)
            
            # Extract legal records count and value
            legal_match = re.search(r'Legal records in past 24 months.*?Number.*?(\d+).*?Value.*?([\d,]+\.?\d*)', self.raw_text, re.DOTALL)
            if legal_match:
                snapshot['legal_records_24months'] = {
                    'count': int(legal_match.group(1)),
                    'value': float(legal_match.group(2).replace(',', ''))
                }
            
            # Extract outstanding credit facilities
            outstanding_match = re.search(r'Outstanding credit facilities.*?Number.*?(\d+).*?Value.*?([\d,]+\.?\d*).*?Installments in arrears.*?(YES|NO)', self.raw_text, re.DOTALL)
            if outstanding_match:
                snapshot['outstanding_facilities'] = {
                    'count': int(outstanding_match.group(1)),
                    'value': float(outstanding_match.group(2).replace(',', '')),
                    'has_arrears': outstanding_match.group(3) == 'YES'
                }
            
            # Extract credit applications
            app_match = re.search(r'Credit applications in past 12 months.*?Total.*?(\d+).*?Approved.*?(\d+).*?Pending.*?(\d+)', self.raw_text, re.DOTALL)
            if app_match:
                snapshot['credit_applications_12months'] = {
                    'total': int(app_match.group(1)),
                    'approved': int(app_match.group(2)),
                    'pending': int(app_match.group(3))
                }
            
            # Extract Special Attention Account status
            saa_match = re.search(r'Special Attention Accounts.*?(?:YES|NO)', self.raw_text)
            if saa_match:
                snapshot['special_attention_account'] = 'YES' in saa_match.group(0)
                
        except Exception as e:
            print(f"Error extracting credit snapshot: {e}")
            
        return snapshot
    
    def _extract_loan_information(self) -> List[Dict]:
        """Extract detailed loan information from CCRIS"""
        loans = []
        
        try:
            # Find the loan information section
            loan_section = re.search(r'Loan Information.*?(?=Special Attention Account|Credit Application|$)', self.raw_text, re.DOTALL)
            
            if not loan_section:
                return loans
            
            loan_text = loan_section.group(0)
            
            # Split by loan entries (looking for date patterns at the start)
            loan_entries = re.split(r'(?=\d{2}-\d{2}-\d{4}\s+Own)', loan_text)
            
            for entry in loan_entries:
                if len(entry.strip()) < 50:  # Skip headers or empty entries
                    continue
                    
                loan = {}
                
                # Extract date
                date_match = re.search(r'(\d{2}-\d{2}-\d{4})', entry)
                if date_match:
                    loan['date'] = date_match.group(1)
                
                # Extract capacity
                if 'Own' in entry:
                    loan['capacity'] = 'Own'
                
                # Extract lender
                lender_match = re.search(r'Own\s+([A-Za-z\s]+?)(?:\d+|OTLNFNCE|CRDTCARD|HSLNFNCE|PCPASCAR|OVRDRAFT)', entry)
                if lender_match:
                    loan['lender'] = lender_match.group(1).strip()
                
                # Extract facility type
                facility_match = re.search(r'(OTLNFNCE|CRDTCARD|HSLNFNCE|PCPASCAR|OVRDRAFT|MICROEFN)', entry)
                if facility_match:
                    loan['facility_type'] = facility_match.group(1)
                    # Map to readable names
                    facility_map = {
                        'OTLNFNCE': 'Other Term Loans/Financing',
                        'CRDTCARD': 'Credit Card',
                        'HSLNFNCE': 'Housing Loans/Financing',
                        'PCPASCAR': 'Purchase Of Passenger Cars',
                        'OVRDRAFT': 'Overdraft',
                        'MICROEFN': 'Micro Enterprise Fund'
                    }
                    loan['facility_type_desc'] = facility_map.get(loan['facility_type'], loan['facility_type'])
                
                # Extract outstanding balance
                balance_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s+\d{2}-\d{2}-\d{4}', entry)
                if balance_match:
                    loan['outstanding_balance'] = float(balance_match.group(1).replace(',', ''))
                
                # Extract limit
                limit_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})\s+(?:00|10|30)', entry)
                if limit_match:
                    loan['limit'] = float(limit_match.group(1).replace(',', ''))
                
                # Extract repayment term
                term_match = re.search(r'(\d+\.?\d{0,2})\s+(MTH|IDF)', entry)
                if term_match:
                    loan['repayment_term_amount'] = float(term_match.group(1))
                    loan['repayment_term_type'] = 'Monthly' if term_match.group(2) == 'MTH' else 'Irregular'
                
                # Extract collateral type
                collateral_match = re.search(r'(00|10|30)', entry)
                if collateral_match:
                    collateral_code = collateral_match.group(1)
                    collateral_map = {
                        '00': 'Clean',
                        '10': 'Properties',
                        '30': 'Motor Vehicles'
                    }
                    loan['collateral_type'] = collateral_map.get(collateral_code, 'Unknown')
                
                # Extract conduct of account (payment history)
                # Looking for the 12-month pattern (N O S A J J M A M F J D)
                conduct_match = re.search(r'([0-9\s]{23,})', entry)
                if conduct_match:
                    conduct_str = conduct_match.group(1).strip()
                    loan['payment_history_12months'] = conduct_str.split()
                
                # Calculate derived metrics if we have the data
                if 'outstanding_balance' in loan and 'limit' in loan and loan['limit'] > 0:
                    loan['utilization_ratio'] = round((loan['outstanding_balance'] / loan['limit']) * 100, 2)
                
                # Count arrears in payment history
                if 'payment_history_12months' in loan:
                    arrears_count = sum(1 for x in loan['payment_history_12months'] if x != '0')
                    loan['months_in_arrears'] = arrears_count
                
                if loan:  # Only add if we extracted some data
                    loans.append(loan)
                    
        except Exception as e:
            print(f"Error extracting loan information: {e}")
            
        return loans
    
    def _extract_credit_applications(self) -> List[Dict]:
        """Extract credit application history"""
        applications = []
        
        try:
            # Find credit application section
            app_section = re.search(r'Credit Application.*?(?=REMARK LEGEND|$)', self.raw_text, re.DOTALL)
            
            if not app_section:
                return applications
            
            app_text = app_section.group(0)
            
            # Split by application entries
            app_entries = re.split(r'(?=\d{2}-\d{2}-\d{4}\s+A\s+Own)', app_text)
            
            for entry in app_entries:
                if len(entry.strip()) < 30:
                    continue
                
                app = {}
                
                # Extract date
                date_match = re.search(r'(\d{2}-\d{2}-\d{4})', entry)
                if date_match:
                    app['application_date'] = date_match.group(1)
                
                # Extract status
                if re.search(r'\s+A\s+', entry):
                    app['status'] = 'Approved'
                
                # Extract lender
                lender_match = re.search(r'Own\s+([A-Za-z\s]+?)(?:MICROEFN|OTLNFNCE|CRDTCARD)', entry)
                if lender_match:
                    app['lender'] = lender_match.group(1).strip()
                
                # Extract facility type
                facility_match = re.search(r'(MICROEFN|OTLNFNCE|CRDTCARD|HSLNFNCE|PCPASCAR)', entry)
                if facility_match:
                    app['facility_type'] = facility_match.group(1)
                
                # Extract amount
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})', entry)
                if amount_match:
                    app['amount'] = float(amount_match.group(1).replace(',', ''))
                
                # Extract property details if present
                if 'Property Status' in entry:
                    prop_status_match = re.search(r'Property Status:\s+([^\n]+)', entry)
                    if prop_status_match:
                        app['property_status'] = prop_status_match.group(1).strip()
                    
                    # Extract address lines
                    address_lines = re.findall(r'Address Line \d+:\s+([^\n]+)', entry)
                    if address_lines:
                        app['property_address'] = ', '.join(address_lines)
                    
                    postcode_match = re.search(r'Postcode/City/State/Country:\s+([^\n]+)', entry)
                    if postcode_match:
                        app['property_location'] = postcode_match.group(1).strip()
                
                if app:
                    applications.append(app)
                    
        except Exception as e:
            print(f"Error extracting credit applications: {e}")
            
        return applications
    
    def _extract_legal_cases(self) -> List[Dict]:
        """Extract legal case information"""
        legal_cases = []
        
        try:
            # Extract bankruptcy proceedings
            bankruptcy_section = re.search(r'1\. BANKRUPTCY PROCEEDING(.*?)(?=2\. SUMMONS|$)', self.raw_text, re.DOTALL)
            if bankruptcy_section:
                case = self._parse_bankruptcy_case(bankruptcy_section.group(1))
                if case:
                    legal_cases.append(case)
            
            # Extract summons cases
            summons_matches = re.finditer(r'SUMMONS - DIRECTED TO(.*?)(?=\d+\. |$)', self.raw_text, re.DOTALL)
            for match in summons_matches:
                case = self._parse_summons_case(match.group(1))
                if case:
                    legal_cases.append(case)
            
            # Extract civil suit cases
            civil_matches = re.finditer(r'CIVIL SUIT - DIRECTED TO(.*?)(?=\d+\. |D2:|$)', self.raw_text, re.DOTALL)
            for match in civil_matches:
                case = self._parse_civil_case(match.group(1))
                if case:
                    legal_cases.append(case)
            
            # Extract winding-up cases (non-personal capacity)
            winding_matches = re.finditer(r'DIRECTOR OF A COMPANY WITH PETITION OR WINDING-UP ORDER ISSUED(.*?)(?=Note:|E: TRADE|$)', self.raw_text, re.DOTALL)
            for match in winding_matches:
                case = self._parse_winding_case(match.group(1))
                if case:
                    legal_cases.append(case)
                    
        except Exception as e:
            print(f"Error extracting legal cases: {e}")
            
        return legal_cases
    
    def _parse_bankruptcy_case(self, text: str) -> Dict:
        """Parse bankruptcy case details"""
        case = {'case_type': 'Bankruptcy Proceeding'}
        
        try:
            # Extract plaintiff
            plaintiff_match = re.search(r'EXPARTE.*?([A-Z\s]+?)(?=CASE NO|$)', text)
            if plaintiff_match:
                case['plaintiff'] = plaintiff_match.group(1).strip()
            
            # Extract case number
            case_no_match = re.search(r'CASE NO.*?(\S+)', text)
            if case_no_match:
                case['case_number'] = case_no_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'AMOUNT.*?([\d,]+\.?\d*)', text)
            if amount_match:
                case['amount'] = float(amount_match.group(1).replace(',', ''))
            
            # Extract dates
            notice_date_match = re.search(r'NOTICE DATE.*?(\d{2}-\d{2}-\d{4})', text)
            if notice_date_match:
                case['notice_date'] = notice_date_match.group(1)
            
            petition_date_match = re.search(r'PETITION DATE.*?(\d{2}-\d{2}-\d{4})', text)
            if petition_date_match:
                case['petition_date'] = petition_date_match.group(1)
            
            # Extract settlement status
            if 'CASE FULLY SETTLED' in text:
                case['settlement_status'] = 'Fully Settled'
                settled_date_match = re.search(r'SETTLED DATE\s+(\d{2}-\d{2}-\d{4})', text)
                if settled_date_match:
                    case['settled_date'] = settled_date_match.group(1)
            
            # Extract solicitor
            solicitor_match = re.search(r'SOLICITOR.*?([A-Z\s&]+)', text)
            if solicitor_match:
                case['solicitor'] = solicitor_match.group(1).strip()
                
        except Exception as e:
            print(f"Error parsing bankruptcy case: {e}")
            
        return case
    
    def _parse_summons_case(self, text: str) -> Dict:
        """Parse summons case details"""
        case = {'case_type': 'Summons'}
        
        try:
            # Extract plaintiff
            plaintiff_match = re.search(r'PLAINTIFF.*?([A-Z\s]+?)(?=CASE NO|$)', text)
            if plaintiff_match:
                case['plaintiff'] = plaintiff_match.group(1).strip()
            
            # Extract case number
            case_no_match = re.search(r'CASE NO.*?(\S+)', text)
            if case_no_match:
                case['case_number'] = case_no_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'AMOUNT.*?([\d,]+\.?\d*)', text)
            if amount_match:
                case['amount'] = float(amount_match.group(1).replace(',', ''))
            
            # Extract action date
            action_date_match = re.search(r'ACTION DATE.*?(\d{2}-\d{2}-\d{4})', text)
            if action_date_match:
                case['action_date'] = action_date_match.group(1)
            
            # Extract settlement
            if 'CASE FULLY SETTLED' in text:
                case['settlement_status'] = 'Fully Settled'
                settled_date_match = re.search(r'SETTLED DATE\s+(\d{2}-\d{2}-\d{4})', text)
                if settled_date_match:
                    case['settled_date'] = settled_date_match.group(1)
                    
        except Exception as e:
            print(f"Error parsing summons case: {e}")
            
        return case
    
    def _parse_civil_case(self, text: str) -> Dict:
        """Parse civil suit case details"""
        case = {'case_type': 'Civil Suit'}
        
        # Similar structure to summons
        try:
            plaintiff_match = re.search(r'PLAINTIFF.*?([A-Z\s]+?)(?=CASE NO|$)', text)
            if plaintiff_match:
                case['plaintiff'] = plaintiff_match.group(1).strip()
            
            case_no_match = re.search(r'CASE NO.*?(\S+)', text)
            if case_no_match:
                case['case_number'] = case_no_match.group(1)
            
            amount_match = re.search(r'AMOUNT.*?([\d,]+\.?\d*)', text)
            if amount_match:
                case['amount'] = float(amount_match.group(1).replace(',', ''))
            
            action_date_match = re.search(r'ACTION DATE.*?(\d{2}-\d{2}-\d{4})', text)
            if action_date_match:
                case['action_date'] = action_date_match.group(1)
            
            if 'CASE FULLY SETTLED' in text:
                case['settlement_status'] = 'Fully Settled'
                settled_date_match = re.search(r'SETTLED DATE\s+(\d{2}-\d{2}-\d{4})', text)
                if settled_date_match:
                    case['settled_date'] = settled_date_match.group(1)
                    
        except Exception as e:
            print(f"Error parsing civil case: {e}")
            
        return case
    
    def _parse_winding_case(self, text: str) -> Dict:
        """Parse winding-up case (non-personal capacity)"""
        case = {'case_type': 'Winding-Up (Non-Personal Capacity)'}
        
        try:
            # Extract company name (respondent)
            respondent_match = re.search(r'RESPONDENT.*?([A-Z\s]+?)(?=REGISTRATION|$)', text)
            if respondent_match:
                case['company'] = respondent_match.group(1).strip()
            
            # Extract petitioner
            petitioner_match = re.search(r'PETITIONER.*?([A-Z]+)', text)
            if petitioner_match:
                case['petitioner'] = petitioner_match.group(1)
            
            # Extract case number
            case_no_match = re.search(r'CASE NO.*?(\S+)', text)
            if case_no_match:
                case['case_number'] = case_no_match.group(1)
            
            # Extract indebtedness
            debt_match = re.search(r'INDEBTEDNESS.*?([\d,]+\.?\d*)', text)
            if debt_match:
                case['indebtedness'] = float(debt_match.group(1).replace(',', ''))
            
            # Extract petition date
            petition_date_match = re.search(r'PETITION DATE.*?(\d{2}-\d{2}-\d{4})', text)
            if petition_date_match:
                case['petition_date'] = petition_date_match.group(1)
            
            # Extract subject's status in company
            status_match = re.search(r'STATUS.*?([A-Z\s&]+?)(?=WOUND-UP|$)', text)
            if status_match:
                case['subject_status'] = status_match.group(1).strip()
            
            # Extract settlement
            if 'CASE FULLY SETTLED' in text:
                case['settlement_status'] = 'Fully Settled'
                settled_date_match = re.search(r'SETTLED DATE\s+(\d{2}-\d{2}-\d{4})', text)
                if settled_date_match:
                    case['settled_date'] = settled_date_match.group(1)
                    
        except Exception as e:
            print(f"Error parsing winding case: {e}")
            
        return case
    
    def _extract_trade_references(self) -> List[Dict]:
        """Extract trade reference information"""
        trade_refs = []
        
        try:
            # Find trade reference section
            trade_section = re.search(r'E: TRADE REFERENCE(.*?)(?=- End of Report|$)', self.raw_text, re.DOTALL)
            
            if not trade_section:
                return trade_refs
            
            trade_text = trade_section.group(0)
            
            # Look for account entries
            account_matches = re.finditer(r'Account No\..*?(\d+)(.*?)(?=Account No\.|7\. Referee|$)', trade_text, re.DOTALL)
            
            for match in account_matches:
                ref = {}
                account_no = match.group(1)
                account_text = match.group(2)
                
                ref['account_number'] = account_no
                
                # Extract referee name
                referee_match = re.search(r'Referee.*?([A-Z\s]+?)(?=Account No|$)', trade_text)
                if referee_match:
                    ref['referee_name'] = referee_match.group(1).strip()
                
                # Extract statement date
                stmt_date_match = re.search(r'Statement Date.*?(\d{4}-\d{2}-\d{2})', account_text)
                if stmt_date_match:
                    ref['statement_date'] = stmt_date_match.group(1)
                
                # Extract default amount
                default_match = re.search(r'Default Amount.*?([\d,]+\.?\d*)', account_text)
                if default_match:
                    ref['default_amount'] = float(default_match.group(1).replace(',', ''))
                
                # Extract credit limit
                limit_match = re.search(r'Credit Limit.*?([\d,]+\.?\d*)', account_text)
                if limit_match:
                    ref['credit_limit'] = float(limit_match.group(1).replace(',', ''))
                
                # Extract credit terms
                terms_match = re.search(r'Credit Terms.*?(\d+)\s+Days', account_text)
                if terms_match:
                    ref['credit_terms_days'] = int(terms_match.group(1))
                
                # Extract aging information
                aging_matches = re.findall(r'(\d+\.?\d{0,2})\s+(?=0\.00|[\d,]+\.?\d*)', account_text)
                if aging_matches and len(aging_matches) >= 7:
                    ref['aging'] = {
                        '0-30_days': float(aging_matches[0]),
                        '31-60_days': float(aging_matches[1]),
                        '61-90_days': float(aging_matches[2]),
                        '91-120_days': float(aging_matches[3]),
                        '121-150_days': float(aging_matches[4]),
                        '151-180_days': float(aging_matches[5]),
                        '>180_days': float(aging_matches[6])
                    }
                
                # Extract account conduct
                if 'Unsatisfactory' in account_text:
                    ref['account_conduct'] = 'Unsatisfactory'
                elif 'Satisfactory' in account_text:
                    ref['account_conduct'] = 'Satisfactory'
                elif 'Good' in account_text:
                    ref['account_conduct'] = 'Good'
                elif 'Excellent' in account_text:
                    ref['account_conduct'] = 'Excellent'
                
                # Extract returned cheque information
                if 'Refer To Drawer' in account_text:
                    cheque_match = re.search(r'(\d+)\s+(\d+)\s+([A-Z\s]+?)\s+([\d,]+\.?\d*)\s+(\d{4}-\d{2}-\d{2})\s+Refer To Drawer', account_text)
                    if cheque_match:
                        ref['returned_cheque'] = {
                            'cheque_no': cheque_match.group(1),
                            'account_no': cheque_match.group(2),
                            'bank': cheque_match.group(3).strip(),
                            'amount': float(cheque_match.group(4).replace(',', '')),
                            'date': cheque_match.group(5),
                            'reason': 'Refer To Drawer'
                        }
                
                # Extract reminder count
                reminder_match = re.search(r'Sent reminder.*?(\d{4}-\d{2}-\d{2})', account_text)
                if reminder_match:
                    ref['reminder_sent_date'] = reminder_match.group(1)
                    ref['reminder_count'] = 1  # Could be enhanced to count multiple reminders
                
                if ref:
                    trade_refs.append(ref)
                    
        except Exception as e:
            print(f"Error extracting trade references: {e}")
            
        return trade_refs
    
    def _extract_directorships(self) -> List[Dict]:
        """Extract directorship and business interests"""
        directorships = []
        
        try:
            # Find directorships section
            director_section = re.search(r'B1: DIRECTORSHIPS AND BUSINESS INTERESTS(.*?)(?=B2: ADDRESS|$)', self.raw_text, re.DOTALL)
            
            if not director_section:
                return directorships
            
            director_text = director_section.group(0)
            
            # Find individual company entries
            company_matches = re.finditer(r'(\d+)\.\s+([A-Z\s]+?SDN BHD|[A-Z\s]+?ENTERPRISE)(.*?)(?=\d+\.|B2:|$)', director_text, re.DOTALL)
            
            for match in company_matches:
                company = {}
                company_name = match.group(2).strip()
                company_text = match.group(3)
                
                company['company_name'] = company_name
                
                # Extract status
                status_match = re.search(r'STATUS.*?(DISSOLVED|EXISTING|WINDING UP|TERMINATED|EXPIRED|ACTIVE)', company_text)
                if status_match:
                    company['status'] = status_match.group(1)
                
                # Extract position
                position_match = re.search(r'POSITION.*?(DIRECTOR.*?HOLDER|SOLE PROPRIETOR|PARTNER)', company_text)
                if position_match:
                    company['position'] = position_match.group(1)
                
                # Extract appointed date
                appointed_match = re.search(r'APPOINTED.*?(\d{2}-\d{2}-\d{4})', company_text)
                if appointed_match:
                    company['appointed_date'] = appointed_match.group(1)
                
                # Extract resigned date
                resigned_match = re.search(r'RESIGNED.*?(\d{2}-\d{2}-\d{4})', company_text)
                if resigned_match:
                    company['resigned_date'] = resigned_match.group(1)
                
                # Extract shares
                shares_match = re.search(r'SHARES.*?([\d,]+\.?\d*)', company_text)
                if shares_match:
                    company['shares'] = float(shares_match.group(1).replace(',', ''))
                
                # Extract profit after tax
                profit_match = re.search(r'Profit After Tax.*?([\d,]+\.?\d*)', company_text)
                if profit_match:
                    company['profit_after_tax'] = float(profit_match.group(1).replace(',', ''))
                
                # Extract year
                year_match = re.search(r'Year.*?(\d{2}-\d{2}-\d{4})', company_text)
                if year_match:
                    company['year'] = year_match.group(1)
                
                # Extract shareholding percentage
                shareholding_match = re.search(r'Shareholding.*?([\d\.]+)', company_text)
                if shareholding_match:
                    company['shareholding_percentage'] = float(shareholding_match.group(1))
                
                # Extract paid-up capital
                capital_match = re.search(r'PAID-UP CAPITAL.*?([\d,]+\.?\d*)', company_text)
                if capital_match:
                    company['paid_up_capital'] = float(capital_match.group(1).replace(',', ''))
                
                # Extract incorporation date
                incorporation_match = re.search(r'INCORPORATION.*?(\d{2}-\d{2}-\d{4})', company_text)
                if incorporation_match:
                    company['incorporation_date'] = incorporation_match.group(1)
                
                # Extract nature of business
                business_match = re.search(r'NATURE OF BUSINESS.*?([A-Z\s]+?)(?=INCORPORATION|REGISTRATION|$)', company_text)
                if business_match:
                    company['nature_of_business'] = business_match.group(1).strip()
                
                if company:
                    directorships.append(company)
                    
        except Exception as e:
            print(f"Error extracting directorships: {e}")
            
        return directorships
    
    def _extract_address_records(self) -> List[Dict]:
        """Extract address history"""
        addresses = []
        
        try:
            # Find address records section
            address_section = re.search(r'B2: ADDRESS RECORDS(.*?)(?=C1: BANKING|$)', self.raw_text, re.DOTALL)
            
            if not address_section:
                return addresses
            
            address_text = address_section.group(0)
            
            # Extract individual addresses
            address_matches = re.finditer(r'([A-Z0-9,\s\.\/\-]+?)\s+(\d{2}-\d{2}-\d{4})\s+(NRD|SSM)', address_text)
            
            for match in address_matches:
                addr = {
                    'address': match.group(1).strip(),
                    'last_updated': match.group(2),
                    'source': match.group(3)
                }
                addresses.append(addr)
                
        except Exception as e:
            print(f"Error extracting address records: {e}")
            
        return addresses


def normalize_data(extracted_data: Dict) -> Dict:
    """
    Normalize and clean extracted data for rule engine processing
    """
    normalized = {
        'report_metadata': {},
        'personal_info': {},
        'credit_profile': {},
        'loan_accounts': [],
        'credit_applications': [],
        'legal_records': [],
        'trade_references': [],
        'directorships': [],
        'behavioral_indicators': {}
    }
    
    try:
        # Normalize personal information
        if 'personal_info' in extracted_data:
            personal = extracted_data['personal_info']
            normalized['personal_info'] = {
                'full_name': personal.get('name', '').strip().upper(),
                'ic_number': personal.get('new_id', '').strip(),
                'date_of_birth': _parse_date(personal.get('date_of_birth', '')),
                'nationality': personal.get('nationality', '').strip(),
                'current_address': personal.get('address', '').strip()
            }
        
        # Normalize CTOS Score
        if 'ctos_score' in extracted_data:
            score_data = extracted_data['ctos_score']
            normalized['credit_profile']['ctos_score'] = score_data.get('score', 0)
            normalized['credit_profile']['score_factors'] = score_data.get('reasons_affecting_score', [])
        
        # Normalize credit snapshot
        if 'credit_snapshot' in extracted_data:
            snapshot = extracted_data['credit_snapshot']
            normalized['credit_profile'].update({
                'has_bankruptcy': snapshot.get('bankruptcy_proceedings', False),
                'special_attention_account': snapshot.get('special_attention_account', False),
                'total_outstanding_facilities': snapshot.get('outstanding_facilities', {}).get('count', 0),
                'total_outstanding_value': snapshot.get('outstanding_facilities', {}).get('value', 0.0),
                'has_installments_in_arrears': snapshot.get('outstanding_facilities', {}).get('has_arrears', False),
                'credit_applications_12m': snapshot.get('credit_applications_12months', {})
            })
        
        # Normalize loans
        if 'loan_information' in extracted_data:
            for loan in extracted_data['loan_information']:
                normalized_loan = {
                    'loan_id': f"{loan.get('lender', '')}_{loan.get('date', '')}".replace(' ', '_'),
                    'date_opened': _parse_date(loan.get('date', '')),
                    'lender_name': loan.get('lender', '').strip(),
                    'lender_type': _classify_lender_type(loan.get('lender', '')),
                    'facility_type': loan.get('facility_type', ''),
                    'facility_description': loan.get('facility_type_desc', ''),
                    'outstanding_balance': loan.get('outstanding_balance', 0.0),
                    'credit_limit': loan.get('limit', 0.0),
                    'utilization_ratio': loan.get('utilization_ratio', 0.0),
                    'repayment_term_amount': loan.get('repayment_term_amount', 0.0),
                    'repayment_frequency': loan.get('repayment_term_type', ''),
                    'collateral_type': loan.get('collateral_type', ''),
                    'payment_history': loan.get('payment_history_12months', []),
                    'months_in_arrears': loan.get('months_in_arrears', 0),
                    'is_revolving': loan.get('facility_type') in ['CRDTCARD', 'OVRDRAFT']
                }
                
                # Add derived fields for rule evaluation
                normalized_loan['is_secured'] = normalized_loan['collateral_type'] != 'Clean'
                normalized_loan['is_maxed_out'] = normalized_loan['utilization_ratio'] >= 100
                normalized_loan['is_high_utilization'] = normalized_loan['utilization_ratio'] > 80
                normalized_loan['has_recent_arrears'] = normalized_loan['months_in_arrears'] > 0
                normalized_loan['has_serious_delinquency'] = normalized_loan['months_in_arrears'] >= 3
                
                normalized['loan_accounts'].append(normalized_loan)
        
        # Normalize credit applications
        if 'credit_applications' in extracted_data:
            for app in extracted_data['credit_applications']:
                normalized_app = {
                    'application_date': _parse_date(app.get('application_date', '')),
                    'lender': app.get('lender', '').strip(),
                    'facility_type': app.get('facility_type', ''),
                    'amount': app.get('amount', 0.0),
                    'status': app.get('status', ''),
                    'property_status': app.get('property_status', ''),
                    'property_address': app.get('property_address', '')
                }
                
                # Classify as high-risk facility
                high_risk_types = ['MICROEFN', 'unsecured personal loan', 'payday loan']
                normalized_app['is_high_risk_facility'] = any(risk_type in normalized_app['facility_type'].lower() 
                                                              for risk_type in high_risk_types)
                
                normalized['credit_applications'].append(normalized_app)
        
        # Normalize legal cases
        if 'legal_cases' in extracted_data:
            for case in extracted_data['legal_cases']:
                normalized_case = {
                    'case_type': case.get('case_type', ''),
                    'case_number': case.get('case_number', ''),
                    'plaintiff': case.get('plaintiff', '').strip(),
                    'amount': case.get('amount', 0.0),
                    'action_date': _parse_date(case.get('action_date') or case.get('notice_date') or case.get('petition_date', '')),
                    'settlement_status': case.get('settlement_status', 'Unsettled'),
                    'settled_date': _parse_date(case.get('settled_date', '')),
                    'is_bankruptcy': 'bankruptcy' in case.get('case_type', '').lower(),
                    'is_winding_up': 'winding' in case.get('case_type', '').lower(),
                    'is_personal_capacity': 'Non-Personal' not in case.get('case_type', '')
                }
                normalized['legal_records'].append(normalized_case)
        
        # Normalize trade references
        if 'trade_references' in extracted_data:
            for ref in extracted_data['trade_references']:
                normalized_ref = {
                    'referee_name': ref.get('referee_name', '').strip(),
                    'account_number': ref.get('account_number', ''),
                    'statement_date': _parse_date(ref.get('statement_date', '')),
                    'default_amount': ref.get('default_amount', 0.0),
                    'credit_limit': ref.get('credit_limit', 0.0),
                    'credit_terms_days': ref.get('credit_terms_days', 0),
                    'account_conduct': ref.get('account_conduct', ''),
                    'aging_breakdown': ref.get('aging', {}),
                    'has_returned_cheque': 'returned_cheque' in ref,
                    'returned_cheque_details': ref.get('returned_cheque', {}),
                    'reminder_count': ref.get('reminder_count', 0)
                }
                
                # Calculate total outstanding from aging
                if normalized_ref['aging_breakdown']:
                    normalized_ref['total_outstanding'] = sum(normalized_ref['aging_breakdown'].values())
                
                normalized['trade_references'].append(normalized_ref)
        
        # Normalize directorships
        if 'directorships' in extracted_data:
            for company in extracted_data['directorships']:
                normalized_company = {
                    'company_name': company.get('company_name', '').strip(),
                    'status': company.get('status', ''),
                    'position': company.get('position', ''),
                    'appointed_date': _parse_date(company.get('appointed_date', '')),
                    'resigned_date': _parse_date(company.get('resigned_date', '')),
                    'shareholding_percentage': company.get('shareholding_percentage', 0.0),
                    'shares_value': company.get('shares', 0.0),
                    'is_active': company.get('status') in ['EXISTING', 'ACTIVE']
                }
                normalized['directorships'].append(normalized_company)
        
        # Calculate behavioral indicators for rule matching
        normalized['behavioral_indicators'] = _calculate_behavioral_indicators(normalized)
        
        # Add metadata
        normalized['report_metadata'] = {
            'extraction_date': datetime.now().isoformat(),
            'total_loans': len(normalized['loan_accounts']),
            'total_applications': len(normalized['credit_applications']),
            'total_legal_cases': len(normalized['legal_records']),
            'total_trade_refs': len(normalized['trade_references'])
        }
        
    except Exception as e:
        print(f"Error normalizing data: {e}")
    
    return normalized


def _parse_date(date_str: str) -> str:
    """Parse and standardize date formats"""
    if not date_str:
        return None
    
    try:
        # Handle DD-MM-YYYY format
        if '-' in date_str and len(date_str) == 10:
            parts = date_str.split('-')
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"  # Convert to YYYY-MM-DD
        # Handle YYYY-MM-DD format (already standardized)
        elif date_str.count('-') == 2:
            return date_str
    except:
        pass
    
    return date_str


def _classify_lender_type(lender_name: str) -> str:
    """Classify lender as bank or non-bank"""
    bank_keywords = ['BANK', 'CIMB', 'MAYBANK', 'PUBLIC BANK', 'RHB', 'HONG LEONG', 
                     'AFFIN', 'ALLIANCE', 'AMBANK', 'OCBC', 'HSBC', 'STANDARD CHARTERED']
    
    lender_upper = lender_name.upper()
    
    for keyword in bank_keywords:
        if keyword in lender_upper:
            return 'Bank'
    
    return 'Non-Bank'


def _calculate_behavioral_indicators(normalized_data: Dict) -> Dict:
    """Calculate aggregate behavioral indicators for rule matching"""
    indicators = {}
    
    try:
        loans = normalized_data.get('loan_accounts', [])
        applications = normalized_data.get('credit_applications', [])
        legal_records = normalized_data.get('legal_records', [])
        trade_refs = normalized_data.get('trade_references', [])
        
        # Loan-based indicators
        if loans:
            indicators['number_of_loans'] = len(loans)
            indicators['total_credit_limit'] = sum(loan['credit_limit'] for loan in loans)
            indicators['total_outstanding'] = sum(loan['outstanding_balance'] for loan in loans)
            indicators['average_utilization'] = sum(loan['utilization_ratio'] for loan in loans) / len(loans)
            
            # Count revolving vs term loans
            revolving_loans = [l for l in loans if l['is_revolving']]
            indicators['number_of_revolving_accounts'] = len(revolving_loans)
            
            # Count loans with arrears
            indicators['loans_with_arrears'] = sum(1 for loan in loans if loan['has_recent_arrears'])
            indicators['loans_with_serious_delinquency'] = sum(1 for loan in loans if loan['has_serious_delinquency'])
            
            # Calculate average months in arrears
            total_arrears = sum(loan['months_in_arrears'] for loan in loans)
            indicators['average_months_in_arrears'] = total_arrears / len(loans) if loans else 0
            
            # Count distinct account types
            account_types = set(loan['facility_type'] for loan in loans)
            indicators['distinct_account_types'] = len(account_types)
            
            # Bank vs non-bank ratio
            bank_accounts = sum(1 for loan in loans if loan['lender_type'] == 'Bank')
            nonbank_accounts = len(loans) - bank_accounts
            indicators['bank_to_nonbank_ratio'] = bank_accounts / len(loans) if loans else 0
            
        # Application-based indicators
        if applications:
            indicators['num_applications_last_12_months'] = len(applications)
            indicators['num_pending_applications'] = sum(1 for app in applications if app['status'] == 'Pending')
            
            # Calculate approval rate
            approved = sum(1 for app in applications if app['status'] == 'Approved')
            indicators['approval_rate'] = (approved / len(applications) * 100) if applications else 0
            indicators['decline_rate'] = 100 - indicators['approval_rate']
            
            # High-risk facility applications
            high_risk_apps = sum(1 for app in applications if app.get('is_high_risk_facility', False))
            indicators['high_risk_applications'] = high_risk_apps
            
        # Legal indicators
        if legal_records:
            indicators['total_legal_cases'] = len(legal_records)
            indicators['bankruptcy_cases'] = sum(1 for case in legal_records if case['is_bankruptcy'])
            indicators['unsettled_legal_cases'] = sum(1 for case in legal_records if case['settlement_status'] != 'Fully Settled')
            
            # Calculate total legal exposure
            indicators['total_legal_amount'] = sum(case['amount'] for case in legal_records if case['amount'])
            
        # Trade reference indicators
        if trade_refs:
            indicators['total_trade_accounts'] = len(trade_refs)
            indicators['unsatisfactory_trade_conduct'] = sum(1 for ref in trade_refs if ref['account_conduct'] == 'Unsatisfactory')
            indicators['returned_cheques'] = sum(1 for ref in trade_refs if ref['has_returned_cheque'])
            indicators['total_trade_reminders'] = sum(ref['reminder_count'] for ref in trade_refs)
            
    except Exception as e:
        print(f"Error calculating behavioral indicators: {e}")
    
    return indicators


def save_to_json(normalized_data: Dict, output_file: str):
    """Save normalized data to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(normalized_data, json_file, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {output_file}")
    except Exception as e:
        print(f"Error saving JSON: {e}")


# Example usage
if __name__ == "__main__":
    # Update with your actual PDF path
    pdf_file = 'data/sample_ctos_report.pdf'
    
    # Initialize parser
    parser = CTOSReportParser(pdf_file)
    
    # Extract data
    print("Extracting data from PDF...")
    extracted_data = parser.extract_data_from_pdf()
    
    # Normalize data
    print("Normalizing data...")
    normalized_data = normalize_data(extracted_data)
    
    # Save to JSON
    print("Saving to JSON...")
    save_to_json(normalized_data, 'output/normalized_credit_data.json')
    
    # Print summary
    print("\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    print(f"Personal Info: {normalized_data['personal_info'].get('full_name', 'N/A')}")
    print(f"CTOS Score: {normalized_data['credit_profile'].get('ctos_score', 'N/A')}")
    print(f"Total Loans: {len(normalized_data['loan_accounts'])}")
    print(f"Total Applications: {len(normalized_data['credit_applications'])}")
    print(f"Legal Cases: {len(normalized_data['legal_records'])}")
    print(f"Trade References: {len(normalized_data['trade_references'])}")
    print(f"Directorships: {len(normalized_data['directorships'])}")
    print("="*50)