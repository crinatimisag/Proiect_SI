from dataclasses import dataclass

@dataclass
class Operatie:
    id_operatie: int | None
    id_fisier: int
    id_cheie: int
    id_algoritm: int
    id_framework: int
    tip_operatie: str
    data_executie: str
    status: str
    fisier_rezultat: str
    hash_rezultat: str
