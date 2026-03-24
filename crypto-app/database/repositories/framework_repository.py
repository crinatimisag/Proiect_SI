from models.framework_model import FrameworkModel
from .base_repository import BaseRepository


class FrameworkRepository(BaseRepository):
    def insert(self, framework: FrameworkModel) -> int:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                "INSERT INTO Framework (nume, versiune, limbaj_programare) VALUES (?, ?, ?)",
                (framework.nume, framework.versiune, framework.limbaj_programare),
            )
            return rezultat.lastrowid

    def get_all(self):
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Framework ORDER BY id_framework").fetchall()
            return [FrameworkModel(**dict(row)) for row in rows]

    def get_by_id(self, id_framework: int):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Framework WHERE id_framework = ?", (id_framework,)).fetchone()
            return FrameworkModel(**dict(row)) if row else None

    def get_by_name(self, nume: str):
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM Framework WHERE nume = ? LIMIT 1", (nume,)).fetchone()
            return FrameworkModel(**dict(row)) if row else None

    def update(self, framework: FrameworkModel) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute(
                "UPDATE Framework SET nume = ?, versiune = ?, limbaj_programare = ? WHERE id_framework = ?",
                (framework.nume, framework.versiune, framework.limbaj_programare, framework.id_framework),
            )
            return rezultat.rowcount > 0

    def delete(self, id_framework: int) -> bool:
        with self.db_manager.get_connection() as conn:
            rezultat = conn.execute("DELETE FROM Framework WHERE id_framework = ?", (id_framework,))
            return rezultat.rowcount > 0