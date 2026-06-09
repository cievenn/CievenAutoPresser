import json
import os

class DatabaseManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.db_path = os.path.join(self.data_dir, "presets.json")
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load(self):
        """Charge la base de données ou en crée une vide, en garantissant la structure."""
        # Modèle de base garanti
        db = {"presets": {}, "current": {}}
        
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # On sécurise la récupération des clés au cas où le JSON est corrompu
                    if isinstance(data, dict):
                        db["presets"] = data.get("presets", {})
                        db["current"] = data.get("current", {})
            except Exception as e:
                print(f"Erreur de lecture de la base (fichier recréé) : {e}")
                
        return db

    def save(self, data):
        """Écrit les données dans le fichier JSON."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)