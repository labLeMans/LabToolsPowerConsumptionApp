import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from app.py import Ui_MainWindow  # Assurez-vous que le nom de la classe correspond à celui généré par pyuic5

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
