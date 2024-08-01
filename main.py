import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from app import Ui_MainWindow  # Remplacez 'example' par le nom de votre fichier généré

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.on_click)

    def on_click(self):
        print("Button clicked!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
