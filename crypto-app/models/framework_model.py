from dataclasses import dataclass

@dataclass
class FrameworkModel:
    id_framework: int | None
    nume: str
    versiune: str
    limbaj_programare: str
