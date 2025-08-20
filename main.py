import sys
from PyQt5.QtWidgets import QApplication
from ui.app import INPIApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = INPIApp()
    window.show()
    sys.exit(app.exec_())
