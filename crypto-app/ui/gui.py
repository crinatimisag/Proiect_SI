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
from models.cheie import Cheie
from models.fisier import Fisier
from models.framework_model import FrameworkModel
from services.crypto_service import CryptoService, CryptoServiceError
from services.cryptography_framework import CryptographyFrameworkError


class CryptoAppUI(tk.Tk):
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

        self.title("Crypto App - varianta 3 cu cryptography")
        self.geometry("1300x760")
        self.bg_main = "#f0f0f0"
        self.configure(bg=self.bg_main)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=self.bg_main)
        self.style.configure("TLabel", background=self.bg_main, font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background=self.bg_main)
        self.style.configure("TLabelframe.Label", background=self.bg_main, font=("Segoe UI", 10, "bold"))
        self.style.configure("TNotebook", background=self.bg_main)
        self.style.configure("TNotebook.Tab", background="#e1e1e1")
        self.style.configure("Action.TButton", font=("Segoe UI", 10), padding=(10, 5))

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
            self.frames["Frameworks"], "Framework", ["Nume", "Versiune", "Limbaj"], self.framework_repo, self.refresh_framework
        )
        self.setup_generic_tab(
            self.frames["Operatii"],
            "Operatie",
            ["FisID", "KeyID", "AlgID", "Tip", "Status"],
            self.operatie_repo,
            self.refresh_operatie,
            readonly_insert=True,
        )
        self.setup_generic_tab(
            self.frames["Performanta"],
            "Performanta",
            ["OpID", "Timp(ms)", "Mem(KB)", "Input"],
            self.perf_repo,
            self.refresh_perf,
            readonly_insert=True,
        )

        self.refresh_all()

    def create_rapid_tab(self, parent):
        outer_frame = ttk.Frame(parent)
        outer_frame.pack(fill="both", expand=True, padx=30, pady=30)

        ttk.Label(outer_frame, text="Crypto App cu biblioteca cryptography", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(
            outer_frame,
            text=(
                "Flux recomandat: pentru AES folosești AES-GCM cu cheie secretă, iar pentru RSA aplicația folosește "
                "o schemă hibridă RSA-OAEP + AES-GCM. Generează cheia în DB, importă fișierul și apoi folosește "
                "criptarea sau decriptarea."
            ),
            wraplength=1000,
        ).pack(anchor="w", pady=(0, 20))

        selection_frame = ttk.LabelFrame(outer_frame, text="Operații rapide", padding=20)
        selection_frame.pack(fill="x")

        ttk.Label(selection_frame, text="Algoritm:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.combo_alg_rapid = ttk.Combobox(selection_frame, width=60, state="readonly")
        self.combo_alg_rapid.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.combo_alg_rapid.bind("<<ComboboxSelected>>", lambda _event: self.update_rapid_keys_for_selected_algorithm())

        ttk.Label(selection_frame, text="Cheie:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.combo_key_rapid = ttk.Combobox(selection_frame, width=60, state="readonly")
        self.combo_key_rapid.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(selection_frame, text="Fișier:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.combo_fisier_rapid = ttk.Combobox(selection_frame, width=60, state="readonly")
        self.combo_fisier_rapid.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        tools_frame = ttk.Frame(selection_frame)
        tools_frame.grid(row=0, column=2, rowspan=3, padx=(25, 0), pady=5, sticky="n")
        ttk.Button(tools_frame, text="Generează cheie", command=self.generate_key_rapid, style="Action.TButton", width=22).pack(fill="x", pady=4)
        ttk.Button(tools_frame, text="Importă fișier", command=self.import_file_rapid, style="Action.TButton", width=22).pack(fill="x", pady=4)
        ttk.Button(tools_frame, text="Refresh liste", command=self.refresh_all, style="Action.TButton", width=22).pack(fill="x", pady=4)

        btn_container = ttk.Frame(outer_frame)
        btn_container.pack(anchor="w", pady=25)
        ttk.Button(btn_container, text="🔒 Criptează", command=self.encrypt_file, width=20, style="Action.TButton").pack(side="left", padx=10)
        ttk.Button(btn_container, text="🔓 Decriptează", command=self.decrypt_file, width=20, style="Action.TButton").pack(side="left", padx=10)

        details_frame = ttk.LabelFrame(outer_frame, text="Observații", padding=15)
        details_frame.pack(fill="both", expand=True)
        self.quick_info = tk.StringVar(
            value=(
                "Cheile generate rapid sunt salvate direct în tabela Cheie, în coloana valoare_cheie_hex. "
                "AES folosește clasa AESGCM, iar RSA folosește chei private PEM și criptare hibridă RSA-OAEP + AES-GCM."
            )
        )
        ttk.Label(details_frame, textvariable=self.quick_info, wraplength=1100, justify="left").pack(anchor="w")

    def setup_generic_tab(self, parent, entity_name, fields, repo, refresh_callback, readonly_insert=False):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side="left", fill="both", expand=True)

        cols = ("ID",) + tuple(fields)
        tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor="center")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        right_container = ttk.Frame(main_frame, width=330)
        right_container.pack(side="right", fill="y", padx=(15, 0))

        form_wrapper = ttk.Frame(right_container)
        form_wrapper.place(relx=0.5, rely=0.1, anchor="n")
        lbl_frame = ttk.LabelFrame(form_wrapper, text=f"Detalii {entity_name.lower()}", padding=15)
        lbl_frame.pack(fill="x")

        vars_dict = {}
        for i, field in enumerate(fields):
            ttk.Label(lbl_frame, text=f"{field}:").grid(row=i, column=0, sticky="e", pady=5, padx=5)

            if entity_name == "Cheie" and field == "Algoritm":
                v = tk.StringVar()
                cb = ttk.Combobox(lbl_frame, textvariable=v, state="readonly", width=24)
                cb.grid(row=i, column=1, pady=5, padx=5)
                vars_dict[field] = v
                self.cheie_alg_combo = cb
            else:
                v = tk.StringVar()
                ttk.Entry(lbl_frame, textvariable=v, width=28).grid(row=i, column=1, pady=5, padx=5)
                vars_dict[field] = v

        btn_frame = ttk.Frame(form_wrapper)
        btn_frame.pack(fill="x", pady=20)

        def get_sid():
            item = tree.selection()
            return tree.item(item)["values"][0] if item else None

        if not readonly_insert:
            ttk.Button(
                btn_frame,
                text="➕ Adaugă",
                style="Action.TButton",
                command=lambda: self.handle_crud(entity_name, vars_dict, repo, "add"),
            ).pack(fill="x", pady=3)

        ttk.Button(
            btn_frame,
            text="📝 Update",
            style="Action.TButton",
            command=lambda: self.handle_crud(entity_name, vars_dict, repo, "upd", get_sid()),
        ).pack(fill="x", pady=3)
        ttk.Button(
            btn_frame,
            text="🗑️ Șterge",
            style="Action.TButton",
            command=lambda: self.handle_crud(entity_name, vars_dict, repo, "del", get_sid()),
        ).pack(fill="x", pady=3)

        if entity_name == "Fisier":
            ttk.Button(
                btn_frame,
                text="📂 Importă fișier în DB",
                style="Action.TButton",
                command=self.import_file_rapid,
            ).pack(fill="x", pady=(12, 3))

        if entity_name == "Cheie":
            ttk.Button(
                btn_frame,
                text="🔑 Generează cheie pentru algoritmul selectat",
                style="Action.TButton",
                command=self.generate_key_rapid,
            ).pack(fill="x", pady=(12, 3))

        tree.bind("<<TreeviewSelect>>", lambda _e: self.populate_form(tree, vars_dict, entity_name))
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
                    algoritm = self.alg_repo.get_by_id(alg_id)
                    if not algoritm:
                        raise ValueError("Algoritmul selectat nu există.")
                    key_hex = self._normalize_hex(vals[5])
                    key_type, key_dimension = self.crypto_service.framework.describe_key_material(
                        algoritm.nume,
                        bytes.fromhex(key_hex),
                    )
                    dimensiune = int(vals[3]) if vals[3].strip() else key_dimension
                    if dimensiune != key_dimension:
                        raise ValueError(
                            f"Dimensiunea introdusă ({dimensiune}) nu corespunde materialului de cheie ({key_dimension})."
                        )
                    tip_cheie = vals[2].strip() or key_type
                    if tip_cheie.lower() != key_type.lower():
                        raise ValueError(f"Tipul cheii pentru {algoritm.nume} trebuie să fie '{key_type}'.")
                    obj = Cheie(
                        sid,
                        alg_id,
                        vals[1],
                        tip_cheie,
                        dimensiune,
                        vals[4] or "DB",
                        key_hex,
                        str(datetime.now()),
                        vals[6] or "activa",
                    )
                elif entity == "Algoritm":
                    obj = Algoritm(sid, *vals)
                elif entity == "Fisier":
                    file_path = Path(vals[1])
                    if file_path.exists():
                        hash_value = self._sha256_file(file_path)
                        dimensiune = file_path.stat().st_size
                    else:
                        hash_value = vals[2]
                        dimensiune = int(vals[3])
                    obj = Fisier(sid, vals[0], vals[1], hash_value, dimensiune, str(datetime.now()), vals[4])
                elif entity == "Framework":
                    obj = FrameworkModel(sid, vals[0], vals[1], vals[2])
                else:
                    raise ValueError("Această tabelă este read-only în UI.")

                if action == "add":
                    repo.insert(obj)
                else:
                    repo.update(obj)
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    def populate_form(self, tree, vars_dict, entity_name):
        item = tree.selection()
        if not item:
            return
        vals = tree.item(item)["values"][1:]
        for (field, var), val in zip(vars_dict.items(), vals):
            if entity_name == "Cheie" and field == "Algoritm":
                for choice in self.cheie_alg_combo["values"]:
                    if choice.startswith(f"{val}:"):
                        var.set(choice)
                        break
            else:
                var.set(val)

    def encrypt_file(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
            key_id = self._get_selected_id(self.combo_key_rapid, "cheie")
            file_id = self._get_selected_id(self.combo_fisier_rapid, "fișier")
            result = self.crypto_service.encrypt_file(file_id, key_id, algorithm_id)
            self.refresh_all()
            self.quick_info.set(
                f"Criptare reușită. Fișier rezultat: {result['output_file'].cale_fisier} | "
                f"Operație ID: {result['operation_id']} | Timp: {result['elapsed_ms']:.2f} ms"
            )
            messagebox.showinfo("Succes", self.quick_info.get())
        except (CryptoServiceError, CryptographyFrameworkError, ValueError) as exc:
            messagebox.showerror("Eroare la criptare", str(exc))

    def decrypt_file(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
            key_id = self._get_selected_id(self.combo_key_rapid, "cheie")
            file_id = self._get_selected_id(self.combo_fisier_rapid, "fișier")
            result = self.crypto_service.decrypt_file(file_id, key_id, algorithm_id)
            self.refresh_all()
            self.quick_info.set(
                f"Decriptare reușită. Fișier rezultat: {result['output_file'].cale_fisier} | "
                f"Operație ID: {result['operation_id']} | Timp: {result['elapsed_ms']:.2f} ms"
            )
            messagebox.showinfo("Succes", self.quick_info.get())
        except (CryptoServiceError, CryptographyFrameworkError, ValueError) as exc:
            messagebox.showerror("Eroare la decriptare", str(exc))

    def import_file_rapid(self):
        source_path = filedialog.askopenfilename(title="Selectează fișierul de importat")
        if not source_path:
            return
        try:
            fisier = self.crypto_service.register_file(source_path)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_fisier_rapid, fisier.id_fisier)
            self.quick_info.set(f"Fișier importat în sistem: {fisier.cale_fisier}")
        except (CryptoServiceError, CryptographyFrameworkError) as exc:
            messagebox.showerror("Eroare la import", str(exc))

    def generate_key_rapid(self):
        try:
            algorithm_id = self._get_selected_id(self.combo_alg_rapid, "algoritm")
        except ValueError as exc:
            messagebox.showwarning("Algoritm lipsă", str(exc))
            return

        key_name = simpledialog.askstring("Nume cheie", "Introdu un nume pentru cheie (sau lasă gol pentru generare automată):")
        try:
            cheie = self.crypto_service.generate_key_for_algorithm(algorithm_id, key_name)
            self.refresh_all()
            self._set_combobox_to_id(self.combo_key_rapid, cheie.id_cheie)
            self.quick_info.set(f"Cheia '{cheie.nume_cheie}' a fost generată și salvată în DB.")
        except (CryptoServiceError, CryptographyFrameworkError) as exc:
            messagebox.showerror("Eroare la generare cheie", str(exc))

    def refresh_alg(self, tree):
        tree.delete(*tree.get_children())
        algs = self.alg_repo.get_all()
        choices = [f"{a.id_algoritm}: {a.nume}" for a in algs]
        for algoritm in algs:
            tree.insert("", "end", values=(algoritm.id_algoritm, algoritm.nume, algoritm.tip))
        self.combo_alg_rapid["values"] = choices
        if hasattr(self, "cheie_alg_combo"):
            self.cheie_alg_combo["values"] = choices
        if choices and not self.combo_alg_rapid.get():
            self.combo_alg_rapid.set(choices[0])

    def refresh_cheie(self, tree):
        tree.delete(*tree.get_children())
        self._all_keys = self.cheie_repo.get_all()
        for cheie in self._all_keys:
            tree.insert(
                "",
                "end",
                values=(
                    cheie.id_cheie,
                    cheie.id_algoritm,
                    cheie.nume_cheie,
                    cheie.tip_cheie,
                    cheie.dimensiune_cheie,
                    cheie.locatie_cheie,
                    cheie.valoare_cheie_hex,
                    cheie.status,
                ),
            )
        self.update_rapid_keys_for_selected_algorithm()

    def refresh_fisier(self, tree):
        tree.delete(*tree.get_children())
        fisiere = self.fisier_repo.get_all()
        for fisier in fisiere:
            tree.insert(
                "",
                "end",
                values=(fisier.id_fisier, fisier.nume_fisier, fisier.cale_fisier, fisier.hash_initial, fisier.dimensiune, fisier.status),
            )
        self.combo_fisier_rapid["values"] = [f"{f.id_fisier}: {f.nume_fisier}" for f in fisiere]

    def refresh_framework(self, tree):
        tree.delete(*tree.get_children())
        for framework in self.framework_repo.get_all():
            tree.insert("", "end", values=(framework.id_framework, framework.nume, framework.versiune, framework.limbaj_programare))

    def refresh_operatie(self, tree):
        tree.delete(*tree.get_children())
        for operatie in self.operatie_repo.get_all():
            tree.insert(
                "",
                "end",
                values=(
                    operatie.id_operatie,
                    operatie.id_fisier,
                    operatie.id_cheie,
                    operatie.id_algoritm,
                    operatie.tip_operatie,
                    operatie.status,
                ),
            )

    def refresh_perf(self, tree):
        tree.delete(*tree.get_children())
        for perf in self.perf_repo.get_all():
            tree.insert(
                "",
                "end",
                values=(perf.id_performanta, perf.id_operatie, perf.timp_executie_ms, perf.memorie_kb, perf.dimensiune_input),
            )

    def refresh_all(self):
        self.refresh_alg(self.tree_algoritm)
        self.refresh_cheie(self.tree_cheie)
        self.refresh_fisier(self.tree_fisier)
        self.refresh_framework(self.tree_framework)
        self.refresh_operatie(self.tree_operatie)
        self.refresh_perf(self.tree_performanta)

    def update_rapid_keys_for_selected_algorithm(self):
        selected_algorithm_id = None
        selection = self.combo_alg_rapid.get()
        if selection:
            selected_algorithm_id = int(selection.split(":", 1)[0])

        key_choices = []
        for key in getattr(self, "_all_keys", []):
            if selected_algorithm_id is None or key.id_algoritm == selected_algorithm_id:
                key_choices.append(f"{key.id_cheie}: {key.nume_cheie}")
        self.combo_key_rapid["values"] = key_choices
        if key_choices:
            current_id = self._extract_selected_id(self.combo_key_rapid.get())
            if current_id is None or all(not choice.startswith(f"{current_id}:") for choice in key_choices):
                self.combo_key_rapid.set(key_choices[0])
        else:
            self.combo_key_rapid.set("")

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