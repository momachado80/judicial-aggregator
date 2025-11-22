import pdfplumber
import re

# Debug: Show exactly what context is captured for a specific process
pdf_path = "data/dje_pdfs/dje_19-11-2025_cad12.pdf"
target_numero = "1100500-77.2025.8.26.0100"

print(f"🔍 Debugging NEW parser logic for process: {target_numero}")
print(f"📄 PDF: {pdf_path}\n")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[6]  # Page 7 (0-indexed)
    text = page.extract_text()

    # Find the process number
    pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'

    for match in re.finditer(pattern, text):
        numero = match.group(1)

        if numero == target_numero:
            print(f"✅ Found process at position {match.start()}-{match.end()}\n")

            # NEW LOGIC: Context ONLY AFTER the process number
            start_contexto = match.end()  # Starts AFTER the number
            end_contexto = min(len(text), match.end() + 300)  # Only 300 chars after
            contexto = text[start_contexto:end_contexto]

            print("="*80)
            print("NEW CONTEXT (300 chars AFTER process number ONLY):")
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

            # Check if it matches Inventário/Divórcio
            if classe_match:
                classe = classe_match.group(1).strip()
                classe_lower = classe.lower()

                print(f"\n🔍 Checking if '{classe}' starts with 'inventário' or 'divórcio':")

                for tipo in ["Inventário", "Divórcio"]:
                    tipo_lower = tipo.lower()
                    if (classe_lower == tipo_lower or
                        classe_lower.startswith(tipo_lower + " ") or
                        classe_lower.startswith(tipo_lower + "-")):
                        print(f"   ✅ MATCH: Class starts with '{tipo}'")
                        break
                else:
                    print(f"   ❌ REJECT: Class does NOT start with 'Inventário' or 'Divórcio'")
                    print(f"   This process will be REJECTED by the filter!")

            break
