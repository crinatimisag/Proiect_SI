
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk




class CryptoAppUI(tk.Tk):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.title('Crypto App')
        self.geometry('480x330')
        self.bg_color = '#ffffff'
        self.configure(bg=self.bg_color)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground='#222', font=('Segoe UI', 11))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=4)
        self.style.configure('TEntry', font=('Segoe UI', 10))
        self.create_tabs()

    def add_key(self):
        messagebox.showinfo('Info', 'Key added (placeholder)')

    def create_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        tab_rapid = ttk.Frame(notebook)
        notebook.add(tab_rapid, text='Rapid')
        self.create_rapid_tab(tab_rapid)

        tab_alg = ttk.Frame(notebook)
        notebook.add(tab_alg, text='Algoritm')
        self.create_algoritm_tab(tab_alg)

        tab_cheie = ttk.Frame(notebook)
        notebook.add(tab_cheie, text='Cheie')
        self.create_cheie_tab(tab_cheie)

        tab_fisier = ttk.Frame(notebook)
        notebook.add(tab_fisier, text='Fisier')
        self.create_fisier_tab(tab_fisier)

        tab_framework = ttk.Frame(notebook)
        notebook.add(tab_framework, text='Framework')
        self.create_framework_tab(tab_framework)

        tab_operatie = ttk.Frame(notebook)
        notebook.add(tab_operatie, text='Operatie')
        self.create_operatie_tab(tab_operatie)

        tab_perf = ttk.Frame(notebook)
        notebook.add(tab_perf, text='Performanta')
        self.create_performanta_tab(tab_perf)


    def create_rapid_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        ttk.Label(frame, text='Crypto App', font=('Segoe UI', 15, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 18))

        db_manager = self.app_context['db_manager']
        from database.repositories.algoritm_repository import AlgoritmRepository
        from database.repositories.cheie_repository import CheieRepository
        from database.repositories.fisier_repository import FisierRepository
        self.alg_repo = AlgoritmRepository(db_manager)
        self.cheie_repo = CheieRepository(db_manager)
        self.fisier_repo = FisierRepository(db_manager)

        self.algoritmi = self.alg_repo.get_all()
        self.chei = self.cheie_repo.get_all()
        self.fisiere = self.fisier_repo.get_all()

        self.alg_names = [a.nume for a in self.algoritmi]
        self.cheie_names = [c.nume_cheie for c in self.chei]
        self.fisier_names = [f.nume_fisier for f in self.fisiere]

        ttk.Label(frame, text='Algorithm:').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.alg_var = tk.StringVar()
        self.alg_menu = ttk.Combobox(frame, textvariable=self.alg_var, values=self.alg_names, width=18)
        self.alg_menu.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.alg_menu.bind('<KeyRelease>', lambda e: self._filter_dropdown(self.alg_menu, self.alg_names))

        ttk.Label(frame, text='Key:').grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.key_var = tk.StringVar()
        self.key_menu = ttk.Combobox(frame, textvariable=self.key_var, values=self.cheie_names, width=18)
        self.key_menu.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.key_menu.bind('<KeyRelease>', lambda e: self._filter_dropdown(self.key_menu, self.cheie_names))
        ttk.Button(frame, text='Add Key', command=self.add_key).grid(row=2, column=2, sticky='w', padx=5, pady=5)

        ttk.Label(frame, text='File:').grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.file_var = tk.StringVar()
        self.file_menu = ttk.Combobox(frame, textvariable=self.file_var, values=self.fisier_names, width=18)
        self.file_menu.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        self.file_menu.bind('<KeyRelease>', lambda e: self._filter_dropdown(self.file_menu, self.fisier_names))

        self.file_label = ttk.Label(frame, text='No file selected', foreground='#888')
        self.file_label.grid(row=4, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 10))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text='Encrypt', command=self.encrypt_file, width=12).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Decrypt', command=self.decrypt_file, width=12).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Analyze Performance', command=self.analyze_performance, width=18).pack(side='left', padx=6)

    def _filter_dropdown(self, combobox, full_list):
        value = combobox.get().lower()
        filtered = [item for item in full_list if value in item.lower()]
        combobox['values'] = filtered if filtered else full_list


    def create_algoritm_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text='Algoritm', font=('Segoe UI', 13, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 10))

        self.alg_listbox = tk.Listbox(frame, width=28, height=7)
        self.alg_listbox.grid(row=1, column=0, rowspan=4, padx=(0, 12), pady=5, sticky='ns')
        self.alg_listbox.bind('<<ListboxSelect>>', self._on_alg_select)

        ttk.Label(frame, text='Nume:').grid(row=1, column=1, sticky='e', padx=2, pady=2)
        self.alg_nume_var = tk.StringVar()
        self.alg_nume_entry = ttk.Entry(frame, textvariable=self.alg_nume_var, width=18)
        self.alg_nume_entry.grid(row=1, column=2, sticky='w', padx=2, pady=2)

        ttk.Label(frame, text='Tip:').grid(row=2, column=1, sticky='e', padx=2, pady=2)
        self.alg_tip_var = tk.StringVar()
        self.alg_tip_combo = ttk.Combobox(frame, textvariable=self.alg_tip_var, values=["Simetric", "Asimetric", "Hash", "Stream", "Block"], width=16, state='readonly')
        self.alg_tip_combo.grid(row=2, column=2, sticky='w', padx=2, pady=2)

        ttk.Button(frame, text='Adaugă', command=self._add_algoritm).grid(row=3, column=1, padx=2, pady=6, sticky='e')
        ttk.Button(frame, text='Editează', command=self._edit_algoritm).grid(row=3, column=2, padx=2, pady=6, sticky='w')
        ttk.Button(frame, text='Șterge', command=self._delete_algoritm).grid(row=4, column=1, columnspan=2, pady=2)

        self._refresh_alg_list()

    def _refresh_alg_list(self):
        if not hasattr(self, 'alg_repo'):
            from database.repositories.algoritm_repository import AlgoritmRepository
            self.alg_repo = AlgoritmRepository(self.app_context['db_manager'])
        self.algoritmi = self.alg_repo.get_all()
        self.alg_listbox.delete(0, tk.END)
        for alg in self.algoritmi:
            self.alg_listbox.insert(tk.END, f"{alg.nume} ({alg.tip})")
        self._clear_alg_fields()
        self.alg_selected_index = None

    def _clear_alg_fields(self):
        self.alg_nume_var.set("")
        self.alg_tip_var.set("")
        self.alg_selected_index = None

    def _on_alg_select(self, event):
        selection = self.alg_listbox.curselection()
        if selection:
            idx = selection[0]
            alg = self.algoritmi[idx]
            self.alg_nume_var.set(alg.nume)
            self.alg_tip_var.set(alg.tip)
            self.alg_selected_index = idx
        else:
            self._clear_alg_fields()

    def _add_algoritm(self):
        nume = self.alg_nume_var.get().strip()
        tip = self.alg_tip_var.get().strip()
        if not nume or not tip:
            messagebox.showwarning('Atenție', 'Completează toate câmpurile!')
            return
        from models.algoritm import Algoritm
        alg = Algoritm(id_algoritm=None, nume=nume, tip=tip)
        try:
            self.alg_repo.insert(alg)
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                messagebox.showerror('Eroare', 'Există deja un algoritm cu acest nume!')
                return
            else:
                messagebox.showerror('Eroare', f'Eroare la inserare: {e}')
                return
        self._refresh_alg_list()

    def _edit_algoritm(self):
        if self.alg_selected_index is None:
            messagebox.showwarning('Atenție', 'Selectează un algoritm din listă!')
            return
        nume = self.alg_nume_var.get().strip()
        tip = self.alg_tip_var.get().strip()
        if not nume or not tip:
            messagebox.showwarning('Atenție', 'Completează toate câmpurile!')
            return
        from models.algoritm import Algoritm
        alg = self.algoritmi[self.alg_selected_index]
        alg.nume = nume
        alg.tip = tip
        try:
            self.alg_repo.update(alg)
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                messagebox.showerror('Eroare', 'Există deja un algoritm cu acest nume!')
                return
            else:
                messagebox.showerror('Eroare', f'Eroare la actualizare: {e}')
                return
        self._refresh_alg_list()

    def _delete_algoritm(self):
        if self.alg_selected_index is None:
            messagebox.showwarning('Atenție', 'Selectează un algoritm din listă!')
            return
        alg = self.algoritmi[self.alg_selected_index]
        if messagebox.askyesno('Confirmare', f'Sigur vrei să ștergi algoritmul "{alg.nume}"?'):
            self.alg_repo.delete(alg.id_algoritm)
            self._refresh_alg_list()

    def create_cheie_tab(self, parent):
        ttk.Label(parent, text='Cheie').pack(pady=10)

    def create_fisier_tab(self, parent):
        ttk.Label(parent, text='Fisier').pack(pady=10)

    def create_framework_tab(self, parent):
        ttk.Label(parent, text='Framework').pack(pady=10)

    def create_operatie_tab(self, parent):
        ttk.Label(parent, text='Operatie').pack(pady=10)

    def create_performanta_tab(self, parent):
        ttk.Label(parent, text='Performanta').pack(pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_label.config(text=file_path)

    def encrypt_file(self):
        messagebox.showinfo('Info', 'File encrypted')

    def decrypt_file(self):
        messagebox.showinfo('Info', 'File decrypted')

    def analyze_performance(self):
        messagebox.showinfo('Info', 'Performance analyzed')
