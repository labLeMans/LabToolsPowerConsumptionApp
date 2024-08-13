import sys
import requests
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout, QWidget, QPushButton, QDialog
from PyQt5 import uic, QtCore
from PyQt5.QtCore import pyqtSignal, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image

# Classe pour le canvas matplotlib
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

# Fenêtre pour afficher le graphique en plein écran
class GraphWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph")
        layout = QVBoxLayout(self)
        self.canvas = MplCanvas(self, width=10, height=8, dpi=100)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

# Classe principale de l'application
class MainApp(QMainWindow):
    power_updated = pyqtSignal(float)  # Signal pour mettre à jour la puissance affichée

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_graph()
        self.init_data()
        self.setup_connections()

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        uic.loadUi('/home/pc/Documents/ITxPT/labtools/labtools/consumption_app_ITxPT/wind.ui', self)

    def init_graph(self):
        """Initialise le graphique."""
        self.graphic_widget = QWidget()
        self.layout = QVBoxLayout(self.graphic_widget)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)
        self.gridLayout_2.addWidget(self.graphic_widget, 0, 0)

        # Bouton pour afficher le graphique en plein écran
        self.fullscreen_button = QPushButton("Afficher le graphique en plein écran")
        self.layout.addWidget(self.fullscreen_button)
        self.fullscreen_button.clicked.connect(self.show_fullscreen_graph)

        # Fenêtre de graphique en plein écran
        self.graph_window = GraphWindow()

    def init_data(self):
        """Initialise les données et les marqueurs."""
        self.start_time = QtCore.QTime.currentTime()  # Heure de départ
        self.power_values = []  # Valeurs de puissance
        self.time_values = []  # Valeurs de temps

        # Dictionnaire pour stocker les marqueurs
        self.markers = {
            'ignition': {'color': 'red', 'label': 'I', 'times': [], 'state': ['']},
            'fullPower': {'color': 'blue', 'label': 'F', 'times': [], 'state': ['']},
            'lowBattery': {'color': 'green', 'label': 'L', 'times': [], 'state': ['']},
            'manualSwitch': {'color': 'orange', 'label': 'M', 'times': [], 'state': ['']}
        }

        # Timer pour mettre à jour le graphique toutes les secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

    def setup_connections(self):
        """Configure les connexions entre les widgets et les fonctions."""
        self.manualSwitchCheckBox.clicked.connect(lambda: self.add_marker('manualSwitch'))
        self.ignitionCheckBox.clicked.connect(lambda: self.add_marker('ignition'))
        self.fullPowerCheckBox.clicked.connect(lambda: self.add_marker('fullPower'))
        self.lowBatteryCheckBox.clicked.connect(lambda: self.add_marker('lowBattery'))
        self.reportPushButton.clicked.connect(self.generate_report)
        self.startPushButton.clicked.connect(self.start_measurement)  # Connexion du bouton Start

    def show_fullscreen_graph(self):
        """Affiche la fenêtre de graphique en plein écran."""
        self.graph_window.showFullScreen()
        self.update_graph_in_window(self.graph_window.canvas)

    def add_marker(self, marker_name):
        """Ajoute un marqueur au moment actuel."""
        elapsed_time = self.start_time.secsTo(QtCore.QTime.currentTime())
        state = 'on' if getattr(self, f"{marker_name}CheckBox").isChecked() else 'off'
        self.markers[marker_name]['times'].append(elapsed_time)
        self.markers[marker_name]['state'].append(state)
        self.update_graph()

    def update_graph(self):
        """Récupère la puissance et met à jour le graphique."""
        power = self.fetch_power_value()
        if power is not None:
            elapsed_time = self.start_time.secsTo(QtCore.QTime.currentTime())
            self.power_values.append(power)
            self.time_values.append(elapsed_time)

            # Garde seulement les 100000 dernières valeurs
            if len(self.power_values) > 100000:
                self.power_values.pop(0)
                self.time_values.pop(0)

            self.canvas.axes.clear()
            self.canvas.axes.plot(self.time_values, self.power_values, label='Power (W)')
            self.update_markers_on_canvas(self.canvas.axes)
            self.canvas.draw()

            self.update_graph_in_window(self.graph_window.canvas)
            self.power_updated.emit(power)  # Émettre le signal pour mettre à jour l'affichage

            # Ajouter les données au fichier CSV si le fichier CSV a été créé
            if hasattr(self, 'csv_filepath'):
                self.update_csv(elapsed_time, power)

    def fetch_power_value(self):
        """Récupère la valeur de puissance actuelle depuis l'URL."""
        url = 'http://192.168.0.2/Home.cgi'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                current = float(soup.find('input', {'id': 'actcur'})['value'].replace(' A', ''))
                voltage = float(soup.find('input', {'id': 'actvol'})['value'].replace(' V', ''))
                return current * voltage  # Calcul de la puissance
            else:
                raise Exception(f"Erreur {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la récupération de la puissance: {e}")
            return None

    def update_markers_on_canvas(self, axes):
        """Met à jour les marqueurs sur le graphique."""
        for marker_name, marker_data in self.markers.items():
            for marker_time, state in zip(marker_data['times'], marker_data['state']):
                axes.axvline(x=marker_time, color=marker_data['color'], label=f"{marker_data['label']}_{state}")
                axes.text(marker_time, 0, f"{marker_data['label']}_{state}", color=marker_data['color'], rotation=90, verticalalignment='bottom')
        self.display_max_between_markers(axes)

    def display_max_between_markers(self, axes):
        """Affiche la puissance maximale entre les marqueurs sur le graphique."""
        combined_markers = [(t, l, s) for m in self.markers.values() for t, l, s in zip(m['times'], [m['label']] * len(m['times']), m['state'])]
        combined_markers.sort(key=lambda x: x[0])

        for i in range(len(combined_markers) - 1):
            start_time, end_time = combined_markers[i][0], combined_markers[i + 1][0]
            max_power = max(p for t, p in zip(self.time_values, self.power_values) if start_time <= t <= end_time)
            mid_time = (start_time + end_time) / 2
            axes.text(mid_time, max_power, f"Max: {max_power:.2f} W", verticalalignment='bottom')

    def update_graph_in_window(self, canvas):
        """Met à jour le graphique dans la fenêtre donnée."""
        canvas.axes.clear()
        canvas.axes.plot(self.time_values, self.power_values, label='Power (W)')
        canvas.axes.set_xlabel("Time (s)")
        canvas.axes.set_ylabel("Power (W)")
        self.update_markers_on_canvas(canvas.axes)
        canvas.draw()

    def update_csv(self, elapsed_time, power):
        """Met à jour le fichier CSV et Excel avec les données de consommation."""
        with open(self.csv_filepath, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Déterminer les états des switches
            main_switch = 'on' if self.manualSwitchCheckBox.isChecked() else 'off'
            ignition = 'on' if self.ignitionCheckBox.isChecked() else 'off'
            full_power = 'on' if self.fullPowerCheckBox.isChecked() else 'off'
            low_battery = 'on' if self.lowBatteryCheckBox.isChecked() else 'off'

            # Écrire la ligne dans le CSV
            writer.writerow([main_switch, ignition, full_power, low_battery, f"{power:.2f} W", f"{elapsed_time:.3f} s"])

        # Mettre à jour le fichier Excel également
        if hasattr(self, 'excel_filepath'):
            self.update_excel(elapsed_time, power)

    def update_excel(self, elapsed_time, power):
        """Met à jour le fichier Excel avec les données."""
        wb = Workbook()
        ws = wb.active
        ws.append(['Main Switch', 'Ignition', 'Full Power', 'Low Battery', 'Power (W)', 'Time (s)'])
        
        # Copie des données du CSV dans l'Excel
        with open(self.csv_filepath, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                ws.append(row)

        # Sauvegarde du fichier Excel
        wb.save(self.excel_filepath)

    def start_measurement(self):
        """Démarre la mesure et initialise les fichiers CSV et Excel."""
        # Récupération du nom du module
        filename = self.moduleNameLineEdit.text().strip()
        
        # Vérification si le nom du module est manquant
        if not filename:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom du module avant de démarrer la mesure.")
            return
        
        # Construction du chemin du répertoire pour les fichiers
        path = "/home/pc/Documents/ITxPT/labtools/labtools/consumption_app_ITxPT/results"
        module_path = os.path.join(path, filename)
        
        # Créer le répertoire s'il n'existe pas déjà
        os.makedirs(module_path, exist_ok=True)
        
        # Construction des chemins de fichier
        self.csv_filepath = os.path.join(module_path, f"{filename}.csv")
        self.excel_filepath = os.path.join(module_path, f"{filename}.xlsx")
        self.graph_image_filepath = os.path.join(module_path, f"{filename}.png")
    
        # Initialisation du fichier CSV
        with open(self.csv_filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Main Switch', 'Ignition', 'Full Power', 'Low Battery', 'Power (W)', 'Time (s)'])
    
        # Initialisation du fichier Excel
        wb = Workbook()
        ws = wb.active
        ws.append(['Main Switch', 'Ignition', 'Full Power', 'Low Battery', 'Power (W)', 'Time (s)'])
        wb.save(self.excel_filepath)
    
        # Démarrer le timer pour mettre à jour le graphique toutes les secondes
        self.timer.start(1000)


    def generate_report(self):
        """Génère le rapport à partir des fichiers CSV et Excel."""
        if not hasattr(self, 'csv_filepath'):
            QMessageBox.warning(self, "Erreur", "Le fichier de données n'existe pas.")
            return

        # Sauvegarder le graphique en tant qu'image
        self.save_graph_as_image()

        wb = Workbook()
        ws = wb.active
        ws.title = "Consumption Data"

        # Copier les données CSV dans Excel
        with open(self.csv_filepath, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                ws.append(row)

        # Ajout des marqueurs à un autre onglet
        ws_markers = wb.create_sheet(title="Markers")
        ws_markers.append(["Marker", "State", "Time (s)"])
        for marker_name, marker_data in self.markers.items():
            for marker_time, state in zip(marker_data['times'], marker_data['state']):
                ws_markers.append([marker_name, state, marker_time])

        # Ajout du graphique dans le rapport
        if os.path.exists(self.graph_image_filepath):
            img = Image(self.graph_image_filepath)
            ws.add_image(img, 'H10')
        else:
            QMessageBox.warning(self, "Erreur", "L'image du graphique n'a pas été trouvée.")


        # Sauvegarder le fichier Excel
        wb.save(self.excel_filepath)
        QMessageBox.information(self, "Succès", f"Rapport généré: {self.excel_filepath}")

    def save_graph_as_image(self):
        """Sauvegarde le graphique actuel en tant qu'image PNG."""
        if not hasattr(self, 'csv_filepath'):
            return  # Assurez-vous que les fichiers sont initialisés avant de sauvegarder l'image
        
        # Créez une image du graphique
        self.canvas.figure.savefig(self.graph_image_filepath, format='png')


# Application
def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
