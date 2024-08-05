import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtGui

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.pushButton.clicked.connect(self.show_second_window)

    def show_second_window(self):
        tool_button_states = self.get_tool_button_states()
        self.second_window = SecondApp(tool_button_states)
        self.second_window.show()
        self.close()  # Ferme la fenêtre principale

    def get_tool_button_states(self):
        # Récupération des états des CheckBox
        states = {
            'fullpower': self.FullPowercheckBox.isChecked(),
            'lowbattery': self.LowBatterycheckBox.isChecked()
        }
        return states

class SecondApp(QMainWindow):
    def __init__(self, tool_button_states):
        super().__init__()
        uic.loadUi('second.ui', self)
        self.display_tool_button_states(tool_button_states)

    def display_tool_button_states(self, states):
        # Mise à jour de l'affichage en fonction des états des CheckBox
        if states['fullpower']:
            self.fullPowerLabel.setText("Full Power")
            self.set_round_image(self.fullPowerLight, 'green_light.png')
        else:
            self.fullPowerLabel.setText("Full Power")
            self.set_round_image(self.fullPowerLight, 'red_light.png')

        if states['lowbattery']:
            self.lowBatteryLabel.setText("Low Battery")
            self.set_round_image(self.lowBatteryLight, 'green_light.png')
        else:
            self.lowBatteryLabel.setText("Low Battery")
            self.set_round_image(self.lowBatteryLight, 'red_light.png')

    def set_round_image(self, label, image_path):
        pixmap = QtGui.QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setStyleSheet("""
            QLabel {
                border-radius: %dpx;
                background: transparent;
            }
        """ % (pixmap.width() // 2))
        label.setScaledContents(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
