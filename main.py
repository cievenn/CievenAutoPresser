import tkinter as tk
import os
import sys
from core.presser_app import AutoPresserUltimate

def resource_path(relative_path):
    """Obtient le chemin absolu de la ressource, compatible avec l'exe PyInstaller."""
    try:
        # PyInstaller crée un dossier temporaire _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # Initialise la fenêtre graphique
    root = tk.Tk()
    
    # Applique ton logo à la fenêtre et à la barre des tâches
    try:
        root.iconbitmap(resource_path('srwautopresser.ico'))
    except:
        pass # Sécurité au cas où l'icône est introuvable
    
    # Lance l'application
    app = AutoPresserUltimate(root)
    
    # Garde la fenêtre ouverte
    root.mainloop()