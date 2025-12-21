from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QPoint

def mostrar_toast(self, mensagem, tempo=2000):
    # --- Criar widget flutuante ---
    toast = QWidget(self)
    toast.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    toast.setAttribute(Qt.WA_TranslucentBackground)

    # --- Label do toast ---
    label = QLabel(mensagem, toast)
    label.setStyleSheet("""
        QLabel {
            background-color: rgba(0, 0, 0, 180);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 20pt;
        }
    """)
    label.adjustSize()
    toast.resize(label.width(), label.height())

    # --- Posição central ---
    largura_janela = self.width()
    altura_janela = self.height()
    x_central = self.x() + (largura_janela - label.width()) // 2
    y_central = self.y() + (altura_janela - label.height()) // 2
    toast.move(x_central, y_central)
    toast.show()
    toast.raise_()
    toast.activateWindow()

    # --- Timer para fechar automaticamente ---
    QTimer.singleShot(tempo, toast.close)
