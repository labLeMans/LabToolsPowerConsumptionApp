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
        # self.timer.start(1000)  # Déplacer le démarrage dans la méthode start_measurement

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
        """Met à jour le fichier CSV avec les données de consommation."""
        with open(self.csv_filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
    
            # Utiliser les états capturés dans les marqueurs
            last_marker_state = {name: state[-1] for name, state in self.markers.items()}
    
            # Écrire la ligne dans le CSV
            writer.writerow([
                last_marker_state['manualSwitch'], 
                last_marker_state['ignition'], 
                last_marker_state['fullPower'], 
                last_marker_state['lowBattery'], 
                f"{power:.2f} W", 
                f"{elapsed_time:.3f} s"
            ])


    def generate_report(self):
        """Génère les trois documents dans le répertoire results/{nom du module}."""
        modulename = self.moduleNameLineEdit.text().strip()
        if not modulename:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom du module")
            return

        # Créer le répertoire results/{nom du module}
        directory = os.path.join('/home/pc/Documents/ITxPT/labtools/labtools/consumption_app_ITxPT/results', modulename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Générer les fichiers
        self.generate_csv(directory, modulename)
        self.save_graph_image(directory, modulename)
        self.generate_excel(directory, modulename)

    def generate_csv(self, directory, modulename):
        """Génère le fichier CSV."""
        self.csv_filepath = os.path.join(directory, f"power_consumption_data_{modulename}.csv")
        with open(self.csv_filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Écrire l'en-tête
            writer.writerow(["MainSwitch", "Ignition", "FullPower", "LowBattery", "MaxPower (W)", "Time (s)"])

    def save_graph_image(self, directory, modulename):
        """Sauvegarde le graphique en tant qu'image PNG."""
        imagepath = os.path.join(directory, f"power_consumption_graph_{modulename}.png")
        self.canvas.figure.savefig(imagepath, format='png')

    def generate_excel(self, directory, modulename):
        """Génère un fichier Excel avec les données de puissance et les états des marqueurs."""
        try:
            filepath = os.path.join(directory, f"power_consumption_report_{modulename}.xlsx")
            imagepath = os.path.join(directory, f"power_consumption_graph_{modulename}.png")
    
            # Créer le fichier Excel
            workbook = Workbook()
    
            # Récupérer la feuille par défaut
            sheet = workbook.active
    
            # Renommer la feuille par défaut
            sheet.title = "Max Power Data"
    
            # Ajouter les en-têtes
            sheet.append(["Manual Switch", "Ignition", "Full Power", "Low Battery", "Max Power (W)", "Duration (s)"])
    
            combined_markers = [(t, l, s) for m in self.markers.values() for t, l, s in zip(m['times'], [m['label']] * len(m['times']), m['state'])]
            combined_markers.sort(key=lambda x: x[0])
    
    
        
            print(f"Combined Markers: {combined_markers}")
    
            for i in range(len(combined_markers) - 1):
                print(f"Processing marker index {i}")  # Débug: affiche l'indice en cours de traitement
                print(f"Marker Data: {combined_markers[i]}")  # Débug: affiche les données du marqueur actuel
    
                start_time, end_time = combined_markers[i][0], combined_markers[i + 1][0]
                print(f"Start time: {start_time}, End time: {end_time}")  # Débug: affiche les temps de début et de fin
    
                max_power = max((p for t, p in zip(self.time_values, self.power_values) if start_time <= t <= end_time), default=None)
                print(f"Max Power between markers: {max_power}")  # Débug: affiche la puissance max entre les marqueurs
    
                if max_power is None:
                    print("No power values found between these markers, skipping...")  # Débug: Cas où aucune valeur de puissance n'est trouvée
                    continue
    
                duration = end_time - start_time
                print(f"Duration between markers: {duration}")  # Débug: affiche la durée entre les marqueurs
    
                # Ajoutez les états des marqueurs
                manual_switch_state = combined_markers[i][2] if len(combined_markers[i]) > 2 else ''
                ignition_state = combined_markers[i][2] if len(combined_markers[i]) > 2 else ''
                full_power_state = combined_markers[i][2] if len(combined_markers[i]) > 2 else ''
                low_battery_state = combined_markers[i][2] if len(combined_markers[i]) > 2 else ''
    
                # Débug: affiche l'état actuel des marqueurs
                print(f"States: manual_switch={manual_switch_state}, ignition={ignition_state}, full_power={full_power_state}, low_battery={low_battery_state}")
    
                sheet.append([
                    manual_switch_state,
                    ignition_state,
                    full_power_state,
                    low_battery_state,
                    max_power,
                    duration
                ])
        
            img = Image(imagepath)
            sheet.add_image(img, 'G5')
    
            workbook.save(filepath)
            print(f"Fichier Excel '{filepath}' créé avec succès.")
    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la création du fichier Excel: {e}")

    def start_measurement(self):
        """Démarre la mesure de la consommation."""
        modulename = self.moduleNameLineEdit.text().strip()
        if not modulename:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom du module avant de commencer.")
            return
        
        self.start_time = QtCore.QTime.currentTime()  # Réinitialise l'heure de départ
        self.power_values.clear()
        self.time_values.clear()
        self.init_data()  # Réinitialise les marqueurs et les données

        self.timer.start(1000)  # Commence la mise à jour du graphique toutes les secondes

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
