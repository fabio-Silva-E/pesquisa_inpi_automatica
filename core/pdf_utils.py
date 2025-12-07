from PyPDF2 import PdfReader

def extrair_dados_do_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        primeira_pagina = reader.pages[0]
        texto = primeira_pagina.extract_text()

        if not texto:
            return {"email": None, "cnpj": None, "mensagem": "❌ Nenhum texto encontrado no PDF."}

        texto_lower = texto.lower()
        email = None
        cnpj = None
        mensagem = None

        # 🔎 Extração do e-mail
        if "e-mail:" in texto_lower:
            email = texto_lower.split("e-mail:")[1].split()[0].strip()

            # Verificação de palavras proibidas
            if "marca" in email or "patente" in email:
                mensagem = f"⚠️ O e-mail '{email}' contém a palavra 'marca' ou 'patente'."

        # 🔎 Extração de CPF/CNPJ
        if "cpf/cnpj/número inpi:" in texto_lower:
            cnpj = texto_lower.split("cpf/cnpj/número inpi:")[1].split()[0].strip()

        return {"email": email, "cnpj": cnpj, "mensagem": mensagem}

    except Exception as e:
        return {"email": None, "cnpj": None, "mensagem": f"❌ Erro ao ler PDF: {e}"}
