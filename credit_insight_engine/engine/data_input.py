"""
Fixed PDF Parser for CTOS Credit Reports
Extracts data from actual CTOS report structure
"""

from datetime import datetime
from typing import Dict, List, Any
import PyPDF2
import re
import logging

logging.basicConfig(level=logging.INFO)

class CTOSReportParser:
    """Parser for CTOS Credit Reports"""
    
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.logger = logging.getLogger(__name__)
        self.full_text = ""

    def extract_data_from_pdf(self) -> Dict:
        """Extract raw data from PDF file"""
        try:
            # Read entire PDF
            with open(self.pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    self.full_text += page.extract_text() + "\n"
            
            self.logger.info(f"Extracted {len(self.full_text)} characters from PDF")
            
            # Extract all data sections
            extracted_data = {
                # Personal info
                'name': self._extract_name(),
                'ic_number': self._extract_ic(),
                'ctos_score': self._extract_ctos_score(),
                
                # Credit summary from snapshot
                'numberofloans': self._extract_number_of_loans(),
                'total_outstanding': self._extract_total_outstanding(),
                'total_limit': self._extract_total_limit(),
                
                # Extract individual loans from CCRIS section
                'loans': self._extract_loans_from_ccris(),
                
                # Applications
                'numapplicationslast12months': self._extract_applications(),
                
                # Calculate derived fields
                'creditutilizationratio': 0,  # Will calculate from loans
                'mon_arrears': 0,  # Will get from payment history
                'inst_arrears': 0
            }
            
            # Calculate utilization from loans
            if extracted_data['loans']:
                total_balance = sum(loan['balance'] for loan in extracted_data['loans'])
                total_limit = sum(loan['limit'] for loan in extracted_data['loans'])
                
                if total_limit > 0:
                    extracted_data['creditutilizationratio'] = (total_balance / total_limit) * 100
                
                # Get worst arrears from any loan
                extracted_data['mon_arrears'] = max(loan.get('arrears', 0) for loan in extracted_data['loans'])
                extracted_data['inst_arrears'] = extracted_data['mon_arrears']

            self.logger.info(f"Extracted data: {extracted_data}")
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error extracting data: {e}")
            return {}

    def _extract_name(self) -> str:
        """Extract person's name"""
        match = re.search(r'Name.*?Nama\s+([A-Z\s]+?)(?:\n|New ID)', self.full_text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_ic(self) -> str:
        """Extract IC number"""
        match = re.search(r'New ID.*?ID Baru\s+(\d+)', self.full_text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_ctos_score(self) -> int:
        """Extract CTOS Score"""
        # Look for the score number (usually 3 digits)
        match = re.search(r'(?:300|400|500|600)\s+(\d{3})\s+(?:700|800|850)', self.full_text)
        if match:
            return int(match.group(1))
        return 0

    def _extract_number_of_loans(self) -> int:
        """Extract number of outstanding loans from snapshot"""
        match = re.search(r'Outstanding credit facilities.*?Number.*?(\d+)', self.full_text, re.DOTALL)
        if match:
            return int(match.group(1))
        return 0

    def _extract_total_outstanding(self) -> float:
        """Extract total outstanding balance from snapshot"""
        match = re.search(r'Outstanding credit facilities.*?Value.*?([\d,]+\.?\d*)', self.full_text, re.DOTALL)
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0

    def _extract_total_limit(self) -> float:
        """Extract total credit limit from CCRIS summary"""
        match = re.search(r'Total Limit.*?Had Jumlah\s+([\d,]+\.?\d*)', self.full_text)
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0

    def _extract_applications(self) -> int:
        """Extract number of credit applications in last 12 months"""
        match = re.search(r'Credit applications in past 12 months.*?Total.*?(\d+)', self.full_text, re.DOTALL)
        if match:
            return int(match.group(1))
        return 0

    def _extract_loans_from_ccris(self) -> List[Dict]:
        """Extract individual loan details from CCRIS Loan Information table"""
        loans = []
        
        try:
            # Find the CCRIS Loan Information section (Page 8)
            loan_section = re.search(
                r'Loan Information.*?Outstanding Credit.*?(.*?)(?=Total Outstanding Balance|Special Attention|REMARK LEGEND)',
                self.full_text,
                re.DOTALL
            )
            
            if not loan_section:
                self.logger.warning("Could not find loan information section")
                return loans
            
            loan_text = loan_section.group(1)
            
            # Parse each loan row
            # Pattern matches rows like: "1  01-01-2002  Own  CIMB  OTLNFNCE  2,340.00  31-10-2023  10,000.00  00  780.00  MTH"
            loan_pattern = re.compile(
                r'(\d+)\s+'  # Loan number
                r'(\d{2}-\d{2}-\d{4})\s+'  # Date
                r'(?:Own|Guarantor)\s+'  # Capacity
                r'([A-Za-z\s]+?)\s+'  # Lender (multiple words)
                r'(\d+(?:,\d{3})*\.?\d*)\s+'  # Limit/Amount
                r'(\d{2})\s*'  # Collateral type
                r'(?:O|C|S)\s+'  # Status
                r'([A-Z]+)\s+'  # Facility type
                r'([\d,]+\.?\d*)\s+'  # Outstanding balance
                r'(\d{2}-\d{2}-\d{4})\s+'  # Date updated
                r'([\d,]+\.?\d*)\s+'  # Repayment amount
                r'(MTH|IDF)',  # Repayment term
                re.MULTILINE
            )
            
            # Alternative: Look for facility types and extract data around them
            facility_types = ['OTLNFNCE', 'CRDTCARD', 'HSLNFNCE', 'PCPASCAR', 'OVRDRAFT', 'MICROEFN']
            
            for facility in facility_types:
                # Find all occurrences of this facility type
                for match in re.finditer(rf'O\s+{facility}\s+([\d,]+\.?\d*)\s+(\d{{2}}-\d{{2}}-\d{{4}})\s+([\d,]+\.?\d*)', loan_text):
                    balance = float(match.group(1).replace(',', ''))
                    limit = float(match.group(3).replace(',', ''))
                    
                    loan = {
                        'facility_type': facility,
                        'balance': balance,
                        'limit': limit,
                        'utilization': (balance / limit * 100) if limit > 0 else 0,
                        'arrears': 0  # Will be extracted from payment history if available
                    }
                    
                    # Try to extract arrears from conduct column
                    # Look for payment history pattern like "0 0 1 2 0 0"
                    conduct_match = re.search(rf'{facility}.*?(\d+)\s+(\d+)\s+(\d+)', loan_text)
                    if conduct_match:
                        # Count non-zero values as arrears
                        arrears = sum(1 for x in [conduct_match.group(1), conduct_match.group(2), conduct_match.group(3)] if int(x) > 0)
                        loan['arrears'] = arrears
                    
                    loans.append(loan)
            
            self.logger.info(f"Extracted {len(loans)} loans from CCRIS")
            
        except Exception as e:
            self.logger.error(f"Error extracting loans: {e}")
        
        return loans


def normalize_data(extracted_data: Dict) -> Dict:
    """
    Normalize extracted data into format expected by rule engine
    """
    try:
        # Get loans list
        loans = extracted_data.get('loans', [])
        
        # Create records for each loan
        loan_records = []
        for loan in loans:
            record = {
                # Basic loan info
                'loantype': _map_facility_type(loan.get('facility_type', '')),
                'loan_type': loan.get('facility_type', ''),
                'lendertype': 'Bank',  # Most CCRIS are banks
                
                # Financial details
                'balance': loan.get('balance', 0),
                'limit': loan.get('limit', 0),
                'creditutilizationratio': loan.get('utilization', 0),
                
                # Payment history
                'mon_arrears': loan.get('arrears', 0),
                'inst_arrears': loan.get('arrears', 0),
                
                # Derived flags
                'maxed_out': loan.get('balance', 0) >= loan.get('limit', 0) if loan.get('limit', 0) > 0 else False
            }
            loan_records.append(record)
        
        # Create aggregate record for overall indicators
        aggregate_record = {
            'numberofloans': extracted_data.get('numberofloans', len(loans)),
            'creditutilizationratio': extracted_data.get('creditutilizationratio', 0),
            'mon_arrears': extracted_data.get('mon_arrears', 0),
            'inst_arrears': extracted_data.get('inst_arrears', 0),
            'numapplicationslast12months': extracted_data.get('numapplicationslast12months', 0),
            'balance': extracted_data.get('total_outstanding', 0),
            'limit': extracted_data.get('total_limit', 0)
        }
        
        # Combine all records
        all_records = loan_records + [aggregate_record] if aggregate_record else loan_records
        
        logging.info(f"Normalized into {len(all_records)} records")
        return {
            'records': all_records,
            'personal_info': {
                'name': extracted_data.get('name', ''),
                'ic_number': extracted_data.get('ic_number', ''),
                'ctos_score': extracted_data.get('ctos_score', 0)
            }
        }

    except Exception as e:
        logging.error(f"Error normalizing data: {e}")
        return {'records': [], 'personal_info': {}}


def _map_facility_type(facility_code: str) -> str:
    """Map facility codes to readable names"""
    mapping = {
        'OTLNFNCE': 'Other Term Loan',
        'CRDTCARD': 'Credit Card',
        'HSLNFNCE': 'Housing Loan',
        'PCPASCAR': 'Car Loan',
        'OVRDRAFT': 'Overdraft',
        'MICROEFN': 'Micro Enterprise Fund'
    }
    return mapping.get(facility_code, facility_code)


def extract_data_from_pdf(pdf_file: str) -> dict:
    """Module-level function to extract data from PDF"""
    parser = CTOSReportParser(pdf_file)
    return parser.extract_data_from_pdf()


# Expose the functions
__all__ = ['CTOSReportParser', 'extract_data_from_pdf', 'normalize_data']