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
        self.update_light(self.fullPowerLight, states['fullpower'])
        self.update_light(self.lowBatteryLight, states['lowbattery'])
        self.update_ecoModecomboBox(states)

    def update_light(self, label, state):
        # Mise à jour de la lumière en fonction de l'état
        if state:
            label.setPixmap(QtGui.QPixmap('images/green_light.png'))
        else:
            label.setPixmap(QtGui.QPixmap('images/red_light.png'))

    def update_ecoModecomboBox(self, states):
        self.ecoModecomboBox.clear()  # Vide la ComboBox avant de la mettre à jour
        if states['fullpower']and not states['lowbattery']:
            self.ecoModecomboBox.addItem("OFF")
            self.ecoModecomboBox.addItem("Sleep")
            self.ecoModecomboBox.addItem("ECO 0")
            self.ecoModecomboBox.addItem("ECO 1")
            self.ecoModecomboBox.addItem("ECO 2")
        if states['fullpower']and states['lowbattery']:
            self.ecoModecomboBox.addItem("OFF")
            self.ecoModecomboBox.addItem("Sleep")
            self.ecoModecomboBox.addItem("ECO 0")
            self.ecoModecomboBox.addItem("ECO 1")
            self.ecoModecomboBox.addItem("ECO 2")
            self.ecoModecomboBox.addItem("Low Battery")
        elif not states['fullpower'] and not states['lowbattery']:
            self.ecoModecomboBox.addItem("OFF")
            self.ecoModecomboBox.addItem("Sleep")
            self.ecoModecomboBox.addItem("ECO 0")
        elif not states['fullpower'] and states['lowbattery']:
            self.ecoModecomboBox.addItem("OFF")
            self.ecoModecomboBox.addItem("Sleep")
            self.ecoModecomboBox.addItem("ECO 0")
            self.ecoModecomboBox.addItem("Low Battery")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
