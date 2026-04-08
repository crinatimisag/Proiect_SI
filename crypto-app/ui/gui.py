import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime

from models.algoritm import Algoritm
from models.cheie import Cheie
from models.fisier import Fisier
from models.framework_model import FrameworkModel
from models.operatie import Operatie
from models.performanta import Performanta

from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.cheie_repository import CheieRepository
from database.repositories.fisier_repository import FisierRepository
from database.repositories.framework_repository import FrameworkRepository
from database.repositories.operatie_repository import OperatieRepository
from database.repositories.performanta_repository import PerformantaRepository

class CryptoAppUI(tk.Tk):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.db_manager = app_context['db_manager']
        
        self.alg_repo = AlgoritmRepository(self.db_manager)
        self.cheie_repo = CheieRepository(self.db_manager)
        self.fisier_repo = FisierRepository(self.db_manager)
        self.framework_repo = FrameworkRepository(self.db_manager)
        self.operatie_repo = OperatieRepository(self.db_manager)
        self.perf_repo = PerformantaRepository(self.db_manager)

        self.title('Crypto App Professional')
        self.geometry('1100x700')
        self.bg_main = '#f0f0f0'
        self.configure(bg=self.bg_main)
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self.style.configure('TFrame', background=self.bg_main)
        self.style.configure('TLabel', background=self.bg_main, font=('Segoe UI', 10))
        self.style.configure('TLabelframe', background=self.bg_main)
        self.style.configure('TLabelframe.Label', background=self.bg_main, font=('Segoe UI', 10, 'bold'))
        self.style.configure('TNotebook', background=self.bg_main)
        self.style.configure('TNotebook.Tab', background='#e1e1e1')
        
        self.style.configure('Action.TButton', font=('Segoe UI', 10), padding=(10, 5))
        
        self.create_tabs()

    def create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab-uri cu prima literă mare
        self.tab_names = ["Rapid", "Algoritmi", "Chei", "Fisiere", "Frameworks", "Operatii", "Performanta"]
        self.frames = {}
        for name in self.tab_names:
            self.frames[name] = ttk.Frame(self.notebook)
            self.notebook.add(self.frames[name], text=name)

        self.create_rapid_tab(self.frames["Rapid"])
        self.setup_generic_tab(self.frames["Algoritmi"], "Algoritm", ["Nume", "Tip"], self.alg_repo, self.refresh_alg)
        self.setup_generic_tab(self.frames["Chei"], "Cheie", ["Algoritm", "Nume", "Tip", "Dim", "Locatie", "Status"], self.cheie_repo, self.refresh_cheie)
        self.setup_generic_tab(self.frames["Fisiere"], "Fisier", ["Nume", "Cale", "Hash", "Dimensiune", "Status"], self.fisier_repo, self.refresh_fisier)
        self.setup_generic_tab(self.frames["Frameworks"], "Framework", ["Nume", "Versiune", "Limbaj"], self.framework_repo, self.refresh_framework)
        self.setup_generic_tab(self.frames["Operatii"], "Operatie", ["FisID", "KeyID", "AlgID", "Tip", "Status"], self.operatie_repo, self.refresh_operatie, readonly_insert=True)
        self.setup_generic_tab(self.frames["Performanta"], "Performanta", ["OpID", "Timp(ms)", "Mem(KB)", "Input"], self.perf_repo, self.refresh_perf, readonly_insert=True)

        self.refresh_all()

    def create_rapid_tab(self, parent):
        outer_frame = ttk.Frame(parent)
        outer_frame.place(relx=0.5, rely=0.4, anchor='center')

        ttk.Label(outer_frame, text='Crypto App', font=('Segoe UI', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        selection_frame = ttk.LabelFrame(outer_frame, text=" ", padding=20)
        selection_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')

        ttk.Label(selection_frame, text='Algoritm:').grid(row=0, column=0, sticky='e', padx=10, pady=10)
        self.combo_alg_rapid = ttk.Combobox(selection_frame, width=45, state="readonly")
        self.combo_alg_rapid.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(selection_frame, text='Cheie:').grid(row=1, column=0, sticky='e', padx=10, pady=10)
        self.combo_key_rapid = ttk.Combobox(selection_frame, width=45, state="readonly")
        self.combo_key_rapid.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(selection_frame, text='Fișier:').grid(row=2, column=0, sticky='e', padx=10, pady=10)
        self.combo_fisier_rapid = ttk.Combobox(selection_frame, width=45, state="readonly")
        self.combo_fisier_rapid.grid(row=2, column=1, padx=10, pady=10)

        btn_container = ttk.Frame(outer_frame)
        btn_container.grid(row=2, column=0, columnspan=2, pady=30)
        
        ttk.Button(btn_container, text='🔒 Criptează', command=self.encrypt_file, width=20, style='Action.TButton').pack(side='left', padx=15)
        ttk.Button(btn_container, text='🔓 Decriptează', command=self.decrypt_file, width=20, style='Action.TButton').pack(side='left', padx=15)

    def setup_generic_tab(self, parent, entity_name, fields, repo, refresh_callback, readonly_insert=False):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side='left', fill='both', expand=True)
        
        cols = ('ID',) + tuple(fields)
        tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        tree.pack(side='left', fill='both', expand=True)
        
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        sb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=sb.set)

        right_container = ttk.Frame(main_frame, width=300)
        right_container.pack(side='right', fill='y', padx=(15, 0))
        
        form_wrapper = ttk.Frame(right_container)
        form_wrapper.place(relx=0.5, rely=0.3, anchor='n')

        # Titlu Labelframe cu prima literă mare
        lbl_frame = ttk.LabelFrame(form_wrapper, text=f" Detalii {entity_name.lower()} ", padding=15)
        lbl_frame.pack(fill='x')

        vars_dict = {}
        for i, field in enumerate(fields):
            ttk.Label(lbl_frame, text=f"{field}:").grid(row=i, column=0, sticky='e', pady=5, padx=5)
            
            if entity_name == "Cheie" and field == "Algoritm":
                v = tk.StringVar()
                cb = ttk.Combobox(lbl_frame, textvariable=v, state="readonly", width=22)
                cb.grid(row=i, column=1, pady=5, padx=5)
                vars_dict[field] = v
                self.cheie_alg_combo = cb
            else:
                v = tk.StringVar()
                ttk.Entry(lbl_frame, textvariable=v, width=25).grid(row=i, column=1, pady=5, padx=5)
                vars_dict[field] = v

        btn_frame = ttk.Frame(form_wrapper)
        btn_frame.pack(fill='x', pady=20)

        def get_sid():
            item = tree.selection()
            return tree.item(item)['values'][0] if item else None

        if not readonly_insert:
            ttk.Button(btn_frame, text="➕ Adaugă", style='Action.TButton', 
                       command=lambda: self.handle_crud(entity_name, vars_dict, repo, "add")).pack(fill='x', pady=3)

        ttk.Button(btn_frame, text="📝 Update", style='Action.TButton',
                   command=lambda: self.handle_crud(entity_name, vars_dict, repo, "upd", get_sid())).pack(fill='x', pady=3)
        ttk.Button(btn_frame, text="🗑️ Șterge", style='Action.TButton',
                   command=lambda: self.handle_crud(entity_name, vars_dict, repo, "del", get_sid())).pack(fill='x', pady=3)
        
        tree.bind('<<TreeviewSelect>>', lambda e: self.populate_form(tree, vars_dict, entity_name))
        setattr(self, f"tree_{entity_name.lower()}", tree)

    def handle_crud(self, entity, vars_dict, repo, action, sid=None):
        vals = [v.get() for v in vars_dict.values()]
        try:
            if action == "del":
                if sid and messagebox.askyesno("Confirmare", "Ștergeți înregistrarea?"): 
                    repo.delete(sid)
            else:
                if entity == "Cheie":
                    alg_id = int(vals[0].split(":")[0])
                    obj = Cheie(sid, alg_id, vals[1], vals[2], int(vals[3]), vals[4], str(datetime.now()), vals[5])
                elif entity == "Algoritm": obj = Algoritm(sid, *vals)
                elif entity == "Fisier": obj = Fisier(sid, vals[0], vals[1], vals[2], int(vals[3]), str(datetime.now()), vals[4])
                elif entity == "Framework": obj = FrameworkModel(sid, vals[0], vals[1], vals[2])
                
                if action == "add": repo.insert(obj)
                else: repo.update(obj)
            self.refresh_all()
        except Exception as e: messagebox.showerror("Eroare", str(e))

    def populate_form(self, tree, vars_dict, entity_name):
        item = tree.selection()
        if not item: return
        vals = tree.item(item)['values'][1:]
        for (field, var), val in zip(vars_dict.items(), vals):
            if entity_name == "Cheie" and field == "Algoritm":
                for choice in self.cheie_alg_combo['values']:
                    if choice.startswith(f"{val}:"):
                        var.set(choice)
                        break
            else: var.set(val)

    def encrypt_file(self): messagebox.showinfo("Info", "Criptare finalizată.")
    def decrypt_file(self): messagebox.showinfo("Info", "Decriptare finalizată.")

    def refresh_alg(self, t):
        t.delete(*t.get_children())
        algs = self.alg_repo.get_all()
        choices = [f"{a.id_algoritm}: {a.nume}" for a in algs]
        for a in algs: t.insert('', 'end', values=(a.id_algoritm, a.nume, a.tip))
        self.combo_alg_rapid['values'] = choices
        if hasattr(self, 'cheie_alg_combo'): self.cheie_alg_combo['values'] = choices

    def refresh_cheie(self, t):
        t.delete(*t.get_children())
        keys = self.cheie_repo.get_all()
        for c in keys: t.insert('', 'end', values=(c.id_cheie, c.id_algoritm, c.nume_cheie, c.tip_cheie, c.dimensiune_cheie, c.locatie_cheie, c.status))
        self.combo_key_rapid['values'] = [f"{c.id_cheie}: {c.nume_cheie}" for c in keys]

    def refresh_fisier(self, t):
        t.delete(*t.get_children())
        fisiere = self.fisier_repo.get_all()
        for f in fisiere: t.insert('', 'end', values=(f.id_fisier, f.nume_fisier, f.cale_fisier, f.hash_initial, f.dimensiune, f.status))
        self.combo_fisier_rapid['values'] = [f"{f.id_fisier}: {f.nume_fisier}" for f in fisiere]

    def refresh_framework(self, t):
        t.delete(*t.get_children())
        for f in self.framework_repo.get_all(): t.insert('', 'end', values=(f.id_framework, f.nume, f.versiune, f.limbaj_programare))

    def refresh_operatie(self, t):
        t.delete(*t.get_children())
        for o in self.operatie_repo.get_all(): t.insert('', 'end', values=(o.id_operatie, o.id_fisier, o.id_cheie, o.id_algoritm, o.tip_operatie, o.status))

    def refresh_perf(self, t):
        t.delete(*t.get_children())
        for p in self.perf_repo.get_all(): t.insert('', 'end', values=(p.id_performanta, p.id_operatie, p.timp_executie_ms, p.memorie_kb, p.dimensiune_input))

    def refresh_all(self):
        self.refresh_alg(self.tree_algoritm)
        self.refresh_cheie(self.tree_cheie)
        self.refresh_fisier(self.tree_fisier)
        self.refresh_framework(self.tree_framework)
        self.refresh_operatie(self.tree_operatie)
        self.refresh_perf(self.tree_performanta)