import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import mouse
import threading
import time
from core.database import DatabaseManager

KEYS_LIST = [
    "clic_gauche", "clic_droit", "clic_milieu",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "backspace", "down", "enter", "esc", "left", "right", "space", "tab", "up",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
]
MODIFIERS_LIST = ["", "ctrl", "alt", "shift"]

class AutoPresserUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Keyboard & Mouse Holder Pro")
        self.root.geometry("740x520")
        self.root.resizable(False, False)

        self.search_buffers = {}
        self.search_times = {}

        self.stop_event = threading.Event()
        self.stop_event.set()
        self.current_start_hotkey = None
        self.current_stop_hotkey = None

        self.db_manager = DatabaseManager()
        self.database = self.db_manager.load()

        self.create_widgets()
        self.apply_loaded_config()
        self.setup_live_listeners()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -----------------------------------------------------
    # OUTILS DE SÉCURITÉ (GETTERS & SETTERS ANTI-CRASH)
    # -----------------------------------------------------
    def safe_int_get(self, int_var, default=0):
        try:
            return int_var.get()
        except tk.TclError:
            return default

    def safe_int_set(self, int_var, value, default=0):
        try:
            int_var.set(int(value))
        except (ValueError, TypeError, tk.TclError):
            int_var.set(default)

    def set_ui_state(self, state):
        """ Gèle ou dégèle l'interface pour empêcher les modifications en cours d'exécution """
        widgets = [
            self.preset_entry, self.btn_save, self.btn_delete, self.presets_listbox,
            self.cb_start_mod, self.cb_start_key, self.cb_stop_mod, self.cb_stop_key,
            self.cb_action_key, self.chk_ctrl, self.chk_alt, self.chk_shift,
            self.rb_continu, self.rb_duree, self.rb_spam,
            self.sb_duration, self.sb_spam_times, self.sb_spam_delay
        ]
        for w in widgets:
            try:
                if state == "normal" and isinstance(w, ttk.Combobox):
                    w.config(state="readonly")
                else:
                    w.config(state=state)
            except tk.TclError:
                pass

    # -----------------------------------------------------
    # CRÉATION DE L'INTERFACE
    # -----------------------------------------------------
    def create_widgets(self):
        self.left_frame = tk.Frame(self.root, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(self.root, padx=10, pady=10, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="y")

        # PRESETS (Droite)
        tk.Label(self.right_frame, text="💾 PRESETS", font=("Segoe UI", 11, "bold"), bg="#f0f0f0").pack(anchor="w", pady=(5, 5))
        tk.Label(self.right_frame, text="Nom du preset :", bg="#f0f0f0", font=("Segoe UI", 9)).pack(anchor="w")
        self.preset_name_var = tk.StringVar()
        self.preset_entry = ttk.Entry(self.right_frame, textvariable=self.preset_name_var, width=22)
        self.preset_entry.pack(anchor="w", pady=2)
        
        self.btn_save = ttk.Button(self.right_frame, text="Sauvegarder", command=self.save_preset)
        self.btn_save.pack(anchor="w", fill="x", pady=(0, 15))

        tk.Label(self.right_frame, text="Vos Presets :", bg="#f0f0f0", font=("Segoe UI", 9, "italic")).pack(anchor="w")
        self.presets_listbox = tk.Listbox(self.right_frame, width=22, height=14, font=("Segoe UI", 10))
        self.presets_listbox.pack(anchor="w", fill="both", expand=True)
        self.presets_listbox.bind("<<ListboxSelect>>", self.on_preset_selected)
        
        self.btn_delete = ttk.Button(self.right_frame, text="❌ Supprimer", command=self.delete_preset)
        self.btn_delete.pack(anchor="w", fill="x", pady=(5, 0))

        # CONTROLES (Gauche)
        frame_hotkeys = tk.LabelFrame(self.left_frame, text=" 1. Raccourcis globaux ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        frame_hotkeys.pack(fill="x", pady=5)

        tk.Label(frame_hotkeys, text="Commencer :").grid(row=0, column=0, sticky="w")
        self.start_mod_var = tk.StringVar(value="ctrl")
        self.cb_start_mod = ttk.Combobox(frame_hotkeys, textvariable=self.start_mod_var, values=MODIFIERS_LIST, width=7, state="readonly")
        self.cb_start_mod.grid(row=0, column=1, padx=5)
        tk.Label(frame_hotkeys, text="+").grid(row=0, column=2)
        self.start_key_var = tk.StringVar(value="f1")
        self.cb_start_key = ttk.Combobox(frame_hotkeys, textvariable=self.start_key_var, values=KEYS_LIST, width=12, state="readonly")
        self.cb_start_key.grid(row=0, column=3, padx=5)

        tk.Label(frame_hotkeys, text="Finir :").grid(row=1, column=0, sticky="w", pady=10)
        self.stop_mod_var = tk.StringVar(value="ctrl")
        self.cb_stop_mod = ttk.Combobox(frame_hotkeys, textvariable=self.stop_mod_var, values=MODIFIERS_LIST, width=7, state="readonly")
        self.cb_stop_mod.grid(row=1, column=1, padx=5)
        tk.Label(frame_hotkeys, text="+").grid(row=1, column=2)
        self.stop_key_var = tk.StringVar(value="f2")
        self.cb_stop_key = ttk.Combobox(frame_hotkeys, textvariable=self.stop_key_var, values=KEYS_LIST, width=12, state="readonly")
        self.cb_stop_key.grid(row=1, column=3, padx=5)

        for cb in [self.cb_start_key, self.cb_stop_key]:
            cb.bind("<Key>", lambda e, c=cb: self.smart_search_combobox(e, c))

        # ACTION (Gauche)
        frame_action = tk.LabelFrame(self.left_frame, text=" 2. Touche ou Souris à simuler ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        frame_action.pack(fill="x", pady=5)
        
        tk.Label(frame_action, text="Cible :").grid(row=0, column=0, sticky="w", pady=5)
        self.action_key_var = tk.StringVar(value="space")
        self.cb_action_key = ttk.Combobox(frame_action, textvariable=self.action_key_var, values=KEYS_LIST, width=15, state="readonly")
        self.cb_action_key.grid(row=0, column=1, padx=5, sticky="w", pady=5)
        self.cb_action_key.bind("<Key>", lambda e, c=self.cb_action_key: self.smart_search_combobox(e, c))

        tk.Label(frame_action, text="Modificateurs :").grid(row=1, column=0, sticky="w", pady=5)
        self.mod_ctrl_var, self.mod_alt_var, self.mod_shift_var = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        frame_mods = tk.Frame(frame_action)
        frame_mods.grid(row=1, column=1, sticky="w", pady=5)
        
        self.chk_ctrl = ttk.Checkbutton(frame_mods, text="Ctrl", variable=self.mod_ctrl_var)
        self.chk_ctrl.pack(side="left", padx=2)
        self.chk_alt = ttk.Checkbutton(frame_mods, text="Alt", variable=self.mod_alt_var)
        self.chk_alt.pack(side="left", padx=2)
        self.chk_shift = ttk.Checkbutton(frame_mods, text="Shift", variable=self.mod_shift_var)
        self.chk_shift.pack(side="left", padx=2)

        # GESTION
        frame_options = tk.LabelFrame(self.left_frame, text=" 3. Gestion ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        frame_options.pack(fill="x", pady=5)
        
        self.mode_var = tk.StringVar(value="hold_continu")
        
        self.rb_continu = ttk.Radiobutton(frame_options, text="En continu (Presse tout le temps)", variable=self.mode_var, value="hold_continu")
        self.rb_continu.grid(row=0, column=0, sticky="w", columnspan=5, pady=5)
        
        self.rb_duree = ttk.Radiobutton(frame_options, text="Relâcher après :", variable=self.mode_var, value="hold_duree")
        self.rb_duree.grid(row=1, column=0, sticky="w", pady=5)
        
        self.duration_var = tk.IntVar(value=5)
        self.sb_duration = ttk.Spinbox(frame_options, from_=1, to=3600, textvariable=self.duration_var, width=5)
        self.sb_duration.grid(row=1, column=1, sticky="w", padx=2)
        tk.Label(frame_options, text="secondes").grid(row=1, column=2, sticky="w", columnspan=3)

        self.rb_spam = ttk.Radiobutton(frame_options, text="Spam :", variable=self.mode_var, value="spam")
        self.rb_spam.grid(row=2, column=0, sticky="w", pady=5)
        
        self.spam_times_var = tk.IntVar(value=1)
        self.sb_spam_times = ttk.Spinbox(frame_options, from_=1, to=999, textvariable=self.spam_times_var, width=4)
        self.sb_spam_times.grid(row=2, column=1, sticky="w", padx=2)
        tk.Label(frame_options, text="fois par").grid(row=2, column=2, sticky="w", padx=2)
        
        self.spam_delay_var = tk.IntVar(value=50)
        self.sb_spam_delay = ttk.Spinbox(frame_options, from_=1, to=10000, textvariable=self.spam_delay_var, width=5)
        self.sb_spam_delay.grid(row=2, column=3, sticky="w", padx=2)
        tk.Label(frame_options, text="ms").grid(row=2, column=4, sticky="w")

        # Statut
        self.status_label = tk.Label(self.left_frame, text="Statut : PRÊT", font=("Segoe UI", 13, "bold"), fg="#2980b9")
        self.status_label.pack(pady=20)

    # -----------------------------------------------------
    # SMART SEARCH
    # -----------------------------------------------------
    def smart_search_combobox(self, event, combobox):
        cb_id = id(combobox)
        now = time.time()
        
        if cb_id not in self.search_times or (now - self.search_times[cb_id] > 0.8):
            self.search_buffers[cb_id] = ""
            
        self.search_times[cb_id] = now
        char = event.char.lower()
        if not char.isalnum() and char not in ["_"]: return
        
        self.search_buffers[cb_id] += char
        buffer = self.search_buffers[cb_id]

        if len(buffer) > 1 and all(c == char for c in buffer):
            matches = [idx for idx, val in enumerate(combobox['values']) if val.lower().startswith(char)]
            if matches:
                current_idx = combobox.current()
                if current_idx in matches:
                    next_idx = matches[(matches.index(current_idx) + 1) % len(matches)]
                    combobox.current(next_idx)
                    combobox.event_generate("<<ComboboxSelected>>")
                    return "break"
        
        for idx, val in enumerate(combobox['values']):
            if val.lower().startswith(buffer):
                combobox.current(idx)
                combobox.event_generate("<<ComboboxSelected>>")
                break
        return "break"

    def setup_live_listeners(self):
        for var in [self.start_mod_var, self.start_key_var, self.stop_mod_var, self.stop_key_var]:
            var.trace_add("write", lambda *args: self.apply_hotkeys_live())
        self.apply_hotkeys_live()

    def apply_hotkeys_live(self):
        start_hk = f"{self.start_mod_var.get()}+{self.start_key_var.get()}" if self.start_mod_var.get() else self.start_key_var.get()
        stop_hk = f"{self.stop_mod_var.get()}+{self.stop_key_var.get()}" if self.stop_mod_var.get() else self.stop_key_var.get()

        if start_hk == stop_hk: 
            self.status_label.config(text="ERREUR : Raccourcis identiques", fg="#c0392b")
            return

        if self.current_start_hotkey:
            try: keyboard.remove_hotkey(self.current_start_hotkey)
            except: pass
        if self.current_stop_hotkey:
            try: keyboard.remove_hotkey(self.current_stop_hotkey)
            except: pass

        try:
            keyboard.add_hotkey(start_hk, self.start_holding)
            self.current_start_hotkey = start_hk
            keyboard.add_hotkey(stop_hk, self.stop_holding)
            self.current_stop_hotkey = stop_hk
            self.status_label.config(text=f"PRÊT ({start_hk.upper()} pour lancer)", fg="#2980b9")
        except: pass

    # -----------------------------------------------------
    # LOGIQUE D'EXÉCUTION
    # -----------------------------------------------------
    def start_holding(self):
        if not self.stop_event.is_set(): return 
        
        target = self.action_key_var.get().strip().lower()
        if not target or target not in KEYS_LIST:
            self.root.after(0, lambda: self.status_label.config(text="ERREUR : Cible invalide !", fg="#c0392b"))
            return

        self.stop_event.clear()
        
        # VERROUILLAGE DE L'UI : Empêche toute interférence utilisateur pendant l'exécution
        self.root.after(0, lambda: self.set_ui_state("disabled"))
        self.root.after(0, lambda: self.status_label.config(text="🔥 ACTION EN COURS...", fg="#e74c3c"))
        
        mods = [m for m, var in zip(["ctrl", "alt", "shift"], [self.mod_ctrl_var, self.mod_alt_var, self.mod_shift_var]) if var.get()]
        
        # Lancement sécurisé via les Safe Getters (Anti Spinbox-vide Crash)
        threading.Thread(
            target=self.hold_process, 
            args=(
                target, mods, 
                self.mode_var.get(), 
                self.safe_int_get(self.duration_var, 5), 
                self.safe_int_get(self.spam_times_var, 1), 
                self.safe_int_get(self.spam_delay_var, 50)
            ), 
            daemon=True
        ).start()

    def stop_holding(self):
        self.stop_event.set()

    def hold_process(self, target, mods, mode, duration, spam_times, spam_delay):
        is_mouse = target in ["clic_gauche", "clic_droit", "clic_milieu"]
        mouse_map = {"clic_gauche": "left", "clic_droit": "right", "clic_milieu": "middle"}

        def safe_ui_update():
            try:
                self.status_label.config(text=f"ARRÊTÉ / PRÊT ({self.current_start_hotkey.upper()})", fg="#2980b9")
                self.set_ui_state("normal") # DÉVERROUILLAGE DE L'UI
            except tk.TclError:
                pass 

        # ANTI CTRL+A (Laisse 300ms à l'humain pour lever ses doigts des touches de lancement)
        time.sleep(0.3)
        
        start_time = time.time()
        
        try:
            for m in mods: keyboard.press(m)

            if mode in ["hold_continu", "hold_duree"]:
                if is_mouse:
                    mouse.press(button=mouse_map[target])
                    if mode == "hold_duree": self.stop_event.wait(duration)
                    else: self.stop_event.wait()
                else:
                    while not self.stop_event.is_set():
                        if mode == "hold_duree" and (time.time() - start_time >= duration):
                            break
                        keyboard.press(target)
                        self.stop_event.wait(0.03)

            elif mode == "spam":
                delay_sec = spam_delay / 1000.0 
                while not self.stop_event.is_set():
                    for _ in range(spam_times):
                        if self.stop_event.is_set(): break
                        if is_mouse: mouse.click(button=mouse_map[target])
                        else: keyboard.send(target) 
                        time.sleep(0.01) 
                    self.stop_event.wait(delay_sec) 

        finally:
            if is_mouse:
                try: mouse.release(button=mouse_map[target])
                except: pass
            else:
                try: keyboard.release(target)
                except: pass
                
            for m in mods: 
                try: keyboard.release(m)
                except: pass

            self.root.after(0, safe_ui_update)
            self.stop_event.set()

    # -----------------------------------------------------
    # SÉCURITÉS & SAUVEGARDE
    # -----------------------------------------------------
    def force_release_all(self):
        try:
            for k in ["ctrl", "alt", "shift"]: keyboard.release(k)
            target = self.action_key_var.get().strip().lower()
            if target in ["clic_gauche", "clic_droit", "clic_milieu"]:
                mouse_map = {"clic_gauche": "left", "clic_droit": "right", "clic_milieu": "middle"}
                mouse.release(button=mouse_map[target])
            elif target in KEYS_LIST:
                keyboard.release(target)
        except:
            pass

    def on_close(self):
        self.stop_holding()
        time.sleep(0.1) 
        self.force_release_all() 
        
        self.database["current"] = self.get_current_ui_state()
        self.save_database_to_file()
        self.root.destroy()

    def save_database_to_file(self):
        self.db_manager.save(self.database)

    def apply_loaded_config(self, config_dict=None):
        if config_dict is None:
            self.update_presets_listbox()
            preset = self.database.get("current", {})
        else:
            preset = config_dict

        if preset:
            self.start_mod_var.set(preset.get("start_mod", "ctrl"))
            self.start_key_var.set(preset.get("start_key", "f1"))
            self.stop_mod_var.set(preset.get("stop_mod", "ctrl"))
            self.stop_key_var.set(preset.get("stop_key", "f2"))
            self.action_key_var.set(preset.get("action_key", "space"))
            self.mod_ctrl_var.set(preset.get("mod_ctrl", False))
            self.mod_alt_var.set(preset.get("mod_alt", False))
            self.mod_shift_var.set(preset.get("mod_shift", False))
            
            old_mode = preset.get("mode", "hold_continu")
            if old_mode in ["continu", "hold_continu"]: self.mode_var.set("hold_continu")
            elif old_mode in ["duree", "hold_duree"]: self.mode_var.set("hold_duree")
            else: self.mode_var.set("spam")
                
            # SÉCURITÉ : Setters sécurisés anti-corruption JSON
            self.safe_int_set(self.duration_var, preset.get("duration", 5), 5)
            self.safe_int_set(self.spam_times_var, preset.get("spam_times", 1), 1)
            self.safe_int_set(self.spam_delay_var, preset.get("spam_delay", 50), 50)

    def get_current_ui_state(self):
        return {
            "start_mod": self.start_mod_var.get(), "start_key": self.start_key_var.get(),
            "stop_mod": self.stop_mod_var.get(), "stop_key": self.stop_key_var.get(),
            "action_key": self.action_key_var.get(), "mod_ctrl": self.mod_ctrl_var.get(),
            "mod_alt": self.mod_alt_var.get(), "mod_shift": self.mod_shift_var.get(),
            "mode": self.mode_var.get(), 
            "duration": self.safe_int_get(self.duration_var, 5),
            "spam_times": self.safe_int_get(self.spam_times_var, 1), 
            "spam_delay": self.safe_int_get(self.spam_delay_var, 50)
        }

    def save_preset(self):
        name = self.preset_name_var.get().strip()
        if not name: return
        self.database.setdefault("presets", {}) 
        self.database["presets"][name] = self.get_current_ui_state()
        self.save_database_to_file()
        self.update_presets_listbox()
        self.preset_name_var.set("") 

    def delete_preset(self):
        selection = self.presets_listbox.curselection()
        if not selection: return
        name = self.presets_listbox.get(selection[0])
        self.database.setdefault("presets", {})
        if name in self.database["presets"]:
            del self.database["presets"][name]
            self.save_database_to_file()
            self.update_presets_listbox()

    def on_preset_selected(self, event):
        selection = self.presets_listbox.curselection()
        if not selection: return
        self.database.setdefault("presets", {})
        preset = self.database["presets"].get(self.presets_listbox.get(selection[0]), {})
        if preset:
            self.apply_loaded_config(preset)
            self.apply_hotkeys_live()

    def update_presets_listbox(self):
        self.presets_listbox.delete(0, tk.END)
        self.database.setdefault("presets", {})
        for name in sorted(self.database["presets"].keys()):
            self.presets_listbox.insert(tk.END, name)