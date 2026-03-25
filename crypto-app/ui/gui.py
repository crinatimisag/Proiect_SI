
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk



class CryptoAppUI(tk.Tk):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.title('Crypto App')
        self.geometry('480x320')
        self.bg_color = '#ffffff'
        self.configure(bg=self.bg_color)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground='#222', font=('Segoe UI', 11))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=4)
        self.style.configure('TEntry', font=('Segoe UI', 10))
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Titlu simplu
        title = ttk.Label(main_frame, text='Crypto Key Management System', font=('Segoe UI', 15, 'bold'), background=self.bg_color)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 18))

        # Algoritm
        ttk.Label(main_frame, text='Algorithm:').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.alg_var = tk.StringVar(value='AES')
        self.alg_menu = ttk.Combobox(main_frame, textvariable=self.alg_var, values=['AES', 'RSA'], state='readonly', width=14)
        self.alg_menu.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Cheie
        ttk.Label(main_frame, text='Key:').grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.key_entry = ttk.Entry(main_frame, width=18)
        self.key_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        ttk.Button(main_frame, text='Add Key', command=self.add_key).grid(row=2, column=2, sticky='w', padx=5, pady=5)

        # Fisier
        ttk.Label(main_frame, text='File:').grid(row=3, column=0, sticky='e', padx=5, pady=5)
        ttk.Button(main_frame, text='Browse', command=self.browse_file).grid(row=3, column=1, sticky='w', padx=5, pady=5)
        self.file_label = ttk.Label(main_frame, text='No file selected', foreground='#888', background=self.bg_color)
        self.file_label.grid(row=4, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 10))

        # Butoane operații pe un rând
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text='Encrypt', command=self.encrypt_file, width=12).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Decrypt', command=self.decrypt_file, width=12).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Analyze Performance', command=self.analyze_performance, width=18).pack(side='left', padx=6)


    def add_key(self):
        messagebox.showinfo('Info', 'Key added')

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
