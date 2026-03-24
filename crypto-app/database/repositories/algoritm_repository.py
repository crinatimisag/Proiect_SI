from models.algoritm import Algoritm
from .base_repository import BaseRepository


class AlgoritmRepository(BaseRepository):
    def insert(self, algoritm: Algoritm) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                "INSERT INTO Algoritm (nume, tip, mod_operare) VALUES (?, ?, ?)",
                (algoritm.nume, algoritm.tip, algoritm.mod_operare),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Algoritm ORDER BY id_algoritm").fetchall()
            return [Algoritm(**dict(row)) for row in rows]

    def get_by_id(self, id_algoritm: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Algoritm WHERE id_algoritm = ?", (id_algoritm,)).fetchone()
            return Algoritm(**dict(row)) if row else None

    def get_by_name(self, nume: str):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Algoritm WHERE nume = ? LIMIT 1", (nume,)).fetchone()
            return Algoritm(**dict(row)) if row else None

    def update(self, algoritm: Algoritm) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                "UPDATE Algoritm SET nume = ?, tip = ?, mod_operare = ? WHERE id_algoritm = ?",
                (algoritm.nume, algoritm.tip, algoritm.mod_operare, algoritm.id_algoritm),
            )
            return rezultat.rowcount > 0

    def delete(self, id_algoritm: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Algoritm WHERE id_algoritm = ?", (id_algoritm,))
            return rezultat.rowcount > 0