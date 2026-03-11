from dataclasses import dataclass

@dataclass
class Fisier:
    id_fisier: int | None
    nume_fisier: str
    cale_fisier: str
    hash_initial: str
    dimensiune: int
    data_adaugare: str
    status: str
