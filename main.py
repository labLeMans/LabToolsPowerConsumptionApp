import sys
import requests
import threading
import time
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
from bs4 import BeautifulSoup
from openpyxl import Workbook

class MainApp(QMainWindow):
    power_updated = pyqtSignal(float)  # Signal personnalisé pour mettre à jour la puissance
    def __init__(self):
        super().__init__()
        self.load_ui()
        self.setup_connections()
        self.max_power = 0  # Initialiser la puissance maximale
        self.collecting_data = False  # Flag to check if data collection is ongoing
        self.power_data = {}  # Dictionnaire pour stocker la puissance maximale pour chaque mode
        #self.modulename = modulename # Stocker le nom du module
        self.selected_item = "OFF"
        self.power_updated.connect(self.update_power_display)# Connecter le signal power_updated à la méthode update_power_display


    def load_ui(self):
        """Charge le fichier UI pour la fenêtre principale."""
        uic.loadUi('wind.ui', self)

    def setup_connections(self):
        """Configure les connexions des signaux et slots."""
        #self.manualSwitchCheckBox.clicked.connect()
        #self.ignitionCheckBox.clicked.connect()
        #self.fullPowerCheckBox.clicked.connect()
        #self.lowBatteryCheckBox.clicked.connect()
        self.reportPushButton.clicked.connect(self.module_identification)

    def module_identification(self, modulename):
        """Vérification si le nom du module à bien été renseigné."""
        modulename = self.moduleNameLineEdit.text().strip() # Récupère le nom du module dans la QLineEdit
        if not modulename:
            # Affiche un message d'erreur si la QLineEdit est vide
            QMessageBox.warning(self, "Nom du module manquant", "Veuillez entrer le nom du module")
            return # Empêche le passage à la fenêtre suivante
        else:
            self.generate_excel

    def fetch_power_value(self):
        """Récupère la valeur de puissance actuelle depuis l'URL."""
        url = 'http://192.168.0.2/Home.cgi'
        try:
            # vérification de la connectivité à l'url
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
                QMessageBox.warning(self, "Erreur {response.status_code} lors de la récupération de la page web de l'alimentation")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la valeur de puissance: {e}")
            QMessageBox.warning(self, "Erreur lors de la récupération de la valeur de puissance: {e}")
            return None
        

    def update_power_display(self, power):
        """Met à jour l'affichage de la puissance en temps réel."""
        self.selectedItemLabel.setText(f"Max Power: {power:.2f} W")

    def generate_excel(self):
        """Génère un fichier Excel avec la puissance maximale pour chaque mode et ferme la fenêtre."""
        try:
            # Créer le répertoire 'results' s'il n'existe pas
            directory = 'results'
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Nom du fichier Excel avec le préfixe et le nom du module
            filename = f"power_consumption_{self.modulename}.xlsx"
            filepath = os.path.join(directory, filename) # chemin complet du fichier

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Max Power Data"

            # Ajouter des en-têtes
            sheet.append(["Mode", "Max Power (W)"])

            # Ajouter les données
            for mode, max_power in self.power_data.items():
                sheet.append([mode, max_power])

            # Sauvegarder le fichier avec le nom spécifié dans le QLineEdit
            workbook.save(filepath)

            # Vérifier si le fichier a été créé correctement
            if os.path.isfile(filepath):
                print(f"Fichier Excel '{filepath}' créé avec succès.")
                # Fermer la fenêtre secondaire
                self.close()
            else:
                raise Exception("Le fichier Excel n'a pas été créé.")
        
        except Exception as e:
            # Afficher un message d'erreur en cas d'exception
            print(f"Erreur lors de la création du fichier Excel : {e}")
            QMessageBox.warning(self, "Erreur lors de la création du fichier Excel : {e}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
