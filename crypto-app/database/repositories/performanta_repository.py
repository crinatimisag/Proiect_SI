from models.performanta import Performanta
from .base_repository import BaseRepository


class PerformantaRepository(BaseRepository):
    def insert(self, performanta: Performanta) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                INSERT INTO Performanta (
                    id_operatie, timp_executie_ms, memorie_kb, dimensiune_input, observatii
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    performanta.id_operatie,
                    performanta.timp_executie_ms,
                    performanta.memorie_kb,
                    performanta.dimensiune_input,
                    performanta.observatii,
                ),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Performanta ORDER BY id_performanta DESC").fetchall()
            return [Performanta(**dict(row)) for row in rows]

    def get_by_id(self, id_performanta: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Performanta WHERE id_performanta = ?", (id_performanta,)).fetchone()
            return Performanta(**dict(row)) if row else None

    def update(self, performanta: Performanta) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                UPDATE Performanta SET 
                    id_operatie = ?, timp_executie_ms = ?, memorie_kb = ?, 
                    dimensiune_input = ?, observatii = ?
                WHERE id_performanta = ?
                """,
                (
                    performanta.id_operatie, performanta.timp_executie_ms,
                    performanta.memorie_kb, performanta.dimensiune_input,
                    performanta.observatii, performanta.id_performanta
                ),
            )
            return rezultat.rowcount > 0

    def delete(self, id_performanta: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Performanta WHERE id_performanta = ?", (id_performanta,))
            return rezultat.rowcount > 0