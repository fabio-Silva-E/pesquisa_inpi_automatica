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
    Conforme pesquisa efetuada ao INPI (Instituto Nacional da Propriedade Industrial), constatamos que o processo de sua titularidade teve seu despacho publicado quanto ao recolhimento das retribuições relativas à concessão do Registro. Passados mais de 90(noventa) dias sem ter sido efetuado o pagamento das taxas, em breve o órgão publicará o ARQUIVAMENTO DEFINITIVO DO PEDIDO DE REGISTRO, tornando-se pública a informação para que terceiros possam solicitar a titularidade da marca.

      Sendo assim torna-se imprescindível o REDEPÓSITO DA MARCA antes da publicação na RPI (Revista da Propriedade Industrial), para evitar futuros problemas com a concorrência.

     Segue abaixo informações da marca.
    </p>
    <p><b>Número do processo:</b> {numero_processo} - <b>Data Depósito:</b> {data_deposito}</p>
    <p><b>Titular:</b> {titular}</p>
    <p><b>Marca:</b> {marca}</p>
    <p><b>Apresentação:</b> {classe}</p>
    <p>
        Caso precise de ajuda, entre em contato pelo WhatsApp:<br>
        <img src="cid:whatsapp_logo" width="20" height="20">
        <a href="https://wa.me/5514996587707">+55 14 996587707</a>
    </p>
    <p>Atenciosamente,</p>
    
    Claudemir Soares
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
