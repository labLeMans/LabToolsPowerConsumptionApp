import sys
import requests
import threading
import time
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout, QWidget
from PyQt5 import uic, QtGui
from bs4 import BeautifulSoup
from openpyxl import Workbook

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
        self.validatePushButton.clicked.connect(self.show_second_window)

    def show_second_window(self):
        """Crée et affiche la fenêtre secondaire, puis ferme la fenêtre principale."""
        modulename = self.moduleNameLineEdit.text().strip()  # Récupère le nom du module dans la QLineEdit
        
        if not modulename:
            # Affiche un message d'erreur si la QLineEdit est vide
            QMessageBox.warning(self, "Nom du module manquant", "Veuillez entrer le nom du module")
            return  # Empêche le passage à la fenêtre suivante
        
        tool_button_states = self.get_tool_button_states()
        modulename = self.moduleNameLineEdit.text()  # Récupère le nom du fichier depuis le QLineEdit
        self.second_window = SecondApp(tool_button_states, modulename)
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
    def __init__(self, tool_button_states, modulename):
        super().__init__()
        self.modulename = modulename  # Stocker le nom du module
        self.selected_item = ""  # Initialiser selected_item
        self.load_ui()
        self.display_tool_button_states(tool_button_states)
        self.setup_connections()
        self.max_power = 0  # Initialiser la puissance maximale
        self.collecting_data = False  # Flag to check if data collection is ongoing
        self.power_data = {}  # Dictionnaire pour stocker la puissance maximale pour chaque mode

    def load_ui(self):
        """Charge le fichier UI pour la fenêtre secondaire."""
        uic.loadUi('second.ui', self)

    def setup_connections(self):
        """Configure les connexions des signaux et slots pour la fenêtre secondaire."""
        self.startPushButton.clicked.connect(self.start_collecting)
        self.stopPushButton.clicked.connect(self.stop_collecting)
        self.endPushButton.clicked.connect(self.generate_excel)  # Connexion pour le bouton "End"
        self.ecoModecomboBox.currentIndexChanged.connect(self.save_selected_item)

    def display_tool_button_states(self, states):
        """Met à jour les éléments de la fenêtre secondaire en fonction des états des CheckBox."""
        self.update_light(self.fullPowerLight, states['fullpower'])
        self.update_light(self.lowBatteryLight, states['lowbattery'])
        self.update_ecoModecomboBox(states)

    def update_light(self, label, state):
        """Met à jour l'image du label en fonction de l'état (vert pour actif, rouge pour inactif)."""
        if state:
            label.setPixmap(QtGui.QPixmap('image/green_light.png'))
        else:
            label.setPixmap(QtGui.QPixmap('image/red_light.png'))

    def update_ecoModecomboBox(self, states):
        """Met à jour les éléments de la ComboBox en fonction des états des CheckBox."""
        self.ecoModecomboBox.clear()  # Vide la ComboBox avant de la mettre à jour
        
        if states['fullpower']:
            self.add_fullpower_items(states['lowbattery'])
        else:
            self.add_no_fullpower_items(states['lowbattery'])

    def add_fullpower_items(self, lowbattery):
        """Ajoute les éléments de la ComboBox lorsque le mode 'fullpower' est activé."""
        self.ecoModecomboBox.addItem("OFF")
        self.ecoModecomboBox.addItem("Sleep")
        self.ecoModecomboBox.addItem("ECO 0")
        self.ecoModecomboBox.addItem("ECO 1")
        self.ecoModecomboBox.addItem("ECO 2")
        if lowbattery:
            self.ecoModecomboBox.addItem("Low Battery")

    def add_no_fullpower_items(self, lowbattery):
        """Ajoute les éléments de la ComboBox lorsque le mode 'fullpower' est désactivé."""
        self.ecoModecomboBox.addItem("OFF")
        self.ecoModecomboBox.addItem("Sleep")
        self.ecoModecomboBox.addItem("ECO 0")
        if lowbattery:
            self.ecoModecomboBox.addItem("Low Battery")

    def save_selected_item(self):
        """Sauvegarde l'élément sélectionné dans la ComboBox."""
        self.selected_item = self.ecoModecomboBox.currentText()

    def start_collecting(self):
        """Démarre la collecte des données de puissance."""
        self.max_power = 0  # Réinitialiser la puissance maximale
        self.collecting_data = True
        self.collect_data_thread = threading.Thread(target=self.collect_data)
        self.collect_data_thread.start()

    def stop_collecting(self):
        """Arrête la collecte des données de puissance."""
        self.collecting_data = False
        if self.collect_data_thread.is_alive():
            self.collect_data_thread.join()
        self.selectedItemLabel.setText(f"Max Power: {self.max_power:.2f} W")
        self.power_data[self.selected_item] = self.max_power  # Enregistre la puissance maximale pour le mode actuel

    def collect_data(self):
        """Collecte les données de puissance à intervalle régulier."""
        while self.collecting_data:
            power = self.fetch_power_value()
            if power is not None:
                self.max_power = max(self.max_power, power)
            time.sleep(1)  # Attendre 1 seconde entre les collectes

    def fetch_power_value(self):
        """Récupère la valeur de puissance actuelle depuis l'URL."""
        url = 'http://192.168.0.2/Home.cgi'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Extrait la valeur à partir du contenu de la page web
                soup = BeautifulSoup(response.text, 'html.parser')

                # Trouver l'input avec l'attribut id "actcur"
                current_element = soup.find('input', {'id': 'actcur'})

                # Trouver l'input avec l'attribut id "actvol"
                voltage_element = soup.find('input', {'id': 'actvol'})

                # Extrait la valeur du courant de l'attribut "value" et conversion en float
                current = float(current_element['value'].replace(' A', ''))

                # Extrait la valeur de la tension de l'attribut "value" et conversion en float
                voltage = float(voltage_element['value'].replace(' V', ''))

                # Multiplication du courant par la tension pour avoir la puissance
                power = current * voltage
                return power
            else:
                print(f"Erreur {response.status_code} lors de la récupération de la page web de l'alimentation")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la valeur de puissance: {e}")
            return None

    def generate_excel(self):
        """Génère un fichier Excel avec la puissance maximale pour chaque mode et ferme la fenêtre."""
        try:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Max Power Data"

            # Ajouter des en-têtes
            sheet.append(["Mode", "Max Power (W)"])

            # Ajouter les données
            for mode, max_power in self.power_data.items():
                sheet.append([mode, max_power])

            # Créez le répertoire 'results' s'il n'existe pas
            results_dir = 'results'
            os.makedirs(results_dir, exist_ok=True)

            # Sauvegarder le fichier avec le nom spécifié dans le QLineEdit dans le répertoire 'results'
            modulename = self.modulename if self.modulename.endswith('.xlsx') else self.modulename + '.xlsx'
            file_path = os.path.join(results_dir, modulename)
            workbook.save(file_path)

            # Vérifier si le fichier a été créé correctement
            if os.path.isfile(file_path):
                print(f"Fichier Excel '{file_path}' créé avec succès.")
                # Fermer la fenêtre secondaire
                self.close()
            else:
                raise Exception("Le fichier Excel n'a pas été créé.")
        
        except Exception as e:
            # Afficher un message d'erreur en cas d'exception
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la création du fichier Excel : {e}")
            print(f"Erreur lors de la création du fichier Excel : {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
