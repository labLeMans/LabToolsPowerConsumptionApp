# consumption_app_ITxPT

## Installation de Qt Creator:
sudo apt install qtcreator
## Lancement de Qt Designer
designer
## Installer les outils nécessaires:
### installation de PyQt intaller pour générer l'exécutable
pip install pyqt5 pyinstaller
pip install pyinstaller
## Convertir le fichier '.ui' en fichier python:
pyuic5 -o nom_du_fichier.py nom_du_fichier.ui
## Créer l'éxécutable:
pyinstaller --onefile main.py

