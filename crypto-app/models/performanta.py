from dataclasses import dataclass

@dataclass
class Performanta:
    id_performanta: int | None
    id_operatie: int
    timp_executie_ms: float
    memorie_kb: float
    dimensiune_input: int
    observatii: str | None = None
