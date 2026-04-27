from models.cheie import Cheie
from .base_repository import BaseRepository


class CheieRepository(BaseRepository):
    def insert(self, cheie: Cheie) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                INSERT INTO Cheie (
                    id_algoritm, nume_cheie, tip_cheie, dimensiune_cheie,
                    locatie_cheie, valoare_cheie_hex, data_creare, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cheie.id_algoritm,
                    cheie.nume_cheie,
                    cheie.tip_cheie,
                    cheie.dimensiune_cheie,
                    cheie.locatie_cheie,
                    cheie.valoare_cheie_hex,
                    cheie.data_creare,
                    cheie.status,
                ),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Cheie ORDER BY id_cheie DESC").fetchall()
            return [Cheie(**dict(row)) for row in rows]

    def get_by_id(self, id_cheie: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Cheie WHERE id_cheie = ?", (id_cheie,)).fetchone()
            return Cheie(**dict(row)) if row else None

    def update(self, cheie: Cheie) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                UPDATE Cheie SET
                    id_algoritm = ?, nume_cheie = ?, tip_cheie = ?,
                    dimensiune_cheie = ?, locatie_cheie = ?, valoare_cheie_hex = ?,
                    data_creare = ?, status = ?
                WHERE id_cheie = ?
                """,
                (
                    cheie.id_algoritm,
                    cheie.nume_cheie,
                    cheie.tip_cheie,
                    cheie.dimensiune_cheie,
                    cheie.locatie_cheie,
                    cheie.valoare_cheie_hex,
                    cheie.data_creare,
                    cheie.status,
                    cheie.id_cheie,
                ),
            )
            return rezultat.rowcount > 0

    def delete(self, id_cheie: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Cheie WHERE id_cheie = ?", (id_cheie,))
            return rezultat.rowcount > 0