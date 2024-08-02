import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5 import uic

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.openButton.clicked.connect(self.show_second_window)

    def show_second_window(self):
        self.second_window = SecondApp()
        self.second_window.show()

class SecondApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('second.ui', self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
