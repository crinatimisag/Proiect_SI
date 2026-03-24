from models.fisier import Fisier
from .base_repository import BaseRepository


class FisierRepository(BaseRepository):
    def insert(self, fisier: Fisier) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                INSERT INTO Fisier (nume_fisier, cale_fisier, hash_initial, dimensiune, data_adaugare, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    fisier.nume_fisier,
                    fisier.cale_fisier,
                    fisier.hash_initial,
                    fisier.dimensiune,
                    fisier.data_adaugare,
                    fisier.status,
                ),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Fisier ORDER BY id_fisier DESC").fetchall()
            return [Fisier(**dict(row)) for row in rows]

    def get_by_id(self, id_fisier: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Fisier WHERE id_fisier = ?", (id_fisier,)).fetchone()
            return Fisier(**dict(row)) if row else None

    def update(self, fisier: Fisier) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                UPDATE Fisier SET 
                    nume_fisier = ?, cale_fisier = ?, hash_initial = ?, 
                    dimensiune = ?, data_adaugare = ?, status = ?
                WHERE id_fisier = ?
                """,
                (
                    fisier.nume_fisier, fisier.cale_fisier, fisier.hash_initial,
                    fisier.dimensiune, fisier.data_adaugare, fisier.status, fisier.id_fisier
                ),
            )
            return rezultat.rowcount > 0

    def delete(self, id_fisier: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Fisier WHERE id_fisier = ?", (id_fisier,))
            return rezultat.rowcount > 0