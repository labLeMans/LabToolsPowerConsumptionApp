import sys
import requests
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout, QWidget
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from bs4 import BeautifulSoup
from openpyxl import Workbook


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainApp(QMainWindow):
    power_updated = pyqtSignal(float)  # Signal personnalisé pour mettre à jour la puissance

    def __init__(self):
        super().__init__()
        self.load_ui()
        self.setup_connections()
        self.max_power = 0  # Initialiser la puissance maximale
        self.collecting_data = False  # Flag to check if data collection is ongoing
        self.power_data = {}  # Dictionnaire pour stocker la puissance maximale pour chaque mode
        self.selected_item = "OFF"
        self.power_updated.connect(self.update_power_display)  # Connecter le signal power_updated à la méthode update_power_display

        # Créer un widget pour contenir le canvas de matplotlib
        self.graphic_widget = QWidget()
        self.layout = QVBoxLayout(self.graphic_widget)

        # Créer le canvas de matplotlib
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)

        # Ajouter le widget de graphique dans le gridLayout_2
        self.gridLayout_2.addWidget(self.graphic_widget, 0, 0)

        # Initialiser une liste pour stocker les données de puissance
        self.power_values = []
        self.time_values = []

        # Configurer le QTimer pour mettre à jour les données toutes les secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)  # Mettre à jour toutes les secondes
        self.start_time = QtCore.QTime.currentTime()  # Enregistrer l'heure de départ

    def load_ui(self):
        """Charge le fichier UI pour la fenêtre principale."""
        uic.loadUi('wind.ui', self)

    def setup_connections(self):
        """Configure les connexions des signaux et slots."""
        self.reportPushButton.clicked.connect(self.module_identification)

    def module_identification(self):
        """Vérification si le nom du module à bien été renseigné."""
        modulename = self.moduleNameLineEdit.text().strip()  # Récupère le nom du module dans la QLineEdit
        if not modulename:
            # Affiche un message d'erreur si la QLineEdit est vide
            QMessageBox.warning(self, "Nom du module manquant", "Veuillez entrer le nom du module")
            return  # Empêche le passage à la fenêtre suivante
        else:
            self.generate_excel()

    def fetch_power_value(self):
        """Récupère la valeur de puissance actuelle depuis l'URL."""
        url = 'http://192.168.0.2/Home.cgi'
        try:
            response = requests.get(url)
            if response.status_code == 200:
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
                QMessageBox.warning(self, f"Erreur {response.status_code} lors de la récupération de la page web de l'alimentation")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la valeur de puissance: {e}")
            QMessageBox.warning(self, f"Erreur lors de la récupération de la valeur de puissance: {e}")
            return None

    def update_power_display(self, power):
        """Met à jour l'affichage de la puissance en temps réel."""
        self.selectedItemLabel.setText(f"Max Power: {power:.2f} W")

    def update_graph(self):
        """Met à jour le graphique avec les nouvelles données de puissance."""
        power = self.fetch_power_value()
        if power is not None:
            current_time = QtCore.QTime.currentTime()
            elapsed_time = self.start_time.secsTo(current_time)  # Temps écoulé en secondes

            self.power_values.append(power)
            self.time_values.append(elapsed_time)
            if len(self.power_values) > 100:  # Garder seulement les 100 dernières valeurs
                self.power_values.pop(0)
                self.time_values.pop(0)

            self.canvas.axes.clear()
            self.canvas.axes.plot(self.time_values, self.power_values, label='Power (W)')
            self.canvas.axes.set_xlabel("Time (s)")
            self.canvas.axes.set_ylabel("Power (W)")
            self.canvas.axes.legend()
            self.canvas.draw()
            self.power_updated.emit(power)  # Émettre le signal pour mettre à jour l'affichage de la puissance

    def generate_excel(self):
        """Génère un fichier Excel avec la puissance maximale pour chaque mode et ferme la fenêtre."""
        try:
            modulename = self.moduleNameLineEdit.text().strip()
            directory = 'results'
            if not os.path.exists(directory):
                os.makedirs(directory)

            filename = f"power_consumption_{modulename}.xlsx"
            filepath = os.path.join(directory, filename)

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Max Power Data"

            # Ajouter des en-têtes
            sheet.append(["Mode", "Max Power (W)"])

            # Ajouter les données
            for mode, max_power in self.power_data.items():
                sheet.append([mode, max_power])

            workbook.save(filepath)

            if os.path.isfile(filepath):
                print(f"Fichier Excel '{filepath}' créé avec succès.")
                self.close()
            else:
                raise Exception("Le fichier Excel n'a pas été créé.")

        except Exception as e:
            print(f"Erreur lors de la création du fichier Excel : {e}")
            QMessageBox.warning(self, f"Erreur lors de la création du fichier Excel : {e}")
            return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
