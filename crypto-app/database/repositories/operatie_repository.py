from models.operatie import Operatie
from .base_repository import BaseRepository


class OperatieRepository(BaseRepository):
    def insert(self, operatie: Operatie) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                INSERT INTO Operatie (
                    id_fisier, id_cheie, id_algoritm, id_framework,
                    tip_operatie, data_executie, status, fisier_rezultat, hash_rezultat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operatie.id_fisier,
                    operatie.id_cheie,
                    operatie.id_algoritm,
                    operatie.id_framework,
                    operatie.tip_operatie,
                    operatie.data_executie,
                    operatie.status,
                    operatie.fisier_rezultat,
                    operatie.hash_rezultat,
                ),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Operatie ORDER BY id_operatie DESC").fetchall()
            return [Operatie(**dict(row)) for row in rows]

    def get_by_id(self, id_operatie: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Operatie WHERE id_operatie = ?", (id_operatie,)).fetchone()
            return Operatie(**dict(row)) if row else None

    def update(self, operatie: Operatie) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                """
                UPDATE Operatie SET 
                    id_fisier = ?, id_cheie = ?, id_algoritm = ?, id_framework = ?,
                    tip_operatie = ?, data_executie = ?, status = ?, 
                    fisier_rezultat = ?, hash_rezultat = ?
                WHERE id_operatie = ?
                """,
                (
                    operatie.id_fisier, operatie.id_cheie, operatie.id_algoritm,
                    operatie.id_framework, operatie.tip_operatie, operatie.data_executie,
                    operatie.status, operatie.fisier_rezultat, operatie.hash_rezultat,
                    operatie.id_operatie
                ),
            )
            return rezultat.rowcount > 0

    def delete(self, id_operatie: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Operatie WHERE id_operatie = ?", (id_operatie,))
            return rezultat.rowcount > 0