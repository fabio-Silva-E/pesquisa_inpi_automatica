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
    QProgressDialog,
    QLabel,
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView,
    QWebEngineDownloadItem,
    QWebEngineProfile,
)
from PyQt5.QtCore import QUrl, QTimer, Qt

from db.connection import conectar_banco
from core.pdf_utils import extrair_email_do_pdf
from core.email_sender import enviar_email

app = QApplication(sys.argv)


# --- SUBCLASSE PARA INTERCEPTAR POPUPS ---
class MeuWebView(QWebEngineView):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app  # referência para INPIApp

    def createWindow(self, _type):
        popup = MeuWebView(app=self.app)
        popup.setWindowTitle("Popup INPI")
        popup.resize(900, 600)
        popup.show()

        # Assim que o popup carregar → preencher e enviar
        popup.page().loadFinished.connect(lambda ok: self.app.acao_no_popup(popup))

        return popup


# --- CLASSE PRINCIPAL ---
class INPIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("INPI busca automatica")
        self.setGeometry(100, 100, 1200, 800)
        self.login_executado = False

        layout_principal = QHBoxLayout()
        self.setLayout(layout_principal)

        # Conteúdo principal
        conteudo_layout = QVBoxLayout()

        # Barra de login
        login_layout = QHBoxLayout()
        self.entry_usuario = QLineEdit()
        self.entry_usuario.setPlaceholderText("Usuário")
        self.entry_senha = QLineEdit()
        self.entry_senha.setPlaceholderText("Senha")
        self.btn_login = QPushButton("Iniciar")
        self.btn_login.clicked.connect(self.fazer_login)
        login_layout.addWidget(self.entry_usuario)
        login_layout.addWidget(self.entry_senha)
        login_layout.addWidget(self.btn_login)
        conteudo_layout.addLayout(login_layout)

        # WebView principal
        self.webview = MeuWebView(app=self)
        profile = self.webview.page().profile()
        profile.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en;q=0.8")
        conteudo_layout.addWidget(self.webview)
        self.webview.page().profile().downloadRequested.connect(
            self.on_download_requested
        )

        layout_principal.addLayout(conteudo_layout, stretch=4)

        # Barra lateral
        sidebar_layout = QVBoxLayout()
        # --- Botão atualizar + contador ---
        botoes_layout = QHBoxLayout()

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.clicked.connect(self.atualizar_lista_processos)

        self.label_contador = QLabel("Processos: 0")

        botoes_layout.addWidget(self.btn_atualizar)
        botoes_layout.addWidget(self.label_contador)
        sidebar_layout.addLayout(botoes_layout)

        self.lista_processos = QListWidget()
        self.lista_processos.itemClicked.connect(self.selecionar_processo)
        sidebar_layout.addWidget(self.lista_processos)
        self.atualizar_lista_processos()
        email_layout = QHBoxLayout()

        self.campo_texto = QLineEdit()
        self.campo_texto.setPlaceholderText("e-mail extraído")
        self.btn_email = QPushButton("Enviar")
        # quando clicar, pega o texto do campo e envia para a função
        self.btn_email.clicked.connect(self.enviar_email_com_feedback)

        email_layout.addWidget(self.campo_texto)
        email_layout.addWidget(self.btn_email)
        sidebar_layout.addLayout(email_layout)
        # enviar = enviar_email
        # email_layout = QHBoxLayout()
        # self.campo_texto = QLineEdit()
        # self.campo_texto.setPlaceholderText("e-mail extraído")
        # self.btn_email = QPushButton("Enviar")
        # self.btn_email.clicked.connect(enviar)
        # email_layout.addWidget(self.campo_texto)
        # email_layout.addWidget(self.btn_email)
        # sidebar_layout.addLayout(email_layout)

        processo_layout = QHBoxLayout()
        self.entry_processo = QLineEdit()
        self.entry_processo.setPlaceholderText("N°Processo")
        self.btn_salvar = QPushButton("Salvar")

        self.btn_salvar.clicked.connect(self.salvar_resultado)

        processo_layout.addWidget(self.entry_processo)
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

    def enviar_email_com_feedback(self):
        email_destino = self.campo_texto.text().strip()
        if not email_destino:
            QMessageBox.warning(self, "Aviso", "Informe um e-mail para envio.")
            return
        # --- Mostra loading ---
        progress = QProgressDialog("Enviando e-mail...", None, 0, 0, self)
        progress.setWindowTitle("Aguarde")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()  # força atualização da interface

        def enviar():
            sucesso, msg = enviar_email(
                destinatario=email_destino,
                titular=self.titular,
                numero_processo=self.entry_processo.text(),
                data_deposito=self.data_deposito,
                marca=self.marca,
                classe=self.classe_nice,
            )
            progress.close()  # fecha loading
            print(msg)

            if sucesso:
                QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.critical(self, "Erro", msg)

        # --- Executa envio após atualizar interface ---
        QTimer.singleShot(100, enviar)

    # --- MÉTODOS DE LOGIN ---

    def fazer_login(self):
        self.login_executado = True
        self.titular = None
        self.processo_atual_id = None
        self.campo_texto.clear()

        print("🔄 Reiniciando fluxo de busca...")
        self.webview.load(QUrl(self.url_inpi))  # volta para a tela inicial do INPI

    def lista_processos(self):
        """
        Retorna lista de processos [(Id, Numero_Processo), ...]
        ou [] se não encontrar nada.
        """
        try:
            conn = conectar_banco()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Numero_Processo FROM Processos ORDER BY Id")
            processos = cursor.fetchall()
            conn.close()
            return processos
        except Exception as e:
            QMessageBox.critical(self, "Erro Banco", f"Falha ao buscar processos: {e}")
            return []

    def on_page_load(self, ok):
        if not ok:
            return

        url_atual = self.webview.url().toString()

        # Página de detalhe → baixar PDF
        if "MarcasServletController?Action=detail" in url_atual:
            QTimer.singleShot(300, self.abrir_popup)

        # Login
        elif self.login_executado and url_atual == self.url_inpi:
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
                    if(btnLogin) btnLogin.click(); else pass.form.submit();
                    return true;
                }} else {{
                    return false;
                }}
            }})()
            """
            self.webview.page().runJavaScript(js_code)

        # Redireciona para página de pesquisa
        elif (
            self.login_executado and "pePI/" in url_atual and url_atual != self.url_inpi
        ):
            self.webview.load(QUrl(self.url_destino))
            self.login_executado = False

        # Página de pesquisa → preencher número do processo
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

        else:
            self.webview.page().toHtml(self.verificar_resultado)

    # --- MÉTODOS DE RESULTADO ---
    def verificar_resultado(self, html):
        if "RESULTADO" in html or "Resultado" in html:
            # Captura titular
            js_pegar_titular = """
            (function(){
                var titular = document.querySelector("font.titular-marcas");
                return titular ? titular.innerText.trim() : null;
            })()
            """
            self.webview.page().runJavaScript(js_pegar_titular, self.salvar_titular)

            js_pegar_marca = """
            (function(){
                 var el = document.evaluate(
                     "//tr[@class='normal']/td/img[contains(@src,'/pePI/jsp/imagens/')]/parent::td/following-sibling::td//b",
                     document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                 ).singleNodeValue;
                 return el ? el.innerText.trim() : null;
             })();
            """

            self.webview.page().runJavaScript(js_pegar_marca, self.salvar_marca)

            # Captura Situação
            js_pegar_situacao = """
            (function(){
                var el = document.querySelector("td.left.padding-5 font.normal");
                return el ? el.innerText.trim() : null;
            })()
            """
            self.webview.page().runJavaScript(js_pegar_situacao, self.salvar_situacao)

            # Captura Classe de Nice
            js_pegar_classe_nice = """
            (function(){
                var el = document.querySelector("font.titulo-marcas");
                return el ? el.innerText.trim() : null;
            })()
            """
            self.webview.page().runJavaScript(
                js_pegar_classe_nice, self.salvar_classe_nice
            )
            # Captura Data de Depósito
            js_pegar_data_deposito = """
            (function(){
                var el = document.evaluate(
                    "//tr[@class='normal']/td[3]/font",  /* terceira coluna da linha de resultado */
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue;
                return el ? el.innerText.trim() : null;
            })()
            """

            self.webview.page().runJavaScript(
                js_pegar_data_deposito, self.salvar_data_deposito
            )
        # Captura link do detalhe
        js_pegar_link = """
            (function(){
                var link = document.querySelector('a[href*="MarcasServletController?Action=detail"]');
                return link ? link.href : null;
            })()
            """
        self.webview.page().runJavaScript(js_pegar_link, self.clicar_proxima_pg)

    def salvar_titular(self, titular):
        self.titular = titular
        print(">>> Titular capturado:", titular)

    def salvar_marca(self, marca):
        self.marca = marca
        print(">>> marca capturada:", marca)

    def salvar_situacao(self, situacao):
        self.situacao = situacao
        print(">>> situacao capturada:", situacao)

    def salvar_classe_nice(self, classe_nice):
        self.classe_nice = classe_nice
        print(">>> classe_nice capturada:", classe_nice)

    def salvar_data_deposito(self, data_deposito):
        self.data_deposito = data_deposito
        print(">>> deposito capturada:", data_deposito)

    # --- DOWNLOAD PDF ---
    def on_download_requested(self, download: QWebEngineDownloadItem):
        dir_base = (
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__))
        )
        pasta_pdfs = os.path.join(dir_base, "pdfs")
        os.makedirs(pasta_pdfs, exist_ok=True)
        nome_arquivo = download.path().split("/")[-1]
        caminho_final = os.path.join(pasta_pdfs, nome_arquivo)
        download.setPath(caminho_final)
        download.accept()
        print(f"📥 Download iniciado: {caminho_final}")
        download.finished.connect(lambda: self._processar_pdf_baixado(caminho_final))

    def _processar_pdf_baixado(self, caminho_final):
        email = extrair_email_do_pdf(caminho_final)
        if email:
            self.campo_texto.setText(email)
            print(f"✅ E-mail extraído: {email}")
        else:
            print("⚠ Nenhum e-mail encontrado no PDF")

    # --- NAVEGAÇÃO ---
    def clicar_proxima_pg(self, href):
        if href:
            if href.startswith("/"):
                href = "https://busca.inpi.gov.br" + href
            self.webview.load(QUrl(href))

    # --- BAIXAR PDF (clicar link popup) ---
    def abrir_popup(self):

        js_click_link = """
            (function(){
                var links = document.querySelectorAll("a.titulo");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].innerText.trim() === "Clique aqui para ter acesso as petições do processo") {
                        links[i].scrollIntoView();
                        // Executa diretamente o onclick
                        if (links[i].getAttribute("onclick")) {
                            eval(links[i].getAttribute("onclick"));
                            return true;
                        } else {
                            links[i].click();
                            return true;
                        }
                    }
                }
                return false;
            })()
            """

        def callback(result):
            print("chegou ate aqui")
            if result:
                print("✅ Link do popup clicado:", result)
            # se abriu popup → acao_no_popup cuida do resto
            else:
                print("⚠ Nenhum link de petições encontrado. Pulando para baixar PDF.")
                QTimer.singleShot(500, self.baixar_pdf)  # chama direto

        self.webview.page().runJavaScript(js_click_link, callback)

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

    # --- POPUP ---
    def acao_no_popup(self, popup_view):
        js_preencher_e_enviar = """
        (function(){
            var select = document.querySelector("select#codigoHipotese");
            var checkbox = document.querySelector("input#aceite");
            var btnEnviar = document.querySelector("input[type='submit'][value*='Enviar']");    
            if (select) select.value = "1";
            if (checkbox) checkbox.checked = true;
            if (btnEnviar) {
                btnEnviar.click();
                return "✅ Enviado no popup";
            }
            return "❌ Botão não encontrado";
        })()
        """

        def callback(result):
            print("📌 Popup:", result)

            # 👉 Só fecha o popup quando ele carregar a resposta do servidor
            QTimer.singleShot(
                1000,
                lambda: (
                    print("✅ Fechando popup..."),
                    popup_view.close(),
                    QTimer.singleShot(1000, self.baixar_pdf),
                ),
            )

        popup_view.page().runJavaScript(js_preencher_e_enviar, callback)

    # --- FUNÇÕES AUXILIARES ---
    def atualizar_lista_processos(self):
        self.lista_processos.clear()
        try:
            conn = conectar_banco()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Numero_Processo FROM Processos ORDER BY Id")
            self.processos = cursor.fetchall()
            for proc in self.processos:
                self.lista_processos.addItem(proc[1])
            conn.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro Banco", f"Falha ao carregar processos: {e}"
            )
        self.label_contador.setText(f"Processos: {self.lista_processos.count()}")

    def selecionar_processo(self, item):
        numero = item.text()
        self.entry_processo.setText(numero)

        # procura o processo pelo número e guarda o Id
        for proc in self.processos:
            if proc[1] == numero:
                self.processo_atual_id = proc[0]
                break

        print(f"✅ Processo selecionado: {numero} (ID={self.processo_atual_id})")

    def salvar_resultado(self):
        numero_processo = self.entry_processo.text().strip()
        if not numero_processo:
            QMessageBox.warning(self, "Aviso", "Nenhum processo informado.")
            return

        conn = conectar_banco()
        if not conn:
            QMessageBox.critical(self, "Erro Banco", "Falha ao conectar no SQL Server.")
            return

        cursor = conn.cursor()

        # 🔹 Se não tiver o Id salvo, busca pelo número do processo
        if not hasattr(self, "processo_atual_id") or not self.processo_atual_id:
            cursor.execute(
                "SELECT Id FROM Processos WHERE Numero_Processo = ?", (numero_processo,)
            )
            row = cursor.fetchone()
            if row:
                self.processo_atual_id = row[0]
            else:
                QMessageBox.critical(self, "Erro", "Processo não encontrado no banco.")
                conn.close()
                return

        # 🔹 Salva no Resultados
        cursor.execute(
            """
            INSERT INTO Resultados 
            (Numero_Processo, Email, classe_nice, data_deposito, titular, situacao, Nome_Marca) 
          VALUES (?, ?, ?, ?, ?, ?, ?)
          """,
            (
                numero_processo,
                self.campo_texto.text(),
                getattr(self, "classe_nice", ""),
                getattr(self, "data_deposito", ""),
                getattr(self, "titular", ""),
                getattr(self, "situacao", ""),
                getattr(self, "marca", ""),
            ),
        )

        # 🔹 Remove da tabela Processos
        cursor.execute("DELETE FROM Processos WHERE Id = ?", (self.processo_atual_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Sucesso", f"Processo {numero_processo} salvo com sucesso."
        )

        # 🔹 Atualiza lista e seleciona o próximo automaticamente
        self.atualizar_lista_processos()
        if self.lista_processos.count() > 0:
            self.lista_processos.setCurrentRow(0)  # já seleciona o próximo processo
            self.selecionar_processo(self.lista_processos.item(0))  # dispara seleção
        else:
            self.entry_processo.clear()


# --- RODA APLICATIVO ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = INPIApp()
    win.show()
    sys.exit(app.exec_())
