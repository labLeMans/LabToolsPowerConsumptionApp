import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5 import uic

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.pushButton.clicked.connect(self.show_second_window)

    def show_second_window(self):
        tool_button_states = self.get_tool_button_states()
        self.second_window = SecondApp(tool_button_states)
        self.second_window.show()
        self.close() # ferme la fenetre principale

    def get_tool_button_states(self):
        #récupération des checkbox full power et low battery
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
        # Affiche les états de full power et low battery
        for button, state in state.items():
            print(f'{button} is {"checked" if state else "unchecked"}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
