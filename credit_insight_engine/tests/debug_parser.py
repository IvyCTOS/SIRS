"""
Debug script to see what's actually in the PDF loan section
"""

import PyPDF2
import re
from pathlib import Path

def debug_loan_section(pdf_path):
    """Extract and display loan section for debugging"""
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
    
    print(f"Total characters: {len(full_text)}")
    print("\n" + "="*80)
    
    # Find loan section
    loan_section = re.search(
        r'Loan Information\s+Maklumat Pinjaman(.*?)(?=Special Attention|Credit Application|REMARK LEGEND)',
        full_text,
        re.DOTALL | re.IGNORECASE
    )
    
    if loan_section:
        loan_text = loan_section.group(1)
        print("FOUND LOAN SECTION")
        print("="*80)
        print(f"Section length: {len(loan_text)} chars")
        print("\nFirst 1500 characters:")
        print("-"*80)
        print(loan_text[:1500])
        print("-"*80)
        
        # Test facility pattern
        print("\nSearching for facility patterns...")
        facility_pattern = r'O\s+(OTLNFNCE|CRDTCARD|HSLNFNCE|PCPASCAR|OVRDRAFT|MICROEFN)\s+([\d,]+\.?\d*)'
        
        matches = list(re.finditer(facility_pattern, loan_text))
        print(f"Found {len(matches)} facilities\n")
        
        for i, match in enumerate(matches[:3]):  # Show first 3
            print(f"Facility {i+1}:")
            print(f"  Type: {match.group(1)}")
            print(f"  Balance: {match.group(2)}")
            print(f"  Position: {match.start()}")
            
            # Show context
            start = max(0, match.start() - 200)
            end = min(len(loan_text), match.end() + 200)
            context = loan_text[start:end]
            print(f"  Context:\n{context}\n")
    else:
        print("⚠ LOAN SECTION NOT FOUND")
        
        # Try to find where loan info might be
        print("\nSearching for 'Outstanding Credit'...")
        outstanding_match = re.search(r'Outstanding Credit.*', full_text, re.IGNORECASE)
        if outstanding_match:
            pos = outstanding_match.start()
            print(f"Found at position {pos}")
            print(full_text[pos:pos+500])
    
    print("\n" + "="*80)
    print("\nSearching for row patterns...")
    row_pattern = r'(\d+)\s+(\d{2}-\d{2}-\d{4})\s+Own'
    row_matches = list(re.finditer(row_pattern, full_text))
    print(f"Found {len(row_matches)} row headers")
    
    for i, match in enumerate(row_matches[:3]):
        print(f"\nRow {i+1}:")
        print(f"  Number: {match.group(1)}")
        print(f"  Date: {match.group(2)}")
        # Show what comes after
        pos = match.end()
        print(f"  After 'Own': {full_text[pos:pos+100]}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = Path(__file__).parent / "data" / "Blanked-New-Sample-Score-Report.pdf"
    
    print(f"Analyzing: {pdf_path}\n")
    debug_loan_section(pdf_path)