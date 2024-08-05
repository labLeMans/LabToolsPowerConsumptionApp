import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtGui

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_ui()
        self.setup_connections()

    def load_ui(self):
        """Charge le fichier UI pour la fenêtre principale."""
        uic.loadUi('main.ui', self)

    def setup_connections(self):
        """Configure les connexions des signaux et slots."""
        self.pushButton.clicked.connect(self.show_second_window)

    def show_second_window(self):
        """Crée et affiche la fenêtre secondaire, puis ferme la fenêtre principale."""
        tool_button_states = self.get_tool_button_states()
        self.second_window = SecondApp(tool_button_states)
        self.second_window.show()
        self.close()  # Ferme la fenêtre principale

    def get_tool_button_states(self):
        """Récupère les états des CheckBox dans la fenêtre principale."""
        states = {
            'fullpower': self.FullPowercheckBox.isChecked(),
            'lowbattery': self.LowBatterycheckBox.isChecked()
        }
        return states

class SecondApp(QMainWindow):
    def __init__(self, tool_button_states):
        super().__init__()
        self.load_ui()
        self.display_tool_button_states(tool_button_states)

    def load_ui(self):
        """Charge le fichier UI pour la fenêtre secondaire."""
        uic.loadUi('second.ui', self)

    def display_tool_button_states(self, states):
        """Met à jour les éléments de la fenêtre secondaire en fonction des états des CheckBox."""
        self.update_light(self.fullPowerLight, states['fullpower'])
        self.update_light(self.lowBatteryLight, states['lowbattery'])
        self.update_ecoModecomboBox(states)

    def update_light(self, label, state):
        """Met à jour l'image du label en fonction de l'état (vert pour actif, rouge pour inactif)."""
        if state:
            label.setPixmap(QtGui.QPixmap('images/green_light.png'))
        else:
            label.setPixmap(QtGui.QPixmap('images/red_light.png'))

    def update_ecoModecomboBox(self, states):
        """Met à jour les éléments de la ComboBox en fonction des états des CheckBox."""
        self.ecoModecomboBox.clear()  # Vide la ComboBox avant de la mettre à jour
        
        if states['fullpower']:
            self.add_fullpower_items(states['lowbattery'])
        elif not states['fullpower'] and states['lowbattery']:
            self.add_lowbattery_items()
        else:
            self.add_basic_items()

    def add_fullpower_items(self, lowbattery):
        """Ajoute les éléments de la ComboBox lorsque le mode 'fullpower' est activé."""
        self.ecoModecomboBox.addItem("OFF")
        self.ecoModecomboBox.addItem("Sleep")
        self.ecoModecomboBox.addItem("ECO 0")
        self.ecoModecomboBox.addItem("ECO 1")
        self.ecoModecomboBox.addItem("ECO 2")
        if lowbattery:
            self.ecoModecomboBox.addItem("Low Battery")

    def add_lowbattery_items(self):
        """Ajoute les éléments de la ComboBox lorsque 'fullpower' est désactivé et 'lowbattery' est activé."""
        self.ecoModecomboBox.addItem("OFF")
        self.ecoModecomboBox.addItem("Sleep")
        self.ecoModecomboBox.addItem("ECO 0")
        self.ecoModecomboBox.addItem("Low Battery")

    def add_basic_items(self):
        """Ajoute les éléments de la ComboBox lorsque ni 'fullpower' ni 'lowbattery' ne sont activés."""
        self.ecoModecomboBox.addItem("OFF")
        self.ecoModecomboBox.addItem("Sleep")
        self.ecoModecomboBox.addItem("ECO 0")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
