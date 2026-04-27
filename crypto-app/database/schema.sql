CREATE TABLE IF NOT EXISTS Algoritm (
    id_algoritm INTEGER PRIMARY KEY AUTOINCREMENT,
    nume TEXT NOT NULL UNIQUE,
    tip TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Cheie (
    id_cheie INTEGER PRIMARY KEY AUTOINCREMENT,
    id_algoritm INTEGER NOT NULL,
    nume_cheie TEXT NOT NULL UNIQUE,
    tip_cheie TEXT NOT NULL,
    dimensiune_cheie INTEGER NOT NULL,
    locatie_cheie TEXT NOT NULL,
    valoare_cheie_hex TEXT NOT NULL DEFAULT '',
    data_creare TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (id_algoritm) REFERENCES Algoritm(id_algoritm)
);

CREATE TABLE IF NOT EXISTS Fisier (
    id_fisier INTEGER PRIMARY KEY AUTOINCREMENT,
    nume_fisier TEXT NOT NULL UNIQUE,
    cale_fisier TEXT NOT NULL,
    hash_initial TEXT NOT NULL,
    dimensiune INTEGER NOT NULL,
    data_adaugare TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Framework (
    id_framework INTEGER PRIMARY KEY AUTOINCREMENT,
    nume TEXT NOT NULL UNIQUE,
    versiune TEXT NOT NULL,
    limbaj_programare TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Operatie (
    id_operatie INTEGER PRIMARY KEY AUTOINCREMENT,
    id_fisier INTEGER NOT NULL,
    id_cheie INTEGER NOT NULL,
    id_algoritm INTEGER NOT NULL,
    id_framework INTEGER NOT NULL,
    tip_operatie TEXT NOT NULL,
    data_executie TEXT NOT NULL,
    status TEXT NOT NULL,
    fisier_rezultat TEXT NOT NULL,
    hash_rezultat TEXT NOT NULL,
    FOREIGN KEY (id_fisier) REFERENCES Fisier(id_fisier),
    FOREIGN KEY (id_cheie) REFERENCES Cheie(id_cheie),
    FOREIGN KEY (id_algoritm) REFERENCES Algoritm(id_algoritm),
    FOREIGN KEY (id_framework) REFERENCES Framework(id_framework)
);

CREATE TABLE IF NOT EXISTS Performanta (
    id_performanta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_operatie INTEGER NOT NULL,
    timp_executie_ms REAL NOT NULL,
    memorie_kb REAL NOT NULL,
    dimensiune_input INTEGER NOT NULL,
    observatii TEXT,
    FOREIGN KEY (id_operatie) REFERENCES Operatie(id_operatie)
);