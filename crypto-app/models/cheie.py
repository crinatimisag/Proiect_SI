from dataclasses import dataclass

@dataclass
class Cheie:
    id_cheie: int | None
    id_algoritm: int
    nume_cheie: str
    tip_cheie: str
    dimensiune_cheie: int
    locatie_cheie: str
    data_creare: str
    status: str
