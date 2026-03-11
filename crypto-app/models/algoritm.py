from dataclasses import dataclass

@dataclass
class Algoritm:
    id_algoritm: int | None
    nume: str
    tip: str
    mod_operare: str | None = None
