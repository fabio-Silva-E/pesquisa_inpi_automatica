import sys
import os
import time

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QListWidget,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl, QTimer

from db.connection import conectar_banco
from core.pdf_utils import extrair_email_do_pdf


class INPIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("INPI busca automatica")
        self.setGeometry(100, 100, 1200, 800)
        self.login_executado = False

        # Layout principal (horizontal → barra lateral + webview)
        layout_principal = QHBoxLayout()
        self.setLayout(layout_principal)

        # ----- PARTE ESQUERDA (conteúdo principal) -----
        conteudo_layout = QVBoxLayout()

        # Barra de login no topo
        login_layout = QHBoxLayout()
        self.entry_usuario = QLineEdit()
        self.entry_usuario.setPlaceholderText("Usuário")
        self.entry_usuario.setFixedHeight(25)
        login_layout.addWidget(self.entry_usuario)

        self.entry_senha = QLineEdit()
        self.entry_senha.setPlaceholderText("Senha")
        self.entry_senha.setFixedHeight(25)
        login_layout.addWidget(self.entry_senha)

        self.btn_login = QPushButton("Iniciar")
        self.btn_login.setFixedHeight(25)
        self.btn_login.clicked.connect(self.fazer_login)
        login_layout.addWidget(self.btn_login)

        conteudo_layout.addLayout(login_layout)

        # Navegador
        self.webview = QWebEngineView()
        conteudo_layout.addWidget(self.webview)

        self.webview.page().profile().downloadRequested.connect(
            self.on_download_requested
        )

        # Adiciona conteúdo principal à esquerda
        layout_principal.addLayout(conteudo_layout, stretch=4)

        # ----- PARTE DIREITA (barra lateral) -----
        sidebar_layout = QVBoxLayout()

        self.lista_processos = QListWidget()
        self.lista_processos.itemClicked.connect(self.selecionar_processo)
        sidebar_layout.addWidget(self.lista_processos)
        self.atualizar_lista_processos()
        email_layout = QHBoxLayout()
        self.campo_texto = QLineEdit()
        self.campo_texto.setPlaceholderText("e-mail extraído")
        email_layout.addWidget(self.campo_texto)

        self.btn_email = QPushButton("Enviar")
        self.btn_email.setFixedHeight(25)
        self.btn_email.clicked.connect(self.enviar_email)  # conecta a função
        email_layout.addWidget(self.btn_email)

        sidebar_layout.addLayout(email_layout)

        processo_layout = QHBoxLayout()
        self.entry_processo = QLineEdit()
        self.entry_processo.setPlaceholderText("N°Processo")
        sidebar_layout.addWidget(self.entry_processo)

        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setFixedHeight(25)
        self.btn_salvar.clicked.connect(
            lambda: self.salvar_resultado(
                self.campo_texto.text(),  # email
                getattr(
                    self, "titular", ""
                ),  # nome da marca, ou string vazia se não tiver
            )
        )
        processo_layout.addWidget(self.btn_salvar)
        sidebar_layout.addLayout(processo_layout)
        layout_principal.addLayout(sidebar_layout, stretch=1)

        # URLs
        self.url_inpi = "https://busca.inpi.gov.br/pePI/"
        self.url_destino = (
            "https://busca.inpi.gov.br/pePI/jsp/marcas/Pesquisa_num_processo.jsp"
        )

        self.webview.load(QUrl(self.url_inpi))
        self.webview.loadFinished.connect(self.on_page_load)

    def enviar_email(self):
        email = self.campo_texto.text().strip()
        if not email:
            QMessageBox.warning(self, "Erro", "Nenhum e-mail informado.")
            return

    def carregar_processos(self):
        self.lista_processos.clear()
        try:
            conn = conectar_banco()
            if not conn:
                QMessageBox.critical(
                    self, "Erro Banco", "Falha ao conectar no SQL Server."
                )
                return

            cursor = conn.cursor()
            cursor.execute(
                "SELECT numero_processo FROM Processos ORDER BY id"
            )  # ajuste o nome da sua tabela/coluna
            for row in cursor.fetchall():
                self.lista_processos.addItem(row[0])
            conn.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro Banco", f"Falha ao carregar processos: {e}"
            )

    def fazer_login(self):
        self.login_executado = True
        self.webview.reload()

    def on_page_load(self, ok):
        if not ok:
            # QMessageBox.critical(self, "Erro", "Falha ao carregar página")
            return

        url_atual = self.webview.url().toString()

        if "MarcasServletController?Action=detail" in url_atual:
            QTimer.singleShot(300, self.baixar_pdf)
        # Login
        if self.login_executado and url_atual == self.url_inpi:
            usuario = self.entry_usuario.text()
            senha = self.entry_senha.text()

            if not usuario or not senha:
                QMessageBox.warning(self, "Erro", "Preencha usuário e senha")
                return

            js_code = f"""
            (function(){{
                var user = document.getElementsByName('T_Login')[0];
                var pass = document.getElementsByName('T_Senha')[0];
                var btnLogin = document.querySelector('input[type="submit"][value*="Continuar"]');
                if(user && pass){{
                    user.value = "{usuario}";
                    pass.value = "{senha}";
                    if(btnLogin) {{
                        btnLogin.click();
                    }} else {{
                        pass.form.submit();
                    }}
                    return true;
                }} else {{
                    return false;
                }}
            }})()
            """
            self.webview.page().runJavaScript(js_code)

        elif (
            self.login_executado and "pePI/" in url_atual and url_atual != self.url_inpi
        ):
            self.webview.load(QUrl(self.url_destino))
            self.login_executado = False

        elif url_atual == self.url_destino:
            processo = self.entry_processo.text()
            if processo:
                js_preencher_processo = f"""
                (function(){{
                    var campo = document.getElementsByName('NumPedido')[0];
                    if(campo){{
                        campo.value = "{processo}";
                        var btn = document.querySelector('input[type="submit"]');
                        if(btn) btn.click();
                    }}
                }})()
                """
                self.webview.page().runJavaScript(js_preencher_processo)

        # Aqui pegamos o HTML antes de procurar por "RESULTADO"
        else:
            self.webview.page().toHtml(self.verificar_resultado)

    def verificar_resultado(self, html):
        if "RESULTADO" in html or "Resultado" in html:
            # 1) Pegar o TITULAR
            js_pegar_titular = """
         (function(){
             var titular = document.querySelector("font.titular-marcas");
             if (titular) {
                 return titular.innerText.trim();
             }
             return null;
         })()
          """
            self.webview.page().runJavaScript(js_pegar_titular, self.salvar_titular)

            # 2) Pegar o link do detalhe
            js_pegar_link = """
         (function(){
             var link = document.querySelector('a[href*="MarcasServletController?Action=detail"]');
             return link ? link.href : null;
         })()
         """
            self.webview.page().runJavaScript(js_pegar_link, self.clicar_proxima_pg)

    def salvar_titular(self, titular):
        if titular:
            self.titular = titular  # salva em uma variável da classe
            print(">>> Titular capturado:", titular)
        else:
            self.titular = None
            print(">>> Titular não encontrado.")

    def on_download_requested(self, download: QWebEngineDownloadItem):
        # Descobre o diretório do executável ou do script Python
        if getattr(sys, "frozen", False):  # se estiver rodando como exe
            dir_base = os.path.dirname(sys.executable)
        else:  # se estiver rodando como script Python
            dir_base = os.path.dirname(os.path.abspath(__file__))

        # Cria a pasta "pdfs" se não existir
        pasta_pdfs = os.path.join(dir_base, "pdfs")
        os.makedirs(pasta_pdfs, exist_ok=True)

        # Define o caminho completo para salvar o PDF
        nome_arquivo = download.path().split("/")[-1]
        caminho_final = os.path.join(pasta_pdfs, nome_arquivo)

        # Configura o download
        download.setPath(caminho_final)
        download.accept()
        print(f"📥 Download iniciado: {caminho_final}")

        # Quando terminar o download, extrai o e-mail
        download.finished.connect(lambda: self._processar_pdf_baixado(caminho_final))

    def _processar_pdf_baixado(self, caminho_final):
        print(f"📥 PDF salvo em: {caminho_final}")
        email = extrair_email_do_pdf(caminho_final)
        if email:
            self.campo_texto.setText(email)
            print(f"✅ E-mail extraído: {email}")
        else:
            print("⚠ Nenhum e-mail encontrado no PDF")

    def clicar_proxima_pg(self, _):
        if not hasattr(self, "titular") or not self.titular:
            print("⚠ Nenhum titular salvo para procurar o PDF.")
            return

        titular_js = self.titular.replace("'", "\\'")
        js_clicar_pdf = f"""
       (function(){{
            var linhas = document.querySelectorAll("tr");
            for (var i = 0; i < linhas.length; i++) {{
                var tds = linhas[i].querySelectorAll("td");
                for (var j = 0; j < tds.length; j++) {{
                    if (tds[j].innerText && tds[j].innerText.includes('{titular_js}')) {{
                       var link = linhas[i].querySelector("a[href*='MarcasServletController?Action=detail']");
                          if(link) {{
                              link.scrollIntoView();
                            link.click();  // navega para a página de detalhe
                            return link.href;
                        }}
                    }}
                 }}
            }}
            return null;
        }})()
        """
        self.webview.page().runJavaScript(js_clicar_pdf, self.ir_para_detalhe)

    def baixar_pdf(self):
        if not hasattr(self, "titular") or not self.titular:
            print("⚠ Nenhum titular salvo.")
            return

        titular_js = self.titular.replace("'", "\\'")
        js_click_pdf = f"""
        (function(){{
            var linhas = document.querySelectorAll("tr");
            for (var i = 0; i < linhas.length; i++) {{
                var tds = linhas[i].querySelectorAll("td");
                var img = linhas[i].querySelector("img.salvaDocumento");
                if(img){{
                    for(var j=0; j<tds.length; j++){{
                        if(tds[j].innerText.includes('{titular_js}')){{
                            img.scrollIntoView();
                            img.click(); // aqui aparece CAPTCHA
                            return true;
                        }}
                    }}
                }}
            }}
            return false;
        }})()
        """
        self.webview.page().runJavaScript(
            js_click_pdf, lambda r: print("PDF clicado:", r)
        )

    def atualizar_lista_processos(self):
        self.lista_processos.clear()
        try:
            conn = conectar_banco()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Numero_Processo FROM Processos ORDER BY Id")
            self.processos = cursor.fetchall()  # guarda Id e número
            for proc in self.processos:
                self.lista_processos.addItem(proc[1])  # mostra só o número na lista
            conn.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro Banco", f"Falha ao carregar processos: {e}"
            )

    def salvar_resultado(self, email, nome_marca):
        if not hasattr(self, "processo_atual_id"):
            print("⚠ Nenhum processo carregado.")
            return

        numero_processo = self.entry_processo.text()
        conn = conectar_banco()
        if not conn:
            QMessageBox.critical(self, "Erro Banco", "Falha ao conectar no SQL Server.")
            return

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Resultados (Numero_Processo, Email, Nome_Marca) VALUES (?, ?, ?)",
            (numero_processo, email, nome_marca),
        )
        cursor.execute("DELETE FROM Processos WHERE Id = ?", (self.processo_atual_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Sucesso", f"Processo {numero_processo} salvo com sucesso."
        )

        # Atualiza lista lateral
        self.atualizar_lista_processos()

        # Limpar campo
        self.entry_processo.clear()

        # Chamar próximo processo automaticamente
        self.pegar_proximo_processo()

    def ir_para_detalhe(self, href):
        if href:
            if href.startswith("/"):
                href = "https://busca.inpi.gov.br" + href
            self.webview.load(QUrl(href))

    def selecionar_processo(self, item):
        self.entry_processo.setText(item.text())
        # self.webview.load(QUrl(self.url_destino))
