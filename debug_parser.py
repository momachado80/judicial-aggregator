import pdfplumber
import re

# Debug: Show exactly what context is captured for a specific process
pdf_path = "data/dje_pdfs/dje_19-11-2025_cad12.pdf"
target_numero = "1100500-77.2025.8.26.0100"

print(f"🔍 Debugging parser for process: {target_numero}")
print(f"📄 PDF: {pdf_path}\n")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[6]  # Page 7 (0-indexed)
    text = page.extract_text()

    # Find the process number
    pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'

    for match in re.finditer(pattern, text):
        numero = match.group(1)

        if numero == target_numero:
            print(f"✅ Found process at position {match.start()}\n")

            # Show context with 600 chars (current setting)
            start = max(0, match.start() - 600)
            end = min(len(text), match.end() + 600)
            contexto = text[start:end]

            print("="*80)
            print("CONTEXT (600 chars before/after):")
            print("="*80)
            print(contexto)
            print("="*80)

            # Try to extract class
            classe_match = re.search(r'CLASSE\s*:\s*([^\n]+)', contexto, re.IGNORECASE)
            if classe_match:
                print(f"\n✅ CLASSE FOUND: '{classe_match.group(1).strip()}'")
                print(f"   Position in context: {classe_match.start()}")
            else:
                print("\n❌ No CLASSE found with 'CLASSE :' format")

            # Try format 2
            classe_match2 = re.search(r'Classe[\s\n]+([^\n]+)', contexto, re.IGNORECASE)
            if classe_match2:
                print(f"\n✅ CLASSE FOUND (format 2): '{classe_match2.group(1).strip()}'")

            break
