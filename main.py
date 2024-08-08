import sys
import requests
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QDialog
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class GraphWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph")
        self.layout = QVBoxLayout(self)
        self.canvas = MplCanvas(self, width=10, height=8, dpi=100)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

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

        # Ajouter un bouton pour afficher le graphique en plein écran
        self.fullscreen_button = QPushButton("Afficher le graphique en plein écran")
        self.layout.addWidget(self.fullscreen_button)
        self.fullscreen_button.clicked.connect(self.show_fullscreen_graph)

        # Initialiser une liste pour stocker les données de puissance
        self.power_values = []
        self.time_values = []

        # Configurer le QTimer pour mettre à jour les données toutes les secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)  # Mettre à jour toutes les secondes
        self.start_time = QtCore.QTime.currentTime()  # Enregistrer l'heure de départ

        # Ajouter les marqueurs
        self.markers = {
            'ignition': {'color': 'red', 'label': 'I', 'times': [], 'state': []},
            'fullPower': {'color': 'blue', 'label': 'F', 'times': [], 'state': []},
            'lowBattery': {'color': 'green', 'label': 'L', 'times': [], 'state': []},
            'manualSwitch': {'color': 'orange', 'label': 'M', 'times': [], 'state': []}
        }

        # Initialiser la fenêtre de graphique en plein écran
        self.graph_window = GraphWindow()

    def show_fullscreen_graph(self):
        """Affiche la fenêtre de graphique en plein écran."""
        self.graph_window.showFullScreen()
        self.update_fullscreen_graph()

    def update_fullscreen_graph(self):
        """Met à jour le graphique dans la fenêtre de graphique en plein écran."""
        self.graph_window.canvas.axes.clear()
        self.graph_window.canvas.axes.plot(self.time_values, self.power_values, label='Power (W)')
        self.graph_window.canvas.axes.set_xlabel("Time (s)")
        self.graph_window.canvas.axes.set_ylabel("Power (W)")
        self.graph_window.canvas.axes.legend()
        self.update_markers_fullscreen()
        self.graph_window.canvas.draw()

    def update_markers_fullscreen(self):
        """Met à jour les marqueurs sur le graphique en plein écran."""
        for marker_name, marker_data in self.markers.items():
            for marker_time, state in zip(marker_data['times'], marker_data['state']):
                self.graph_window.canvas.axes.axvline(x=marker_time, color=marker_data['color'], label=f"{marker_data['label']}_{state}")
                self.graph_window.canvas.axes.text(marker_time, 0, f"{marker_data['label']}_{state}", color=marker_data['color'], rotation=90, verticalalignment='bottom')

        # Afficher les maximas entre les marqueurs
        self.display_max_between_markers(self.graph_window.canvas.axes)

    def add_marker_time(self, marker_name, state):
        """Enregistre le temps actuel pour un marqueur donné avec son état."""
        current_time = QtCore.QTime.currentTime()
        elapsed_time = self.start_time.secsTo(current_time)  # Temps écoulé en secondes
        self.markers[marker_name]['times'].append(elapsed_time)
        self.markers[marker_name]['state'].append(state)
        self.update_graph()

    def update_markers(self):
        """Met à jour les marqueurs sur le graphique."""
        for marker_name, marker_data in self.markers.items():
            for marker_time, state in zip(marker_data['times'], marker_data['state']):
                self.canvas.axes.axvline(x=marker_time, color=marker_data['color'], label=f"{marker_data['label']}_{state}")
                self.canvas.axes.text(marker_time, 0, f"{marker_data['label']}_{state}", color=marker_data['color'], rotation=90, verticalalignment='bottom')

        # Afficher les maximas entre les marqueurs
        self.display_max_between_markers(self.canvas.axes)

    def load_ui(self):
        """Charge le fichier UI pour la fenêtre principale."""
        uic.loadUi('wind.ui', self)

    def setup_connections(self):
        """Configure les connexions des signaux et slots."""
        self.manualSwitchCheckBox.clicked.connect(lambda: self.add_marker_time('manualSwitch', 'on' if self.manualSwitchCheckBox.isChecked() else 'off'))
        self.ignitionCheckBox.clicked.connect(lambda: self.add_marker_time('ignition', 'on' if self.ignitionCheckBox.isChecked() else 'off'))
        self.fullPowerCheckBox.clicked.connect(lambda: self.add_marker_time('fullPower', 'on' if self.fullPowerCheckBox.isChecked() else 'off'))
        self.lowBatteryCheckBox.clicked.connect(lambda: self.add_marker_time('lowBattery', 'on' if self.lowBatteryCheckBox.isChecked() else 'off'))
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
        self.powerLabel.setText(f"Max Power: {power:.2f} W")

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
            self.update_markers()
            self.canvas.draw()
            self.update_fullscreen_graph()
            self.power_updated.emit(power)  # Émettre le signal pour mettre à jour l'affichage de la puissance

    def display_max_between_markers(self, axes):
        """Affiche le maximum de puissance entre les marqueurs."""
        for marker_name, marker_data in self.markers.items():
            if len(marker_data['times']) >= 2:
                for i in range(len(marker_data['times']) - 1):
                    start_time = marker_data['times'][i]
                    end_time = marker_data['times'][i + 1]
                    start_idx = next(idx for idx, val in enumerate(self.time_values) if val >= start_time)
                    end_idx = next(idx for idx, val in enumerate(self.time_values) if val >= end_time)
                    max_power = max(self.power_values[start_idx:end_idx])
                    max_time = self.time_values[self.power_values.index(max_power)]
                    axes.text(max_time, max_power, f"Max: {max_power:.2f} W", color=marker_data['color'], verticalalignment='bottom')

    def generate_excel(self):
        """Génère un fichier Excel avec la puissance maximale pour chaque mode, ajoute le graphique, et ferme la fenêtre."""
        try:
            modulename = self.moduleNameLineEdit.text().strip()
            directory = 'results'
            if not os.path.exists(directory):
                os.makedirs(directory)

            filename = f"power_consumption_{modulename}.xlsx"
            imagename = f"power_graph_{modulename}.png"
            filepath = os.path.join(directory, filename)
            imagepath = os.path.join(directory, imagename)  # Chemin pour l'image du graphique

            # Sauvegarder le graphique comme une image
            self.canvas.figure.savefig(imagepath, format='png')

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Max Power Data"

            # Ajouter des en-têtes
            sheet.append(["Mode", "Max Power (W)"])

            # Ajouter les données
            for mode, max_power in self.power_data.items():
                sheet.append([mode, max_power])

            # Ajouter l'image du graphique
            img = Image(imagepath)
            sheet.add_image(img, 'E5')  # Positionner l'image à la cellule E5

            # Sauvegarder le fichier Excel
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
