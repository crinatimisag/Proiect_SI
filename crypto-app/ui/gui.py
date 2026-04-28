import hashlib
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.cheie_repository import CheieRepository
from database.repositories.fisier_repository import FisierRepository
from database.repositories.framework_repository import FrameworkRepository
from database.repositories.operatie_repository import OperatieRepository
from database.repositories.performanta_repository import PerformantaRepository
from models.algoritm import Algoritm
from models.fisier import Fisier
from models.framework_model import FrameworkModel
from services.crypto_service import CryptoService, CryptoServiceError
from services.cryptography_framework import CryptographyFrameworkError


class CryptoAppUI(tk.Tk):
    """Interfață grafică pentru managementul local al cheilor și fișierelor criptate."""

    OPENSSL_COMPATIBLE_ALGORITHMS = {"AES-128-CBC", "AES-256-CBC", "RSA"}
    CRYPTOGRAPHY_PREFERRED_ALGORITHM = "AES-256-GCM"
    OPENSSL_PREFERRED_ALGORITHM = "AES-256-CBC"

    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.db_manager = app_context["db_manager"]

        self.alg_repo = AlgoritmRepository(self.db_manager)
        self.cheie_repo = CheieRepository(self.db_manager)
        self.fisier_repo = FisierRepository(self.db_manager)
        self.framework_repo = FrameworkRepository(self.db_manager)
        self.operatie_repo = OperatieRepository(self.db_manager)
        self.perf_repo = PerformantaRepository(self.db_manager)
        self.crypto_service = CryptoService(self.db_manager)

        self._all_algorithms = []
        self._all_keys = []
        self._all_files = []

        self.title("Crypto Key Manager - AES / RSA / OpenSSL")
        self.geometry("1320x780")
        self.minsize(1120, 680)
        self.bg_main = "#f4f6f8"
        self.configure(bg=self.bg_main)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=self.bg_main)
        self.style.configure("TLabel", background=self.bg_main, font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background=self.bg_main)
        self.style.configure("TLabelframe.Label", background=self.bg_main, font=("Segoe UI", 10, "bold"))
        self.style.configure("TNotebook", background=self.bg_main)
        self.style.configure("TNotebook.Tab", background="#e8edf3", padding=(14, 7))
        self.style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        self.style.configure("Action.TButton", font=("Segoe UI", 10), padding=(10, 5))
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        self.create_tabs()

    def create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_names = ["Rapid", "Algoritmi", "Chei", "Fisiere", "Frameworks", "Operatii", "Performanta"]
        self.frames = {}
        for name in self.tab_names:
            self.frames[name] = ttk.Frame(self.notebook)
            self.notebook.add(self.frames[name], text=name)

        self.create_rapid_tab(self.frames["Rapid"])
        self.setup_generic_tab(self.frames["Algoritmi"], "Algoritm", ["Nume", "Tip"], self.alg_repo, self.refresh_alg)
        self.setup_generic_tab(
            self.frames["Chei"],
            "Cheie",
            ["Algoritm", "Nume", "Tip", "Dim", "Locatie", "Valoare(hex)", "Status"],
            self.cheie_repo,
            self.refresh_cheie,
        )
        self.setup_generic_tab(
            self.frames["Fisiere"],
            "Fisier",
            ["Nume", "Cale", "Hash", "Dimensiune", "Status"],
            self.fisier_repo,
            self.refresh_fisier,
        )
        self.setup_generic_tab(
            self.frames["Frameworks"],
            "Framework",
            ["Nume", "Versiune", "Limbaj"],
            self.framework_repo,
            self.refresh_framework,
        )
        self.setup_generic_tab(
            self.frames["Operatii"],
            "Operatie",
            ["FisID", "KeyID", "AlgID", "FrameworkID", "Tip", "Status", "Rezultat"],
            self.operatie_repo,
            self.refresh_operatie,
            readonly_insert=True,
        )
        self.setup_generic_tab(
            self.frames["Performanta"],
            "Performanta",
            ["OpID", "Timp(ms)", "Mem(KB)", "Input", "Observatii"],
            self.perf_repo,
            self.refresh_perf,
            readonly_insert=True,
        )

        self.refresh_all()
        self._add_chart_button()

    def create_rapid_tab(self, parent):
        outer_frame = ttk.Frame(parent)
        outer_frame.pack(fill="both", expand=True, padx=30, pady=30)

        ttk.Label(
            outer_frame,
            text="Management local pentru chei, fișiere criptate și performanțe",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            outer_frame,
            text=(
                "Selectează întâi framework-ul. Lista de algoritmi este filtrată automat: "
                "OpenSSL folosește AES-CBC sau RSA hibrid, iar cryptography poate folosi AES-GCM, AES-CBC sau RSA."
            ),
            wraplength=1080,
        ).pack(anchor="w", pady=(0, 16))

        selection_frame = ttk.LabelFrame(outer_frame, text="Operații rapide", padding=20)
        selection_frame.pack(fill="x")
        selection_frame.columnconfigure(1, weight=1)

        ttk.Label(selection_frame, text="Framework:").grid(row=0, column=0, sticky="e", padx=10, pady=9)
        self.combo_frame_rapid = ttk.Combobox(selection_frame, width=72, state="readonly")
        self.combo_frame_rapid.grid(row=0, column=1, padx=10, pady=9, sticky="ew")
        self.combo_frame_rapid.bind("<<ComboboxSelected>>", lambda _event: self.on_framework_changed())

        ttk.Label(selection_frame, text="Algoritm:").grid(row=1, column=0, sticky="e", padx=10, pady=9)
        self.combo_alg_rapid = ttk.Combobox(selection_frame, width=72, state="readonly")
        self.combo_alg_rapid.grid(row=1, column=1, padx=10, pady=9, sticky="ew")
        self.combo_alg_rapid.bind("<<ComboboxSelected>>", lambda _event: self.on_algorithm_changed())

        ttk.Label(selection_frame, text="Cheie:").grid(row=2, column=0, sticky="e", padx=10, pady=9)
        self.combo_key_rapid = ttk.Combobox(selection_frame, width=72, state="readonly")
        self.combo_key_rapid.grid(row=2, column=1, padx=10, pady=9, sticky="ew")

        ttk.Label(selection_frame, text="Fișier:").grid(row=3, column=0, sticky="e", padx=10, pady=9)
        self.combo_fisier_rapid = ttk.Combobox(selection_frame, width=72, state="readonly")
        self.combo_fisier_rapid.grid(row=3, column=1, padx=10, pady=9, sticky="ew")

        tools_frame = ttk.Frame(selection_frame)
        tools_frame.grid(row=0, column=2, rowspan=4, padx=(25, 0), pady=2, sticky="n")
        ttk.Button(tools_frame, text="Generează cheie", command=self.generate_key_rapid, style="Action.TButton", width=24).pack(fill="x", pady=4)
        ttk.Button(tools_frame, text="Importă fișier", command=self.import_file_rapid, style="Action.TButton", width=24).pack(fill="x", pady=4)
        ttk.Button(tools_frame, text="Refresh liste", command=self.refresh_all, style="Action.TButton", width=24).pack(fill="x", pady=4)

        self.compat_info = tk.StringVar(value="")
        ttk.Label(selection_frame, textvariable=self.compat_info, wraplength=980, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 0)
        )

        btn_container = ttk.Frame(outer_frame)
        btn_container.pack(anchor="w", pady=24)
        ttk.Button(btn_container, text="🔒 Criptează fișier", command=self.encrypt_file, width=22, style="Action.TButton").pack(side="left", padx=(0, 12))
        ttk.Button(btn_container, text="🔓 Decriptează fișier", command=self.decrypt_file, width=22, style="Action.TButton").pack(side="left", padx=12)

        details_frame = ttk.LabelFrame(outer_frame, text="Status", padding=15)
        details_frame.pack(fill="both", expand=True)
        self.quick_info = tk.StringVar(value="Sistem pregătit. Importă un fișier, generează o cheie și rulează criptarea.")
        ttk.Label(details_frame, textvariable=self.quick_info, wraplength=1120, justify="left").pack(anchor="w")

    def setup_generic_tab(self, parent, entity_name, fields, repo, refresh_callback, readonly_insert=False):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side="left", fill="both", expand=True)

        cols = ("ID",) + tuple(fields)
        tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=self._column_width(col), anchor="center", stretch=True)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        right_container = ttk.Frame(main_frame, width=340)
        right_container.pack(side="right", fill="y", padx=(15, 0))
        right_container.pack_propagate(False)

        lbl_frame = ttk.LabelFrame(right_container, text=f"Detalii {entity_name.lower()}", padding=15)
        lbl_frame.pack(fill="x", anchor="n")

        vars_dict = {}
        for i, field in enumerate(fields):
            ttk.Label(lbl_frame, text=f"{field}:").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            v = tk.StringVar()
            entry = ttk.Entry(lbl_frame, textvariable=v, width=30)
            entry.grid(row=i, column=1, pady=5, padx=5)
            vars_dict[field] = v

        btn_frame = ttk.Frame(right_container)
        btn_frame.pack(fill="x", pady=18)

        def get_sid():
            item = tree.selection()
            return tree.item(item)["values"][0] if item else None

        manual_crud_entities = {"Algoritm", "Framework"}
        generated_entities = {"Cheie", "Fisier"}
        readonly_entities = {"Operatie", "Performanta"}

        if entity_name in manual_crud_entities:
            ttk.Button(btn_frame, text="➕ Adaugă", style="Action.TButton", command=lambda: self.handle_crud(entity_name, vars_dict, repo, "add")).pack(fill="x", pady=3)
            ttk.Button(
                btn_frame,
                text="📝 Update",
                style="Action.TButton",
                command=lambda en=entity_name, vd=vars_dict, r=repo: self.handle_crud(en, vd, r, "upd", get_sid()),
            ).pack(fill="x", pady=3)
            ttk.Button(
                btn_frame,
                text="🗑️ Șterge",
                style="Action.TButton",
                command=lambda en=entity_name, vd=vars_dict, r=repo: self.handle_crud(en, vd, r, "del", get_sid()),
            ).pack(fill="x", pady=3)
        elif entity_name == "Cheie":
            ttk.Label(
                btn_frame,
                text="Cheile se generează automat din tab-ul Rapid, ca să aibă dimensiunea corectă pentru algoritm.",
                wraplength=300,
                justify="left",
            ).pack(fill="x", pady=(0, 8))
            ttk.Button(btn_frame, text="🔑 Generează din Rapid", style="Action.TButton", command=lambda: self.notebook.select(self.frames["Rapid"])).pack(fill="x", pady=3)
            ttk.Button(
                btn_frame,
                text="🗑️ Șterge cheia selectată",
                style="Action.TButton",
                command=lambda en=entity_name, vd=vars_dict, r=repo: self.handle_crud(en, vd, r, "del", get_sid()),
            ).pack(fill="x", pady=3)
        elif entity_name == "Fisier":
            ttk.Label(
                btn_frame,
                text="Fișierele se importă prin aplicație pentru a calcula corect hash-ul, dimensiunea și statusul.",
                wraplength=300,
                justify="left",
            ).pack(fill="x", pady=(0, 8))
            ttk.Button(btn_frame, text="📁 Importă fișier", style="Action.TButton", command=self.import_file_rapid).pack(fill="x", pady=3)
            ttk.Button(
                btn_frame,
                text="🗑️ Șterge fișierul selectat din DB",
                style="Action.TButton",
                command=lambda en=entity_name, vd=vars_dict, r=repo: self.handle_crud(en, vd, r, "del", get_sid()),
            ).pack(fill="x", pady=3)
        elif entity_name in readonly_entities or readonly_insert:
            ttk.Label(
                btn_frame,
                text="Acest tabel este completat automat după operațiile de criptare/decriptare.",
                wraplength=300,
                justify="left",
            ).pack(fill="x", pady=(0, 8))

        tree.bind("<<TreeviewSelect>>", lambda _e: self.populate_form(tree, vars_dict, entity_name))
        setattr(self, f"tree_{entity_name.lower()}", tree)

    def handle_crud(self, entity, vars_dict, repo, action, sid=None):
        vals = [v.get() for v in vars_dict.values()]
        try:
            if action == "del":
                if not sid:
                    messagebox.showwarning("Selecție lipsă", "Selectează mai întâi o înregistrare.")
                    return
                if messagebox.askyesno("Confirmare", "Ștergeți înregistrarea selectată din baza de date?"):
                    repo.delete(sid)
            else:
                if entity == "Algoritm":
                    obj = Algoritm(sid, vals[0].strip(), vals[1].strip())
                elif entity == "Fisier":
                    obj = Fisier(sid, vals[0], vals[1], vals[2], int(vals[3]), str(datetime.now()), vals[4])
                elif entity == "Framework":
                    obj = FrameworkModel(sid, vals[0].strip(), vals[1].strip(), vals[2].strip())
                else:
                    raise ValueError("Operația manuală nu este permisă pentru această tabelă.")

                if action == "add":
                    repo.insert(obj)
                else:
                    if not sid:
                        messagebox.showwarning("Selecție lipsă", "Selectează mai întâi o înregistrare.")
                        return
                    repo.update(obj)
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    def populate_form(self, tree, vars_dict, entity_name):
        item = tree.selection()
        if not item:
            return
        vals = tree.item(item)["values"][1:]
        for (_field, var), val in zip(vars_dict.items(), vals):
            var.set(val)

    def encrypt_file(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
            key_id = self._get_selected_id(self.combo_key_rapid, "cheie")
            file_id = self._get_selected_id(self.combo_fisier_rapid, "fișier")
            framework_id = self._get_selected_id(self.combo_frame_rapid, "framework")

            fisier = self.fisier_repo.get_by_id(file_id)
            if fisier and fisier.status == "criptat":
                messagebox.showwarning("Fișier nepotrivit", "Pentru criptare selectează un fișier importat sau decriptat, nu unul deja criptat.")
                return

            self._validate_selected_framework_algorithm()
            result = self.crypto_service.encrypt_file(file_id, key_id, algorithm_id, framework_id)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_fisier_rapid, result["output_file"].id_fisier)
            self.quick_info.set(f"Criptare reușită. Fișier: {result['output_file'].cale_fisier} | Timp: {result['elapsed_ms']:.2f} ms")
            messagebox.showinfo("Succes", self.quick_info.get())
        except (CryptoServiceError, CryptographyFrameworkError, ValueError) as exc:
            messagebox.showerror("Eroare la criptare", str(exc))

    def decrypt_file(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
            key_id = self._get_selected_id(self.combo_key_rapid, "cheie")
            file_id = self._get_selected_id(self.combo_fisier_rapid, "fișier")
            framework_id = self._get_selected_id(self.combo_frame_rapid, "framework")

            fisier = self.fisier_repo.get_by_id(file_id)
            if fisier and fisier.status != "criptat":
                messagebox.showwarning("Fișier nepotrivit", "Pentru decriptare selectează un fișier cu status 'criptat'.")
                return

            self._validate_selected_framework_algorithm()
            result = self.crypto_service.decrypt_file(file_id, key_id, algorithm_id, framework_id)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_fisier_rapid, result["output_file"].id_fisier)
            self.quick_info.set(f"Decriptare reușită. Fișier restabilit: {result['output_file'].cale_fisier} | Timp: {result['elapsed_ms']:.2f} ms")
            messagebox.showinfo("Succes", self.quick_info.get())
        except (CryptoServiceError, CryptographyFrameworkError, ValueError) as exc:
            messagebox.showerror("Eroare la decriptare", str(exc))

    def import_file_rapid(self):
        source_path = filedialog.askopenfilename(title="Selectează fișier")
        if not source_path:
            return
        try:
            fisier = self.crypto_service.register_file(source_path)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_fisier_rapid, fisier.id_fisier)
            self.quick_info.set(f"Fișier importat: {fisier.cale_fisier}")
            self.notebook.select(self.frames["Rapid"])
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))

    def generate_key_rapid(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
            framework_id = self._get_selected_id(self.combo_frame_rapid, "framework")
            self._validate_selected_framework_algorithm()
        except ValueError as exc:
            messagebox.showwarning("Selecție incompletă", str(exc))
            return

        key_name = simpledialog.askstring("Nume cheie", "Identificator cheie (poate rămâne gol pentru nume automat):")
        if key_name is None:
            return
        try:
            cheie = self.crypto_service.make_key(algorithm_id, key_name, framework_id)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_key_rapid, cheie.id_cheie)
            self.quick_info.set(f"Cheie generată: {cheie.nume_cheie} ({cheie.dimensiune_cheie} biți, {cheie.tip_cheie})")
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))

    def refresh_alg(self, tree):
        tree.delete(*tree.get_children())
        self._all_algorithms = self.alg_repo.get_all()
        for a in self._all_algorithms:
            tree.insert("", "end", values=(a.id_algoritm, a.nume, a.tip))
        self.update_rapid_algorithm_choices()

    def refresh_cheie(self, tree):
        tree.delete(*tree.get_children())
        self._all_keys = self.cheie_repo.get_all()
        for k in self._all_keys:
            tree.insert(
                "",
                "end",
                values=(
                    k.id_cheie,
                    k.id_algoritm,
                    k.nume_cheie,
                    k.tip_cheie,
                    k.dimensiune_cheie,
                    k.locatie_cheie,
                    self._mask_key_hex(k.valoare_cheie_hex),
                    k.status,
                ),
            )
        self.update_rapid_keys_for_selected_algorithm()

    def refresh_fisier(self, tree):
        tree.delete(*tree.get_children())
        self._all_files = self.fisier_repo.get_all()
        for f in self._all_files:
            tree.insert("", "end", values=(f.id_fisier, f.nume_fisier, f.cale_fisier, f.hash_initial, f.dimensiune, f.status))
        self.combo_fisier_rapid["values"] = [self._format_file_choice(f) for f in self._all_files]
        if self._all_files and not self.combo_fisier_rapid.get():
            self.combo_fisier_rapid.set(self._format_file_choice(self._all_files[0]))

    def refresh_framework(self, tree):
        tree.delete(*tree.get_children())
        frames = self.framework_repo.get_all()
        choices = [f"{fr.id_framework}: {fr.nume}" for fr in frames]
        for fr in frames:
            tree.insert("", "end", values=(fr.id_framework, fr.nume, fr.versiune, fr.limbaj_programare))
        self.combo_frame_rapid["values"] = choices
        if choices and not self.combo_frame_rapid.get():
            preferred = next((choice for choice in choices if "cryptography" in choice.lower()), choices[0])
            self.combo_frame_rapid.set(preferred)
        self.update_rapid_algorithm_choices()

    def refresh_operatie(self, tree):
        tree.delete(*tree.get_children())
        for o in self.operatie_repo.get_all():
            tree.insert(
                "",
                "end",
                values=(
                    o.id_operatie,
                    o.id_fisier,
                    o.id_cheie,
                    o.id_algoritm,
                    o.id_framework,
                    o.tip_operatie,
                    o.status,
                    o.fisier_rezultat,
                ),
            )

    def refresh_perf(self, tree):
        tree.delete(*tree.get_children())
        for p in self.perf_repo.get_all():
            tree.insert(
                "",
                "end",
                values=(
                    p.id_performanta,
                    p.id_operatie,
                    f"{p.timp_executie_ms:.2f}",
                    f"{p.memorie_kb:.2f}",
                    p.dimensiune_input,
                    p.observatii or "",
                ),
            )

    def refresh_all(self):
        self.refresh_framework(self.tree_framework)
        self.refresh_alg(self.tree_algoritm)
        self.refresh_cheie(self.tree_cheie)
        self.refresh_fisier(self.tree_fisier)
        self.refresh_operatie(self.tree_operatie)
        self.refresh_perf(self.tree_performanta)
        self.update_compatibility_note()

    def on_framework_changed(self):
        self.update_rapid_algorithm_choices()
        self.update_rapid_keys_for_selected_algorithm()
        self.update_compatibility_note()

    def on_algorithm_changed(self):
        self.update_rapid_keys_for_selected_algorithm()
        self.update_compatibility_note()

    def update_rapid_algorithm_choices(self):
        if not hasattr(self, "combo_alg_rapid"):
            return
        current_id = self._extract_selected_id(self.combo_alg_rapid.get())
        compatible = [a for a in self._all_algorithms if self._algorithm_supported_by_selected_framework(a.nume)]
        choices = [self._format_algorithm_choice(a) for a in compatible]
        self.combo_alg_rapid["values"] = choices

        if not choices:
            self.combo_alg_rapid.set("")
            return

        if current_id and any(choice.startswith(f"{current_id}:") for choice in choices):
            return

        preferred_name = self.OPENSSL_PREFERRED_ALGORITHM if self._is_openssl_selected() else self.CRYPTOGRAPHY_PREFERRED_ALGORITHM
        preferred = next((a for a in compatible if a.nume == preferred_name), compatible[0])
        self.combo_alg_rapid.set(self._format_algorithm_choice(preferred))

    def update_rapid_keys_for_selected_algorithm(self):
        if not hasattr(self, "combo_key_rapid"):
            return
        selected_algorithm_id = self._extract_selected_id(self.combo_alg_rapid.get())

        key_choices = []
        for key in getattr(self, "_all_keys", []):
            if selected_algorithm_id is None or key.id_algoritm == selected_algorithm_id:
                key_choices.append(self._format_key_choice(key))
        self.combo_key_rapid["values"] = key_choices

        if key_choices:
            current_id = self._extract_selected_id(self.combo_key_rapid.get())
            if current_id is None or all(not choice.startswith(f"{current_id}:") for choice in key_choices):
                self.combo_key_rapid.set(key_choices[0])
        else:
            self.combo_key_rapid.set("")

    def update_compatibility_note(self):
        if not hasattr(self, "compat_info"):
            return
        if self._is_openssl_selected():
            self.compat_info.set(
                "OpenSSL selectat: sunt disponibile AES-128-CBC, AES-256-CBC și RSA hibrid. "
                "AES-GCM este ascuns deoarece OpenSSL CLI nu este folosit aici pentru GCM."
            )
        else:
            self.compat_info.set(
                "cryptography selectat: poți folosi AES-GCM, AES-CBC sau RSA hibrid. "
                "Pentru comparația cerută în proiect, rulează aceeași operație și cu OpenSSL."
            )

    def _validate_selected_framework_algorithm(self):
        algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
        alg = next((a for a in self._all_algorithms if a.id_algoritm == algorithm_id), None)
        if not alg:
            raise ValueError("Algoritmul selectat nu există în baza de date.")
        if not self._algorithm_supported_by_selected_framework(alg.nume):
            raise ValueError(f"Algoritmul {alg.nume} nu este compatibil cu framework-ul selectat.")

    def _is_openssl_selected(self) -> bool:
        return "openssl" in self.combo_frame_rapid.get().lower() if hasattr(self, "combo_frame_rapid") else False

    def _algorithm_supported_by_selected_framework(self, algorithm_name: str) -> bool:
        if self._is_openssl_selected():
            return algorithm_name.upper() in self.OPENSSL_COMPATIBLE_ALGORITHMS
        return True

    @staticmethod
    def _extract_selected_id(value: str) -> int | None:
        if not value:
            return None
        try:
            return int(value.split(":", 1)[0])
        except (TypeError, ValueError):
            return None

    def _get_selected_id(self, combobox: ttk.Combobox, label: str) -> int:
        value = combobox.get().strip()
        if not value:
            raise ValueError(f"Selectează mai întâi un {label}.")
        try:
            return int(value.split(":", 1)[0])
        except ValueError as exc:
            raise ValueError(f"Selecția pentru {label} este invalidă.") from exc

    def _set_combobox_to_id(self, combobox: ttk.Combobox, item_id: int | None):
        if item_id is None:
            return
        for choice in combobox["values"]:
            if choice.startswith(f"{item_id}:"):
                combobox.set(choice)
                return

    @staticmethod
    def _format_algorithm_choice(alg) -> str:
        return f"{alg.id_algoritm}: {alg.nume} ({alg.tip})"

    @staticmethod
    def _format_key_choice(key) -> str:
        return f"{key.id_cheie}: {key.nume_cheie} ({key.dimensiune_cheie} biți, {key.status})"

    @staticmethod
    def _format_file_choice(file_obj) -> str:
        return f"{file_obj.id_fisier}: {file_obj.nume_fisier} [{file_obj.status}, {file_obj.dimensiune} B]"

    @staticmethod
    def _mask_key_hex(value: str) -> str:
        if not value:
            return ""
        if len(value) <= 32:
            return value
        return f"{value[:16]}...{value[-16:]}"

    @staticmethod
    def _column_width(col: str) -> int:
        widths = {
            "ID": 60,
            "Nume": 170,
            "Cale": 260,
            "Hash": 250,
            "Valoare(hex)": 260,
            "Observatii": 260,
            "Rezultat": 280,
            "Versiune": 220,
            "Dimensiune": 100,
            "FrameworkID": 100,
        }
        return widths.get(col, 120)

    @staticmethod
    def _normalize_hex(value: str) -> str:
        normalized = "".join(value.strip().split()).upper()
        if len(normalized) % 2 != 0:
            raise ValueError("Valoarea hex trebuie să aibă un număr par de caractere.")
        bytes.fromhex(normalized)
        return normalized

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _add_chart_button(self):
        btn_frame = ttk.Frame(self.frames["Performanta"])
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))
        ttk.Button(
            btn_frame,
            text="📊 Afișează grafic comparativ",
            style="Action.TButton",
            command=self.show_performance_chart,
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame,
            text="💾 Export CSV",
            style="Action.TButton",
            command=self.export_perf_csv,
        ).pack(side="left", padx=5)

    def show_performance_chart(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from collections import defaultdict

        perfs = self.perf_repo.get_all()
        if not perfs:
            messagebox.showinfo("Info", "Nu există date de performanță.")
            return

        groups_timp = defaultdict(list)
        groups_mem = defaultdict(list)
        for p in perfs:
            label = p.observatii or f"Op#{p.id_operatie}"
            groups_timp[label].append(p.timp_executie_ms)
            groups_mem[label].append(p.memorie_kb)

        labels = list(groups_timp.keys())
        avg_timp = [sum(v) / len(v) for v in groups_timp.values()]
        avg_mem = [sum(v) / len(v) for v in groups_mem.values()]

        win = tk.Toplevel(self)
        win.title("Analiză Performanță")
        win.geometry("960x560")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.2))
        fig.patch.set_facecolor(self.bg_main)
        x = range(len(labels))

        bars1 = ax1.bar(x, avg_timp)
        ax1.set_title("Timp mediu execuție (ms)", fontsize=12, fontweight="bold")
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        ax1.set_ylabel("ms")
        for bar, val in zip(bars1, avg_timp):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}", ha="center", va="bottom", fontsize=8)

        bars2 = ax2.bar(x, avg_mem)
        ax2.set_title("Memorie medie utilizată (KB)", fontsize=12, fontweight="bold")
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        ax2.set_ylabel("KB")
        for bar, val in zip(bars2, avg_mem):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}", ha="center", va="bottom", fontsize=8)

        fig.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_perf_csv(self):
        import csv

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Salvează CSV",
        )
        if not path:
            return
        perfs = self.perf_repo.get_all()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "OperatieID", "Timp(ms)", "Memorie(KB)", "DimensiuneInput", "Observatii"])
            for p in perfs:
                writer.writerow([
                    p.id_performanta,
                    p.id_operatie,
                    f"{p.timp_executie_ms:.2f}",
                    f"{p.memorie_kb:.2f}",
                    p.dimensiune_input,
                    p.observatii or "",
                ])
        messagebox.showinfo("Export", f"Date exportate în:\n{path}")
