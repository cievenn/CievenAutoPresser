import tkinter as tk
from core.presser_app import AutoPresserUltimate

if __name__ == "__main__":
    # Initialise la fenêtre graphique
    root = tk.Tk()
    
    # Lance l'application
    app = AutoPresserUltimate(root)
    
    # Garde la fenêtre ouverte
    root.mainloop()