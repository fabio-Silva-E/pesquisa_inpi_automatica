import win32com.client as win32
import os

ARQUIVO_LOG = "sent_log.txt"

def carregar_log():
    try:
        with open(ARQUIVO_LOG, "r") as f:
            return set(linha.strip() for linha in f.readlines())
    except FileNotFoundError:
        return set()

def salvar_log(email):
    with open(ARQUIVO_LOG, "a") as f:
        f.write(email + "\n")

def enviar_email(destinatario, marca, classe, data_deposito, titular, numero_processo):
    assunto = f"Arquivamento de marca {marca} Processo - {numero_processo} "

    # Corpo HTML
    corpo_html = f"""
    <p>Prezados,</p>
    <p>
      Sua marca foi depositada, publicada e deferida (concedido o registro por 10 anos), tinha uma taxa federal para ser paga em 90 dias e a mesma, não foi paga.    </p>
    <p>
       Ainda há tempo de recuperar a marca preencha o requerimento e nos envie via E-mail ou WhatsApp <a href="https://wa.me/5514996587707">14-99658-7707</a>.    </p>
    <p>Segue pesquisa do INSTITUTO NACIONAL DA PROPRIEDADE INDUSTRIAL, mostrando que passou mais de 90 (NOVENTA) dias sem ter sido efetuado o pagamento da taxa do decênio, em breve o órgão publicará o ARQUIVAMENTO DEFINITIVO DO PEDIDO DE REGISTRO, é imprescindível o RE-DEPÓSITO URGENTE DA MARCA antes da publicação na Revista da Propriedade Industrial, para evitar que terceiros solicite sua marca.</p>
    <p>Para a segurança de nossos clientes somente trabalhamos com requerimento devidamente preenchido e assinado ficando os documentos originais em poder das contratantes.
     </p>
     <p>Sendo assim torna-se imprescindível o REDEPÓSITO DA MARCA antes da publicação na RPI (Revista da Propriedade Industrial), para evitar futuros problemas com a concorrência.
     </p>
     <p>RE-DEPÓSITO DA MARCA preencha o requerimento que está em anexo.</p>
    <p><b>Número do processo:</b> {numero_processo} - <b>Data Depósito:</b> {data_deposito}</p>
    <p><b>Titular:</b> {titular}</p>
    <p><b>Marca:</b> {marca}</p>
    <p><b>Apresentação:</b> {classe}</p>
    <p>
        Caso precise de ajuda, entre em contato pelo WhatsApp:<br>
        <a href="https://wa.me/5514996587707">+55 14 996587707</a>
    </p>
    <p>Atenciosamente,</p>
    
   <p> Claudemir Soares </p>
<p>
  E-mail: 
  <a href="mailto:claudemir@mpbrasil.com">claudemir@mpbrasil.com</a>
</p>
    Consultor em marcas
    """

    try:
        # Conecta ao Outlook
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = e-mail

        mail.To = destinatario
        mail.Subject = assunto
        mail.HTMLBody = corpo_html

        # Anexa a imagem
        caminho_imagem = os.path.join("imgs", "whatsapp.png")
        if os.path.exists(caminho_imagem):
            mail.Attachments.Add(caminho_imagem)
        else:
            print("⚠ Arquivo whatsapp.png não encontrado na pasta imgs.")

        # Envia
        mail.Send()

        salvar_log(destinatario)
        return True, f"E-mail enviado com sucesso para {destinatario}."
    except Exception as e:
        return False, f"Falha ao enviar e-mail para {destinatario}: {e}"
