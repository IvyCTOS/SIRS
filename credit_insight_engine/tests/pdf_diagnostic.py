"""
PDF Diagnostic Tool - Shows actual extracted text structure
Use this to understand the PDF format and fix extraction patterns
"""

import PyPDF2
import re

def diagnose_pdf(pdf_file: str):
    """Extract and show PDF structure for debugging"""
    
    print("="*80)
    print("PDF DIAGNOSTIC TOOL")
    print("="*80)
    
    # Extract full text
    full_text = ""
    try:
        with open(pdf_file, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"\nTotal pages: {len(reader.pages)}")
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                full_text += page_text + "\n"
                print(f"Page {i+1}: {len(page_text)} characters")
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    print(f"\nTotal characters extracted: {len(full_text)}")
    
    # Save full text for inspection
    with open('pdf_full_text.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    print("✓ Full text saved to: pdf_full_text.txt")
    
    # Find and show loan section
    print("\n" + "="*80)
    print("SECTION 1: LOAN INFORMATION")
    print("="*80)
    
    # Try to find loan section
    loan_patterns = [
        r'Outstanding Credit.*?Kredit Belum Jelas(.*?)(?=Total Outstanding Balance|Special Attention)',
        r'Loan Information.*?Maklumat Pinjaman(.*?)(?=Total Outstanding|Special Attention)',
        r'C1: BANKING.*?CCRIS DETAILS.*?Loan Information(.*?)(?=Special Attention|Total Outstanding)',
    ]
    
    loan_section = None
    for pattern in loan_patterns:
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            loan_section = match.group(1)
            print(f"✓ Found loan section using pattern: {pattern[:50]}...")
            break
    
    if loan_section:
        print(f"\nLoan section length: {len(loan_section)} characters")
        print("\nFirst 1500 characters of loan section:")
        print("-"*80)
        print(loan_section[:1500])
        print("-"*80)
        
        # Save loan section
        with open('pdf_loan_section.txt', 'w', encoding='utf-8') as f:
            f.write(loan_section)
        print("\n✓ Loan section saved to: pdf_loan_section.txt")
        
        # Look for facility types
        print("\nSearching for facility types...")
        facility_types = ['OTLNFNCE', 'CRDTCARD', 'HSLNFNCE', 'PCPASCAR', 'OVRDRAFT', 'MICROEFN']
        for ftype in facility_types:
            count = len(re.findall(ftype, loan_section))
            if count > 0:
                print(f"  ✓ Found {count} x {ftype}")
        
        # Look for pattern around first CRDTCARD
        if 'CRDTCARD' in loan_section:
            print("\nContext around first CRDTCARD:")
            print("-"*80)
            match = re.search(r'.{200}CRDTCARD.{200}', loan_section, re.DOTALL)
            if match:
                print(match.group(0))
            print("-"*80)
    else:
        print("❌ Could not find loan section")
        print("\nSearching for keywords in full text:")
        keywords = ['Outstanding Credit', 'Loan Information', 'CCRIS', 'CRDTCARD', 'Facility']
        for keyword in keywords:
            if keyword in full_text:
                print(f"  ✓ Found: {keyword}")
                # Show context
                match = re.search(r'.{100}' + re.escape(keyword) + r'.{100}', full_text, re.DOTALL)
                if match:
                    print(f"    Context: {match.group(0)[:200]}...")
            else:
                print(f"  ❌ NOT found: {keyword}")
    
    # Find and show trade reference section
    print("\n" + "="*80)
    print("SECTION 2: TRADE REFERENCE")
    print("="*80)
    
    trade_patterns = [
        r'E: TRADE REFERENCE.*?RUJUKAN PERDAGANGAN(.*?)(?=D:|F:|Note:)',
        r'TRADE REFERENCE.*?Summary.*?Ringkasan(.*?)(?=CRA Comment|Subject)',
    ]
    
    trade_section = None
    for pattern in trade_patterns:
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            trade_section = match.group(1)
            print(f"✓ Found trade section using pattern: {pattern[:50]}...")
            break
    
    if trade_section:
        print(f"\nTrade section length: {len(trade_section)} characters")
        print("\nFirst 1000 characters:")
        print("-"*80)
        print(trade_section[:1000])
        print("-"*80)
        
        with open('pdf_trade_section.txt', 'w', encoding='utf-8') as f:
            f.write(trade_section)
        print("\n✓ Trade section saved to: pdf_trade_section.txt")
    else:
        print("❌ Could not find trade reference section")
    
    # Find and show legal section
    print("\n" + "="*80)
    print("SECTION 3: LEGAL CASES")
    print("="*80)
    
    legal_patterns = [
        r'D1: LEGAL CASES.*?SUMMARY.*?RINGKASAN(.*?)(?=D2:|E: TRADE)',
        r'LEGAL CASES.*?DEFENDANT.*?DEFENDAN(.*?)(?=D2:|PLAINTIFF)',
    ]
    
    legal_section = None
    for pattern in legal_patterns:
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            legal_section = match.group(1)
            print(f"✓ Found legal section using pattern: {pattern[:50]}...")
            break
    
    if legal_section:
        print(f"\nLegal section length: {len(legal_section)} characters")
        print("\nFirst 1000 characters:")
        print("-"*80)
        print(legal_section[:1000])
        print("-"*80)
        
        with open('pdf_legal_section.txt', 'w', encoding='utf-8') as f:
            f.write(legal_section)
        print("\n✓ Legal section saved to: pdf_legal_section.txt")
    else:
        print("❌ Could not find legal section")
    
    # Find and show D4 section
    print("\n" + "="*80)
    print("SECTION 4: DIRECTOR WINDING UP (D4)")
    print("="*80)
    
    d4_patterns = [
        r'D4:.*?COMPANY.*?WINDING.*?UP(.*?)(?=E: TRADE|Note:)',
        r'DIRECTOR OF A COMPANY.*?WINDING(.*?)(?=E: TRADE)',
    ]
    
    d4_section = None
    for pattern in d4_patterns:
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            d4_section = match.group(1)
            print(f"✓ Found D4 section using pattern: {pattern[:50]}...")
            break
    
    if d4_section:
        print(f"\nD4 section length: {len(d4_section)} characters")
        print("\nFirst 800 characters:")
        print("-"*80)
        print(d4_section[:800])
        print("-"*80)
        
        with open('pdf_d4_section.txt', 'w', encoding='utf-8') as f:
            f.write(d4_section)
        print("\n✓ D4 section saved to: pdf_d4_section.txt")
    else:
        print("❌ Could not find D4 section")
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    print("\nFiles created:")
    print("  1. pdf_full_text.txt      - Complete extracted text")
    if loan_section:
        print("  2. pdf_loan_section.txt   - Loan information section")
    if trade_section:
        print("  3. pdf_trade_section.txt  - Trade reference section")
    if legal_section:
        print("  4. pdf_legal_section.txt  - Legal cases section")
    if d4_section:
        print("  5. pdf_d4_section.txt     - Director winding up section")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Open pdf_full_text.txt to see the complete extracted text")
    print("2. Search for 'CRDTCARD' or 'Credit Card' to find loan section manually")
    print("3. Search for 'TRADE REFERENCE' to find trade section manually")
    print("4. Search for 'LEGAL CASES' or 'BANKRUPTCY' to find legal section")
    print("5. Look at the actual structure and spacing")
    print("6. Update the regex patterns in data_input.py to match the actual format")
    print("="*80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_diagnostic.py <pdf_file>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    try:
        diagnose_pdf(pdf_file)
    except FileNotFoundError:
        print(f"❌ ERROR: File '{pdf_file}' not found")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()