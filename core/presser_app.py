import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import mouse
import threading
import time
from core.database import DatabaseManager

# --- LISTE DES TOUCHES MISE À JOUR ---
KEYS_LIST = [
    "clic_gauche", "clic_droit", "clic_milieu",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", # Chiffres rangée du haut
    "&", "é", "\"", "'", "(", "-", "è", "_", "ç", "à",
    "numpad 0", "numpad 1", "numpad 2", "numpad 3", "numpad 4", # Pavé numérique (Droite)
    "numpad 5", "numpad 6", "numpad 7", "numpad 8", "numpad 9", # Pavé numérique (Droite)
    "numpad .", "numpad +", "numpad -", "numpad *", "numpad /", # Opérateurs Pavé numérique
    "backspace", "down", "enter", "esc", "left", "right", "space", "tab", "up",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
]
MODIFIERS_LIST = ["", "ctrl", "alt", "shift"]

class AutoPresserUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Keyboard & Mouse Holder Pro")
        self.root.geometry("780x690") 
        self.root.resizable(False, False)

        self.search_buffers = {}
        self.search_times = {}

        self.stop_event = threading.Event()
        self.stop_event.set()
        self.current_start_hotkey = None
        self.current_stop_hotkey = None
        
        self.sequence_list = []

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
        try: return int_var.get()
        except tk.TclError: return default

    def safe_int_set(self, int_var, value, default=0):
        try: int_var.set(int(value))
        except (ValueError, TypeError, tk.TclError): int_var.set(default)
        
    def safe_float_get(self, float_var, default=0.0):
        try: return float_var.get()
        except tk.TclError: return default

    def safe_float_set(self, float_var, value, default=0.0):
        try: float_var.set(float(value))
        except (ValueError, TypeError, tk.TclError): float_var.set(default)

    def set_ui_state(self, state):
        widgets = [
            self.preset_entry, self.btn_save, self.btn_delete, self.presets_listbox,
            self.cb_start_mod, self.cb_start_key, self.cb_stop_mod, self.cb_stop_key,
            self.rb_mode_simple, self.rb_mode_sequence,
            self.cb_action_key, self.chk_ctrl, self.chk_alt, self.chk_shift,
            self.rb_continu, self.rb_duree, self.rb_spam, self.sb_duration, self.sb_spam_times, self.sb_spam_delay,
            self.cb_seq_key, self.sb_seq_delay, self.btn_add_seq_key, self.btn_add_seq_delay,
            self.btn_seq_del, self.btn_seq_clear, self.seq_listbox,
            self.rb_seq_infini, self.rb_seq_duree, self.rb_seq_boucles, self.sb_seq_duration, self.sb_seq_loops
        ]
        for w in widgets:
            try:
                if state == "normal" and isinstance(w, ttk.Combobox): w.config(state="readonly")
                else: w.config(state=state)
            except tk.TclError: pass

    # -----------------------------------------------------
    # CRÉATION DE L'INTERFACE
    # -----------------------------------------------------
    def create_widgets(self):
        self.left_frame = tk.Frame(self.root, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(self.root, padx=10, pady=10, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="y")

        tk.Label(self.right_frame, text="💾 PRESETS", font=("Segoe UI", 11, "bold"), bg="#f0f0f0").pack(anchor="w", pady=(5, 5))
        tk.Label(self.right_frame, text="Nom du preset :", bg="#f0f0f0", font=("Segoe UI", 9)).pack(anchor="w")
        self.preset_name_var = tk.StringVar()
        self.preset_entry = ttk.Entry(self.right_frame, textvariable=self.preset_name_var, width=22)
        self.preset_entry.pack(anchor="w", pady=2)
        
        self.btn_save = ttk.Button(self.right_frame, text="Sauvegarder", command=self.save_preset)
        self.btn_save.pack(anchor="w", fill="x", pady=(0, 15))

        tk.Label(self.right_frame, text="Vos Presets :", bg="#f0f0f0", font=("Segoe UI", 9, "italic")).pack(anchor="w")
        self.presets_listbox = tk.Listbox(self.right_frame, width=22, height=22, font=("Segoe UI", 10))
        self.presets_listbox.pack(anchor="w", fill="both", expand=True)
        self.presets_listbox.bind("<<ListboxSelect>>", self.on_preset_selected)
        
        self.btn_delete = ttk.Button(self.right_frame, text="❌ Supprimer", command=self.delete_preset)
        self.btn_delete.pack(anchor="w", fill="x", pady=(5, 0))

        frame_hotkeys = tk.LabelFrame(self.left_frame, text=" 1. Raccourcis globaux ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        frame_hotkeys.pack(fill="x", pady=5)

        tk.Label(frame_hotkeys, text="Commencer :").grid(row=0, column=0, sticky="w")
        self.start_mod_var, self.start_key_var = tk.StringVar(value="ctrl"), tk.StringVar(value="f1")
        self.cb_start_mod = ttk.Combobox(frame_hotkeys, textvariable=self.start_mod_var, values=MODIFIERS_LIST, width=7, state="readonly")
        self.cb_start_mod.grid(row=0, column=1, padx=5)
        tk.Label(frame_hotkeys, text="+").grid(row=0, column=2)
        self.cb_start_key = ttk.Combobox(frame_hotkeys, textvariable=self.start_key_var, values=KEYS_LIST, width=12, state="readonly")
        self.cb_start_key.grid(row=0, column=3, padx=5)

        tk.Label(frame_hotkeys, text="Finir :").grid(row=1, column=0, sticky="w", pady=10)
        self.stop_mod_var, self.stop_key_var = tk.StringVar(value="ctrl"), tk.StringVar(value="f2")
        self.cb_stop_mod = ttk.Combobox(frame_hotkeys, textvariable=self.stop_mod_var, values=MODIFIERS_LIST, width=7, state="readonly")
        self.cb_stop_mod.grid(row=1, column=1, padx=5)
        tk.Label(frame_hotkeys, text="+").grid(row=1, column=2)
        self.cb_stop_key = ttk.Combobox(frame_hotkeys, textvariable=self.stop_key_var, values=KEYS_LIST, width=12, state="readonly")
        self.cb_stop_key.grid(row=1, column=3, padx=5)

        for cb in [self.cb_start_key, self.cb_stop_key]:
            cb.bind("<Key>", lambda e, c=cb: self.smart_search_combobox(e, c))

        frame_action_main = tk.LabelFrame(self.left_frame, text=" 2. Action(s) à simuler ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        frame_action_main.pack(fill="x", pady=5)
        
        frame_toggle = tk.Frame(frame_action_main)
        frame_toggle.pack(fill="x", pady=(0, 10))
        self.action_mode_var = tk.StringVar(value="simple")
        self.rb_mode_simple = ttk.Radiobutton(frame_toggle, text="Mode Simple (1 Touche)", variable=self.action_mode_var, value="simple", command=self.toggle_mode)
        self.rb_mode_simple.pack(side="left", padx=(0, 15))
        self.rb_mode_sequence = ttk.Radiobutton(frame_toggle, text="Mode Séquence (Macro Boucle)", variable=self.action_mode_var, value="sequence", command=self.toggle_mode)
        self.rb_mode_sequence.pack(side="left")

        # --- MODE SIMPLE ---
        self.frame_simple = tk.Frame(frame_action_main)
        tk.Label(self.frame_simple, text="Cible :", width=12, anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        self.action_key_var = tk.StringVar(value="space")
        self.cb_action_key = ttk.Combobox(self.frame_simple, textvariable=self.action_key_var, values=KEYS_LIST, width=15, state="readonly")
        self.cb_action_key.grid(row=0, column=1, padx=5, sticky="w", pady=5)
        self.cb_action_key.bind("<Key>", lambda e, c=self.cb_action_key: self.smart_search_combobox(e, c))

        tk.Label(self.frame_simple, text="Modificateurs :", width=12, anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self.mod_ctrl_var, self.mod_alt_var, self.mod_shift_var = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        frame_mods = tk.Frame(self.frame_simple)
        frame_mods.grid(row=1, column=1, sticky="w", pady=5)
        self.chk_ctrl = ttk.Checkbutton(frame_mods, text="Ctrl", variable=self.mod_ctrl_var)
        self.chk_alt = ttk.Checkbutton(frame_mods, text="Alt", variable=self.mod_alt_var)
        self.chk_shift = ttk.Checkbutton(frame_mods, text="Shift", variable=self.mod_shift_var)
        self.chk_ctrl.pack(side="left", padx=2)
        self.chk_alt.pack(side="left", padx=2)
        self.chk_shift.pack(side="left", padx=2)

        # --- MODE SEQUENCE ---
        self.frame_sequence = tk.Frame(frame_action_main)
        
        frame_add_key = tk.Frame(self.frame_sequence)
        frame_add_key.pack(fill="x", pady=2)
        tk.Label(frame_add_key, text="Touche/Souris :", width=12, anchor="w").pack(side="left")
        self.seq_key_var = tk.StringVar(value="clic_gauche")
        self.cb_seq_key = ttk.Combobox(frame_add_key, textvariable=self.seq_key_var, values=KEYS_LIST, width=15, state="readonly")
        self.cb_seq_key.pack(side="left", padx=5)
        self.cb_seq_key.bind("<Key>", lambda e, c=self.cb_seq_key: self.smart_search_combobox(e, c))
        self.btn_add_seq_key = ttk.Button(frame_add_key, text="➕ Ajouter Touche", command=self.add_seq_action)
        self.btn_add_seq_key.pack(side="left")

        frame_add_delay = tk.Frame(self.frame_sequence)
        frame_add_delay.pack(fill="x", pady=(2, 10))
        tk.Label(frame_add_delay, text="Délai (sec) :", width=12, anchor="w").pack(side="left")
        self.seq_delay_var = tk.DoubleVar(value=1.0)
        self.sb_seq_delay = ttk.Spinbox(frame_add_delay, from_=0.1, to=3600.0, increment=0.1, textvariable=self.seq_delay_var, width=15)
        self.sb_seq_delay.pack(side="left", padx=5)
        self.btn_add_seq_delay = ttk.Button(frame_add_delay, text="⏳ Ajouter Délai", command=self.add_seq_delay)
        self.btn_add_seq_delay.pack(side="left")

        self.seq_listbox = tk.Listbox(self.frame_sequence, height=6, font=("Segoe UI", 9))
        self.seq_listbox.pack(fill="x", pady=2)
        
        frame_seq_ctrl = tk.Frame(self.frame_sequence)
        frame_seq_ctrl.pack(fill="x")
        self.btn_seq_del = ttk.Button(frame_seq_ctrl, text="❌ Supprimer sélection", command=self.remove_seq_item)
        self.btn_seq_del.pack(side="left", expand=True, fill="x", padx=(0, 2))
        self.btn_seq_clear = ttk.Button(frame_seq_ctrl, text="🗑️ Vider la liste", command=self.clear_seq)
        self.btn_seq_clear.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ---------------- 3. GESTION ----------------
        self.frame_gestion_main = tk.LabelFrame(self.left_frame, text=" 3. Gestion ", font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        self.frame_gestion_main.pack(fill="x", pady=5)
        
        # GESTION SIMPLE
        self.frame_gestion_simple = tk.Frame(self.frame_gestion_main)
        self.mode_var = tk.StringVar(value="hold_continu")
        
        self.rb_continu = ttk.Radiobutton(self.frame_gestion_simple, text="En continu (Presse tout le temps)", variable=self.mode_var, value="hold_continu")
        self.rb_continu.grid(row=0, column=0, sticky="w", columnspan=5, pady=5)
        
        self.rb_duree = ttk.Radiobutton(self.frame_gestion_simple, text="Relâcher après :", variable=self.mode_var, value="hold_duree")
        self.rb_duree.grid(row=1, column=0, sticky="w", pady=5)
        self.duration_var = tk.IntVar(value=5)
        self.sb_duration = ttk.Spinbox(self.frame_gestion_simple, from_=1, to=3600, textvariable=self.duration_var, width=5)
        self.sb_duration.grid(row=1, column=1, sticky="w", padx=2)
        tk.Label(self.frame_gestion_simple, text="secondes").grid(row=1, column=2, sticky="w", columnspan=3)

        self.rb_spam = ttk.Radiobutton(self.frame_gestion_simple, text="Spam :", variable=self.mode_var, value="spam")
        self.rb_spam.grid(row=2, column=0, sticky="w", pady=5)
        self.spam_times_var = tk.IntVar(value=1)
        self.sb_spam_times = ttk.Spinbox(self.frame_gestion_simple, from_=1, to=999, textvariable=self.spam_times_var, width=4)
        self.sb_spam_times.grid(row=2, column=1, sticky="w", padx=2)
        tk.Label(self.frame_gestion_simple, text="fois par").grid(row=2, column=2, sticky="w", padx=2)
        self.spam_delay_var = tk.IntVar(value=50)
        self.sb_spam_delay = ttk.Spinbox(self.frame_gestion_simple, from_=1, to=10000, textvariable=self.spam_delay_var, width=5)
        self.sb_spam_delay.grid(row=2, column=3, sticky="w", padx=2)
        tk.Label(self.frame_gestion_simple, text="ms").grid(row=2, column=4, sticky="w")

        # GESTION SÉQUENCE (MACRO)
        self.frame_gestion_sequence = tk.Frame(self.frame_gestion_main)
        self.seq_mode_var = tk.StringVar(value="seq_infini")
        
        self.rb_seq_infini = ttk.Radiobutton(self.frame_gestion_sequence, text="Boucler à l'infini (jusqu'à Stop)", variable=self.seq_mode_var, value="seq_infini")
        self.rb_seq_infini.grid(row=0, column=0, sticky="w", columnspan=3, pady=5)
        
        self.rb_seq_duree = ttk.Radiobutton(self.frame_gestion_sequence, text="Arrêter la boucle après :", variable=self.seq_mode_var, value="seq_duree")
        self.rb_seq_duree.grid(row=1, column=0, sticky="w", pady=5)
        self.seq_duration_var = tk.IntVar(value=60)
        self.sb_seq_duration = ttk.Spinbox(self.frame_gestion_sequence, from_=1, to=36000, textvariable=self.seq_duration_var, width=5)
        self.sb_seq_duration.grid(row=1, column=1, sticky="w", padx=2)
        tk.Label(self.frame_gestion_sequence, text="secondes au total").grid(row=1, column=2, sticky="w")

        self.rb_seq_boucles = ttk.Radiobutton(self.frame_gestion_sequence, text="Faire exactement :", variable=self.seq_mode_var, value="seq_boucles")
        self.rb_seq_boucles.grid(row=2, column=0, sticky="w", pady=5)
        self.seq_loops_var = tk.IntVar(value=10)
        self.sb_seq_loops = ttk.Spinbox(self.frame_gestion_sequence, from_=1, to=9999, textvariable=self.seq_loops_var, width=5)
        self.sb_seq_loops.grid(row=2, column=1, sticky="w", padx=2)
        tk.Label(self.frame_gestion_sequence, text="boucle(s)").grid(row=2, column=2, sticky="w")

        self.toggle_mode()

        self.status_label = tk.Label(self.left_frame, text="Statut : PRÊT", font=("Segoe UI", 13, "bold"), fg="#2980b9")
        self.status_label.pack(pady=10)

    # -----------------------------------------------------
    # LOGIQUE D'AFFICHAGE ET MACRO
    # -----------------------------------------------------
    def toggle_mode(self):
        if self.action_mode_var.get() == "simple":
            self.frame_sequence.pack_forget()
            self.frame_gestion_sequence.pack_forget()
            self.frame_simple.pack(fill="x")
            self.frame_gestion_simple.pack(fill="x")
        else:
            self.frame_simple.pack_forget()
            self.frame_gestion_simple.pack_forget()
            self.frame_sequence.pack(fill="x")
            self.frame_gestion_sequence.pack(fill="x")

    def add_seq_action(self):
        val = self.seq_key_var.get().strip().lower()
        if val in KEYS_LIST:
            self.sequence_list.append({"type": "action", "val": val})
            self.refresh_seq_listbox()

    def add_seq_delay(self):
        val = self.safe_float_get(self.seq_delay_var, 1.0)
        self.sequence_list.append({"type": "delay", "val": val})
        self.refresh_seq_listbox()

    def remove_seq_item(self):
        selection = self.seq_listbox.curselection()
        if selection:
            del self.sequence_list[selection[0]]
            self.refresh_seq_listbox()

    def clear_seq(self):
        self.sequence_list.clear()
        self.refresh_seq_listbox()

    def refresh_seq_listbox(self):
        self.seq_listbox.delete(0, tk.END)
        for i, item in enumerate(self.sequence_list):
            if item["type"] == "action":
                icon = "🖱️" if item["val"] in ["clic_gauche", "clic_droit", "clic_milieu"] else "⌨️"
                self.seq_listbox.insert(tk.END, f"{i+1}. {icon} Action : {item['val']}")
            else:
                self.seq_listbox.insert(tk.END, f"{i+1}. ⏳ Délai : {item['val']} sec")

    # -----------------------------------------------------
    # SMART SEARCH CORRIGÉ POUR LES ESPACES
    # -----------------------------------------------------
    def smart_search_combobox(self, event, combobox):
        cb_id = id(combobox)
        now = time.time()
        if cb_id not in self.search_times or (now - self.search_times[cb_id] > 0.8):
            self.search_buffers[cb_id] = ""
            
        self.search_times[cb_id] = now
        char = event.char.lower()
        
        # On autorise les espaces " " pour pouvoir taper "numpad 1" etc.
        if not char.isalnum() and char not in ["_", " "]: return
        
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
    # MOTEUR D'EXÉCUTION
    # -----------------------------------------------------
    def start_holding(self):
        if not self.stop_event.is_set(): return 
        
        action_mode = self.action_mode_var.get()
        
        if action_mode == "simple":
            target = self.action_key_var.get().strip().lower()
            if not target or target not in KEYS_LIST:
                self.root.after(0, lambda: self.status_label.config(text="ERREUR : Cible simple invalide !", fg="#c0392b"))
                return
        else:
            if not self.sequence_list:
                self.root.after(0, lambda: self.status_label.config(text="ERREUR : La séquence est vide !", fg="#c0392b"))
                return

        self.stop_event.clear()
        
        self.root.after(0, lambda: self.set_ui_state("disabled"))
        self.root.after(0, lambda: self.status_label.config(text="🔥 BOT EN COURS D'EXÉCUTION...", fg="#e74c3c"))
        
        mods = [m for m, var in zip(["ctrl", "alt", "shift"], [self.mod_ctrl_var, self.mod_alt_var, self.mod_shift_var]) if var.get()]
        
        args_dict = {
            "action_mode": action_mode,
            "target": self.action_key_var.get().strip().lower(),
            "mods": mods,
            "mode": self.mode_var.get(),
            "duration": self.safe_int_get(self.duration_var, 5),
            "spam_times": self.safe_int_get(self.spam_times_var, 1),
            "spam_delay": self.safe_int_get(self.spam_delay_var, 50),
            
            "sequence": list(self.sequence_list), 
            "seq_mode": self.seq_mode_var.get(),
            "seq_duration": self.safe_int_get(self.seq_duration_var, 60),
            "seq_loops": self.safe_int_get(self.seq_loops_var, 10)
        }

        threading.Thread(target=self.hold_process, args=(args_dict,), daemon=True).start()

    def stop_holding(self):
        self.stop_event.set()

    def hold_process(self, params):
        action_mode = params["action_mode"]
        mouse_map = {"clic_gauche": "left", "clic_droit": "right", "clic_milieu": "middle"}

        def safe_ui_update():
            try:
                self.status_label.config(text=f"ARRÊTÉ / PRÊT ({self.current_start_hotkey.upper()})", fg="#2980b9")
                self.set_ui_state("normal")
            except tk.TclError: pass 

        time.sleep(0.3) 
        start_time = time.time()
        
        try:
            if action_mode == "simple":
                target = params["target"]
                mods = params["mods"]
                mode = params["mode"]
                is_mouse = target in mouse_map

                for m in mods: keyboard.press(m)

                if mode in ["hold_continu", "hold_duree"]:
                    if is_mouse:
                        mouse.press(button=mouse_map[target])
                        if mode == "hold_duree": self.stop_event.wait(params["duration"])
                        else: self.stop_event.wait()
                    else:
                        while not self.stop_event.is_set():
                            if mode == "hold_duree" and (time.time() - start_time >= params["duration"]):
                                break
                            keyboard.press(target)
                            self.stop_event.wait(0.03)

                elif mode == "spam":
                    delay_sec = params["spam_delay"] / 1000.0 
                    while not self.stop_event.is_set():
                        for _ in range(params["spam_times"]):
                            if self.stop_event.is_set(): break
                            if is_mouse: mouse.click(button=mouse_map[target])
                            else: keyboard.send(target) 
                            time.sleep(0.01) 
                        self.stop_event.wait(delay_sec) 
                        
            else:
                sequence = params["sequence"]
                seq_mode = params["seq_mode"]
                loop_counter = 0
                
                while not self.stop_event.is_set():
                    if seq_mode == "seq_duree" and (time.time() - start_time >= params["seq_duration"]):
                        break
                    if seq_mode == "seq_boucles" and loop_counter >= params["seq_loops"]:
                        break
                        
                    for step in sequence:
                        if self.stop_event.is_set(): break 
                        
                        if step["type"] == "action":
                            val = step["val"]
                            try:  # <-- AJOUTE CECI
                                if val in mouse_map:
                                    mouse.click(button=mouse_map[val])
                                else:
                                    keyboard.send(val)
                            except Exception: # <-- ET CECI
                                pass
                            if val in mouse_map:
                                mouse.click(button=mouse_map[val])
                            else:
                                keyboard.send(val)
                        elif step["type"] == "delay":
                            self.stop_event.wait(step["val"])
                            
                    loop_counter += 1

        finally:
            if action_mode == "simple":
                target = params["target"]
                is_mouse = target in mouse_map
                if is_mouse:
                    try: mouse.release(button=mouse_map[target])
                    except: pass
                else:
                    try: keyboard.release(target)
                    except: pass
                for m in params["mods"]: 
                    try: keyboard.release(m)
                    except: pass

            self.root.after(0, safe_ui_update)
            self.stop_event.set()

    # -----------------------------------------------------
    # SÉCURITÉS & SAUVEGARDE JSON
    # -----------------------------------------------------
    def force_release_all(self):
        try:
            for k in ["ctrl", "alt", "shift"]: keyboard.release(k)
            for k in KEYS_LIST:
                if "clic" not in k: keyboard.release(k)
            mouse.release(button="left")
            mouse.release(button="right")
            mouse.release(button="middle")
        except: pass

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
            
            self.action_mode_var.set(preset.get("action_mode", "simple"))
            self.toggle_mode()
            
            self.action_key_var.set(preset.get("action_key", "space"))
            self.mod_ctrl_var.set(preset.get("mod_ctrl", False))
            self.mod_alt_var.set(preset.get("mod_alt", False))
            self.mod_shift_var.set(preset.get("mod_shift", False))
            self.mode_var.set(preset.get("mode", "hold_continu"))
            self.safe_int_set(self.duration_var, preset.get("duration", 5), 5)
            self.safe_int_set(self.spam_times_var, preset.get("spam_times", 1), 1)
            self.safe_int_set(self.spam_delay_var, preset.get("spam_delay", 50), 50)
            
            seq_list = preset.get("sequence_list", [])
            self.sequence_list = seq_list if isinstance(seq_list, list) else []
            self.refresh_seq_listbox()
            self.seq_mode_var.set(preset.get("seq_mode", "seq_infini"))
            self.safe_int_set(self.seq_duration_var, preset.get("seq_duration", 60), 60)
            self.safe_int_set(self.seq_loops_var, preset.get("seq_loops", 10), 10)

    def get_current_ui_state(self):
        return {
            "start_mod": self.start_mod_var.get(), "start_key": self.start_key_var.get(),
            "stop_mod": self.stop_mod_var.get(), "stop_key": self.stop_key_var.get(),
            
            "action_mode": self.action_mode_var.get(),
            
            "action_key": self.action_key_var.get(), "mod_ctrl": self.mod_ctrl_var.get(),
            "mod_alt": self.mod_alt_var.get(), "mod_shift": self.mod_shift_var.get(),
            "mode": self.mode_var.get(), 
            "duration": self.safe_int_get(self.duration_var, 5),
            "spam_times": self.safe_int_get(self.spam_times_var, 1), 
            "spam_delay": self.safe_int_get(self.spam_delay_var, 50),
            
            "sequence_list": list(self.sequence_list),
            "seq_mode": self.seq_mode_var.get(),
            "seq_duration": self.safe_int_get(self.seq_duration_var, 60),
            "seq_loops": self.safe_int_get(self.seq_loops_var, 10)
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