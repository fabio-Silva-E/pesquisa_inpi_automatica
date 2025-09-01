from PyPDF2 import PdfReader

def extrair_email_do_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        primeira_pagina = reader.pages[0]
        texto = primeira_pagina.extract_text()
        
        if texto and "e-mail:" in texto.lower():
            email = texto.lower().split("e-mail:")[1].split()[0]
            return email.strip()
        
        return None

    except Exception as e:
        print(f"❌ Erro ao ler PDF: {e}")
        return None
