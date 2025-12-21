import sys
from PyQt5.QtWidgets import QApplication
from ui.app import MainApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
