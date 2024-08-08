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
        self.grap
