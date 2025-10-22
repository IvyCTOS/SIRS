"""
CTOS Parser - XML VERSION
Extracts data from CTOS XML reports instead of PDF
"""

from datetime import datetime
from typing import Dict, List, Any, Tuple
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO)

class CTOSReportParser:
    """Parser for CTOS Credit Reports (XML format)"""
    
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.logger = logging.getLogger(__name__)
        self.root = None
        self.ns = {'ns': 'http://ws.cmctos.com.my/ctosnet/response'}

    def extract_data_from_xml(self) -> Dict:
        """Extract raw data from XML file"""
        try:
            tree = ET.parse(self.xml_file)
            self.root = tree.getroot()
            
            self.logger.info(f"Parsed XML file: {self.xml_file}")
            
            extracted_data = {
                'name': self._extract_name(),
                'ic_number': self._extract_ic(),
                'ctos_score': self._extract_ctos_score(),
                'numberofloans': 0,  # Will be calculated from loans
                'total_outstanding': 0,  # Will be calculated from loans
                'total_limit': 0,  # Will be calculated from loans
                'loans': self._extract_loans_from_ccris(),
                'numapplicationslast12months': self._extract_applications(),
                'numpendingapplications': self._extract_pending_applications(),
                'trade_references': self._extract_trade_references(),
                'legal_cases': self._extract_legal_cases(),
                'director_winding_up': self._extract_director_winding_up(),
                'creditutilizationratio': 0,
                'payment_conduct_code': 0,
                'oldest_account_months': 0,
                'distinct_account_types': 0
            }
            
            # Log extracted legal cases
            self.logger.info(f"✓ Extracted legal_cases: {extracted_data.get('legal_cases', [])}")
            
            # Calculate totals from loans
            if extracted_data['loans']:
                extracted_data['numberofloans'] = len(extracted_data['loans'])
                extracted_data['total_outstanding'] = sum(loan['balance'] for loan in extracted_data['loans'])
                extracted_data['total_limit'] = sum(loan['limit'] for loan in extracted_data['loans'])
                
                # Calculate revolving utilization
                revolving_loans = [l for l in extracted_data['loans'] 
                                  if l['facility_type'] in ['CRDTCARD', 'OVRDRAFT']]
                
                if revolving_loans:
                    total_balance = sum(loan['balance'] for loan in revolving_loans)
                    total_limit = sum(loan['limit'] for loan in revolving_loans)
                    
                    if total_limit > 0:
                        extracted_data['creditutilizationratio'] = (total_balance / total_limit) * 100
                        self.logger.info(f"Overall revolving utilization: {extracted_data['creditutilizationratio']:.1f}%")
                
                extracted_data['payment_conduct_code'] = max(
                    loan.get('payment_conduct_code', 0) for loan in extracted_data['loans']
                )
                
                extracted_data['distinct_account_types'] = len(
                    set(loan['facility_type'] for loan in extracted_data['loans'])
                )
                
                extracted_data['oldest_account_months'] = self._calculate_oldest_account(
                    extracted_data['loans']
                )

            self.logger.info(f"✓ Extracted {len(extracted_data['loans'])} loans")
            self.logger.info(f"✓ Trade refs: {len(extracted_data['trade_references'])} accounts")
            self.logger.info(f"✓ Legal cases: {len(extracted_data['legal_cases'])} cases")
            
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error extracting data: {e}", exc_info=True)
            return {}

    def _extract_name(self) -> str:
        """Extract name from XML"""
        try:
            name_elem = self.root.find('.//ns:enq_sum/ns:name', self.ns)
            return name_elem.text.strip() if name_elem is not None and name_elem.text else ""
        except Exception as e:
            self.logger.error(f"Error extracting name: {e}")
            return ""

    def _extract_ic(self) -> str:
        """Extract IC/NRIC number from XML"""
        try:
            ic_elem = self.root.find('.//ns:enq_sum/ns:nic_brno', self.ns)
            return ic_elem.text.strip() if ic_elem is not None and ic_elem.text else ""
        except Exception as e:
            self.logger.error(f"Error extracting IC: {e}")
            return ""

    def _extract_ctos_score(self) -> int:
        """Extract CTOS/FICO score from XML"""
        try:
            score_elem = self.root.find('.//ns:enq_sum/ns:fico_index', self.ns)
            if score_elem is not None:
                score = score_elem.get('score')
                return int(score) if score else 0
            return 0
        except Exception as e:
            self.logger.error(f"Error extracting CTOS score: {e}")
            return 0

    def _extract_applications(self) -> int:
        """Extract number of credit applications in past 12 months"""
        try:
            # From CCRIS summary
            summary = self.root.find('.//ns:section_ccris/ns:summary/ns:application', self.ns)
            if summary is not None:
                approved = summary.find('ns:approved', self.ns)
                pending = summary.find('ns:pending', self.ns)
                
                approved_count = int(approved.get('count', 0)) if approved is not None else 0
                pending_count = int(pending.get('count', 0)) if pending is not None else 0
                
                return approved_count + pending_count
            return 0
        except Exception as e:
            self.logger.error(f"Error extracting applications: {e}")
            return 0

    def _extract_pending_applications(self) -> int:
        """Extract number of pending applications"""
        try:
            summary = self.root.find('.//ns:section_ccris/ns:summary/ns:application/ns:pending', self.ns)
            if summary is not None:
                return int(summary.get('count', 0))
            return 0
        except Exception as e:
            self.logger.error(f"Error extracting pending applications: {e}")
            return 0

    def _extract_loans_from_ccris(self) -> List[Dict]:
        """Extract loans from CCRIS section"""
        loans = []
        
        try:
            # Extract from regular accounts
            accounts = self.root.findall('.//ns:section_ccris/ns:accounts/ns:account', self.ns)
            for account in accounts:
                loan = self._parse_account(account, is_special_attention=False)
                if loan:
                    loans.append(loan)
            
            # Extract from special attention accounts
            special_accounts = self.root.findall('.//ns:section_ccris/ns:special_attention_accs/ns:special_attention_acc', self.ns)
            for account in special_accounts:
                loan = self._parse_account(account, is_special_attention=True)
                if loan:
                    loans.append(loan)
            
        except Exception as e:
            self.logger.error(f"Error extracting loans: {e}", exc_info=True)
        
        return loans

    def _parse_account(self, account_elem, is_special_attention=False) -> Dict:
        """Parse a single account element"""
        try:
            # Extract basic info
            approval_date = self._get_text(account_elem, 'ns:approval_date')
            lender_type_elem = account_elem.find('ns:lender_type', self.ns)
            
            # Get full lender name (text content), fallback to code attribute
            if lender_type_elem is not None:
                lender = lender_type_elem.text.strip() if lender_type_elem.text else lender_type_elem.get('code', 'Unknown')
            else:
                lender = 'Unknown'
            
            limit = float(self._get_text(account_elem, 'ns:limit', '0'))
            
            # Extract sub-account (facility) info
            sub_account = account_elem.find('.//ns:sub_account', self.ns)
            if sub_account is None:
                return None
            
            facility_elem = sub_account.find('ns:facility', self.ns)
            facility_type = facility_elem.get('code', 'UNKNOWN') if facility_elem is not None else 'UNKNOWN'
            
            # Get latest position (first cr_position with balance)
            cr_positions = sub_account.findall('.//ns:cr_position', self.ns)
            if not cr_positions:
                return None
            
            latest_position = cr_positions[0]
            balance = float(self._get_text(latest_position, 'ns:balance', '0'))
            
            # Extract payment conduct (inst_arrears from last 12 months)
            conduct_codes = []
            for pos in cr_positions[:12]:  # Last 12 months
                inst_arrears = int(self._get_text(pos, 'ns:inst_arrears', '0'))
                # Convert arrears to conduct code (0=current, 1=1 month late, etc.)
                conduct_code = min(inst_arrears, 8)  # Cap at 8
                conduct_codes.append(conduct_code)
            
            # Pad to 12 months if needed
            while len(conduct_codes) < 12:
                conduct_codes.append(0)
            
            payment_conduct_code = max(conduct_codes)
            
            # Check if all conduct codes are zero (perfect payment history)
            payment_conduct_all_zero = all(code == 0 for code in conduct_codes)
            
            # Calculate utilization
            utilization = (balance / limit * 100) if limit > 0 else 0
            
            loan = {
                'facility_type': facility_type,
                'lender': lender,
                'balance': balance,
                'limit': limit,
                'utilization': utilization,
                'date_opened': approval_date,
                'payment_conduct_code': payment_conduct_code,
                'conduct_codes': conduct_codes,
                'payment_conduct_all_zero': payment_conduct_all_zero,
                'is_special_attention': is_special_attention
            }
            
            self.logger.info(
                f"✓ {facility_type} from {lender}, "
                f"Balance=RM {balance:,.2f}, Limit=RM {limit:,.2f}, "
                f"Util={utilization:.1f}%, Conduct={payment_conduct_code}"
            )
            
            return loan
            
        except Exception as e:
            self.logger.error(f"Error parsing account: {e}")
            return None

    def _extract_trade_references(self) -> List[Dict]:
        """Extract trade references from Section E"""
        trade_refs = []
        
        try:
            # Check if Section E has data
            section_e = self.root.find('.//ns:section_e', self.ns)
            if section_e is None or section_e.get('data') != 'true':
                self.logger.info("No trade reference data found")
                return trade_refs
            
            # Extract trade reference records
            records = section_e.findall('.//ns:record', self.ns)
            for record in records:
                account = self._get_text(record, 'ns:account_no', '')
                amount = float(self._get_text(record, 'ns:amount', '0').replace(',', ''))
                
                # Extract aging bucket from remark
                remark = self._get_text(record, 'ns:remark', '')
                aging_bucket = 'None'
                if 'days' in remark.lower():
                    # Extract aging info
                    aging_bucket = remark
                
                trade_refs.append({
                    'account': account,
                    'amount': amount,
                    'aging_bucket': aging_bucket
                })
                
                self.logger.info(f"✓ Trade ref {account}: RM {amount:,.2f} in {aging_bucket}")
            
        except Exception as e:
            self.logger.error(f"Error extracting trade refs: {e}")
        
        return trade_refs

    def _extract_legal_cases(self) -> List[Dict]:
        """Extract legal cases from Section D"""
        legal_cases = []
        
        try:
            # Extract from Section D (legal cases)
            section_d = self.root.find('.//ns:section_d', self.ns)
            if section_d is None:
                self.logger.warning("⚠️  Section D not found in XML")
                return legal_cases
            
            has_data = section_d.get('data')
            self.logger.info(f"Section D found, data attribute: {has_data}")
            
            if has_data != 'true':
                self.logger.info("Section D has no data (data != 'true')")
                return legal_cases
            
            records = section_d.findall('.//ns:record', self.ns)
            self.logger.info(f"Found {len(records)} legal case records in Section D")
            
            for record in records:
                title = self._get_text(record, 'ns:title', '')
                plaintiff = self._get_text(record, 'ns:plaintiff', 'Unknown')
                amount_str = self._get_text(record, 'ns:amount', '0')
                amount = float(amount_str.replace(',', '')) if amount_str else 0
                
                settlement = self._get_text(record, 'ns:settlement', '')
                is_settled = 'SETTLED' in settlement.upper() if settlement else False
                status = 'CASE FULLY SETTLED' if is_settled else 'ACTIVE'
                
                legal_cases.append({
                    'case_type': title,
                    'amount': amount,
                    'plaintiff': plaintiff,
                    'status': status,
                    'is_settled': is_settled
                })
                
                self.logger.info(f"✓ Legal case: {title}, Plaintiff={plaintiff}, RM {amount:,.2f}, Status={status}")
            
        except Exception as e:
            self.logger.error(f"Error extracting legal cases: {e}", exc_info=True)
        
        return legal_cases

    def _extract_director_winding_up(self) -> List[Dict]:
        """Extract director winding up cases from Section D4"""
        winding_up = []
        
        try:
            section_d4 = self.root.find('.//ns:section_d4', self.ns)
            if section_d4 is None or section_d4.get('data') != 'true':
                self.logger.info("No director winding-up data found")
                return winding_up
            
            records = section_d4.findall('.//ns:record', self.ns)
            for record in records:
                company_name = self._get_text(record, 'ns:name', 'Unknown Company')
                settlement = self._get_text(record, 'ns:settlement', '')
                status = settlement if settlement else 'ACTIVE'
                
                winding_up.append({
                    'company_name': company_name,
                    'status': status,
                    'is_active': 'SETTLED' not in status.upper()
                })
                
                self.logger.info(f"✓ Director winding-up: {company_name}, Status: {status}")
        
        except Exception as e:
            self.logger.error(f"Error extracting D4: {e}")
        
        return winding_up

    def _calculate_oldest_account(self, loans: List[Dict]) -> int:
        """Calculate months since oldest account"""
        if not loans:
            return 0
        
        dates_opened = [loan.get('date_opened') for loan in loans if loan.get('date_opened')]
        
        if not dates_opened:
            return 0
        
        try:
            parsed_dates = []
            for date_str in dates_opened:
                # XML format: DD-MM-YYYY
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = parts
                    if int(year) >= 2023:
                        continue
                    parsed_dates.append(datetime(int(year), int(month), int(day)))
            
            if not parsed_dates:
                return 0
            
            oldest_date = min(parsed_dates)
            today = datetime.now()
            
            months_diff = (today.year - oldest_date.year) * 12 + (today.month - oldest_date.month)
            years = months_diff / 12
            
            self.logger.info(f"✓ Oldest account: {oldest_date.strftime('%d-%m-%Y')}, {months_diff} months ({years:.1f} years)")
            return months_diff
            
        except Exception as e:
            self.logger.error(f"Error calculating oldest account: {e}")
            return 0

    def _get_text(self, element, tag, default=''):
        """Helper to safely get text from XML element"""
        elem = element.find(tag, self.ns)
        return elem.text.strip() if elem is not None and elem.text else default


def normalize_data(extracted_data: Dict) -> Dict:
    """Normalize extracted data"""
    try:
        loans = extracted_data.get('loans', [])
        trade_refs = extracted_data.get('trade_references', [])
        legal_cases = extracted_data.get('legal_cases', [])
        director_winding_up = extracted_data.get('director_winding_up', [])
        
        # Loan records
        loan_records = []
        for loan in loans:
            facility_type = loan.get('facility_type', '')
            is_revolving = facility_type in ['CRDTCARD', 'OVRDRAFT']
            
            loan_records.append({
                'Facility': _map_facility_type(facility_type),
                'facility_type': facility_type,
                'loantype': _map_facility_type(facility_type),
                'Lender_Type': loan.get('lender', 'Unknown'),
                'lendertype': loan.get('lender', 'Unknown'),
                'balance': loan.get('balance', 0),
                'limit': loan.get('limit', 0),
                'creditutilizationratio': loan.get('utilization', 0) if is_revolving else 0,
                'payment_conduct_code': loan.get('payment_conduct_code', 0),
                'payment_conduct_all_zero': loan.get('payment_conduct_all_zero', False),
                'is_revolving': is_revolving,
                'account_type': 'revolving' if is_revolving else 'installment'
            })
        
        # Calculate lender concentration
        from collections import Counter
        lender_counts = Counter(loan.get('lender', 'Unknown') for loan in loans)
        accounts_per_lender = max(lender_counts.values()) if lender_counts else 0
        lender_name = max(lender_counts, key=lender_counts.get) if lender_counts else ''
        
        # Calculate secured debt ratio
        secured_balance = 0
        total_balance = sum(loan.get('balance', 0) for loan in loans)
        
        for loan in loans:
            if loan.get('facility_type') in ['HSLNFNCE', 'PCPASCAR']:
                secured_balance += loan.get('balance', 0)
        
        secured_loan_ratio = (secured_balance / total_balance * 100) if total_balance > 0 else 0
        
        # Aggregates
        trade_ref_amount_overdue = sum(ref.get('amount', 0) for ref in trade_refs)
        
        aging_bucket = 'None'
        if trade_refs:
            for ref in trade_refs:
                if ref.get('aging_bucket') and ref['aging_bucket'] != 'None':
                    aging_bucket = ref['aging_bucket']
                    break
        
        legal_cases_settled = len([c for c in legal_cases if c.get('is_settled', False)])
        legal_cases_active = len([c for c in legal_cases if not c.get('is_settled', False)])
        
        logging.info(f"Legal cases: {len(legal_cases)} total, {legal_cases_settled} settled, {legal_cases_active} active")
        
        # DEBUG: Log the legal_cases structure
        if legal_cases:
            logging.info(f"Legal cases data: {legal_cases}")
        
        # Build case_types summary string for active cases
        active_cases = [c for c in legal_cases if not c.get('is_settled', False)]
        logging.info(f"Active cases count: {len(active_cases)}")
        
        if active_cases:
            case_types = ', '.join(c.get('case_type', 'Unknown') for c in active_cases)
            logging.info(f"✓ Active case types: '{case_types}'")
        else:
            case_types = ''
            logging.warning("⚠️  No active cases found for case_types")
        
        # Build case_details for bankruptcy (if any)
        bankruptcy_cases = [c for c in legal_cases if 'BANKRUPTCY' in c.get('case_type', '').upper() and not c.get('is_settled', False)]
        if bankruptcy_cases:
            case_details = f"{bankruptcy_cases[0].get('case_type', 'Bankruptcy')} - Amount: RM {bankruptcy_cases[0].get('amount', 0):,.2f}"
        else:
            case_details = ''
        
        director_windingup_company = len([w for w in director_winding_up if w.get('is_active', False)])
        company_name = director_winding_up[0]['company_name'] if director_winding_up else ''
        
        aggregate_record = {
            'numberofloans': len(loans),
            'numapplicationslast12months': extracted_data.get('numapplicationslast12months', 0),
            'numpendingapplications': extracted_data.get('numpendingapplications', 0),
            'distinct_account_types': extracted_data.get('distinct_account_types', 0),
            'oldest_account_months': extracted_data.get('oldest_account_months', 0),
            'payment_conduct_code': extracted_data.get('payment_conduct_code', 0),
            'has_credit_card': any(l['facility_type'] == 'CRDTCARD' for l in loans),
            'has_installment_loan': any(l['facility_type'] in ['HSLNFNCE', 'PCPASCAR', 'OTLNFNCE'] for l in loans),
            'creditutilizationratio': extracted_data.get('creditutilizationratio', 0),
            'trade_ref_amount_overdue': trade_ref_amount_overdue,
            'trade_ref_reminder_count': len(trade_refs),
            'aging_bucket': aging_bucket,
            'legal_cases_settled': legal_cases_settled,
            'legal_cases_active': legal_cases_active,
            'bankruptcy_active': any('BANKRUPTCY' in c.get('case_type', '') and not c.get('is_settled') for c in legal_cases),
            'director_windingup_company': director_windingup_company,
            'company_name': company_name,
            'accounts_per_lender': accounts_per_lender,
            'lender_name': lender_name,
            'secured_loan_ratio': secured_loan_ratio,
            # Add template variables for legal cases
            'case_types': case_types,
            'case_details': case_details
        }
        
        all_records = loan_records + [aggregate_record]
        
        logging.info(f"\n{'='*60}")
        logging.info(f"NORMALIZED: {len(loan_records)} loans + 1 aggregate")
        logging.info(f"Trade: RM {trade_ref_amount_overdue:,.2f}, Legal: {legal_cases_settled} settled/{legal_cases_active} active")
        logging.info(f"{'='*60}\n")
        
        return {
            'records': all_records,
            'personal_info': {
                'name': extracted_data.get('name', ''),
                'ic_number': extracted_data.get('ic_number', ''),
                'ctos_score': extracted_data.get('ctos_score', 0)
            }
        }

    except Exception as e:
        logging.error(f"Error normalizing: {e}", exc_info=True)
        return {'records': [], 'personal_info': {}}


def _map_facility_type(facility_code: str) -> str:
    """Map facility codes to names"""
    mapping = {
        'OTLNFNCE': 'Other Term Loan',
        'CRDTCARD': 'Credit Card',
        'HSLNFNCE': 'Housing Loan',
        'PCPASCAR': 'Car Loan',
        'OVRDRAFT': 'Overdraft',
        'MICROEFN': 'Micro Enterprise Fund',
        'BUYNPAYL': 'Buy Now Pay Later'
    }
    return mapping.get(facility_code, facility_code)


def extract_data_from_xml(xml_file: str) -> dict:
    """Module-level function for XML extraction"""
    parser = CTOSReportParser(xml_file)
    return parser.extract_data_from_xml()


__all__ = ['CTOSReportParser', 'extract_data_from_xml', 'normalize_data']