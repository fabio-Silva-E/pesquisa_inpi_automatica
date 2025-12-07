import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from .config import EMAIL_REMETENTE, SENHA_APP
from email.mime.base import MIMEBase
from email import encoders
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

    assunto = f"Arquivamento de marca INPI - {numero_processo} - {marca}"

    # Corpo HTML com a imagem inline
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


    # Criação do e-mail
    msg = MIMEMultipart("related")
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = destinatario
    msg["Subject"] = assunto

    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText("Seu cliente de e-mail não suporta HTML", "plain"))
    msg_alternative.attach(MIMEText(corpo_html, "html"))

    # Anexa a imagem do WhatsApp
    caminho_imagem = os.path.join("imgs", "whatsapp.png")

    try:
        with open(caminho_imagem, "rb") as img_file:
            img_data = img_file.read()
            img = MIMEImage(img_data)  # aqui detecta o tipo automaticamente
            img.add_header(
                "Content-ID", "<whatsapp_logo>"
            )  # deve ser igual ao usado no HTML
            img.add_header("Content-Disposition", "inline", filename="whatsapp.png")
            msg.attach(img)
    except FileNotFoundError:
        print("⚠ Arquivo whatsapp.png não encontrado na raiz do projeto.")

    # Evita reenvio
    # enviados = carregar_log()
    # if destinatario in enviados:
    #   return False, "E-mail já enviado anteriormente."

    # Envio
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, SENHA_APP)
            server.send_message(msg)

        salvar_log(destinatario)
        return True, f"E-mail enviado com sucesso para {destinatario}."
    except Exception as e:
        return False, f"Falha ao enviar e-mail para {destinatario}: {e}"
