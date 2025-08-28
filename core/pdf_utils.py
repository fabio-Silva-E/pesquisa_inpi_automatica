import PyPDF2


def extrair_email_do_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            texto = "".join([page.extract_text() for page in reader.pages])

        if "e-mail:" in texto.lower():
            email = texto.lower().split("e-mail:")[1].split()[0]
            return email.strip()
        return None

    except Exception as e:
        print(f"❌ Erro ao ler PDF: {e}")
        return None
