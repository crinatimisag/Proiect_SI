import tempfile
import unittest
from pathlib import Path

from database.db_manager import DBManager
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.cheie_repository import CheieRepository
from models.algoritm import Algoritm
from models.cheie import Cheie


class TestDatabaseCRUD(unittest.TestCase):

    def test_initialize_database_creates_tables(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            expected_tables = {"Algoritm", "Cheie", "Fisier", "Framework", "Operatie", "Performanta"}

            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()

            created_tables = {row["name"] for row in rows}
            self.assertTrue(expected_tables.issubset(created_tables))
        finally:
            temp_dir.cleanup()

    def test_algoritm_crud(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            alg_repo = AlgoritmRepository(db_manager)

            algoritm = Algoritm(None, "AES", "simetric", "CBC")
            algoritm_id = alg_repo.insert(algoritm)
            self.assertIsInstance(algoritm_id, int)

            algoritm_din_db = alg_repo.get_by_id(algoritm_id)
            self.assertIsNotNone(algoritm_din_db)
            self.assertEqual(algoritm_din_db.nume, "AES")
            self.assertEqual(algoritm_din_db.tip, "simetric")

            algoritm_actualizat = Algoritm(algoritm_id, "AES-256", "simetric", "GCM")
            self.assertTrue(alg_repo.update(algoritm_actualizat))

            dupa_update = alg_repo.get_by_id(algoritm_id)
            self.assertEqual(dupa_update.nume, "AES-256")
            self.assertEqual(dupa_update.mod_operare, "GCM")

            self.assertTrue(alg_repo.delete(algoritm_id))
            self.assertIsNone(alg_repo.get_by_id(algoritm_id))
        finally:
            temp_dir.cleanup()

    def test_cheie_legata_de_algoritm(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            alg_repo = AlgoritmRepository(db_manager)
            cheie_repo = CheieRepository(db_manager)

            algoritm_id = alg_repo.insert(Algoritm(None, "RSA", "asimetric", None))

            cheie = Cheie(
                None,
                algoritm_id,
                "cheie_test",
                "privata",
                2048,
                "/keys/test.pem",
                "2026-03-24",
                "activa"
            )
            cheie_id = cheie_repo.insert(cheie)

            cheie_din_db = cheie_repo.get_by_id(cheie_id)
            self.assertIsNotNone(cheie_din_db)
            self.assertEqual(cheie_din_db.nume_cheie, "cheie_test")
            self.assertEqual(cheie_din_db.id_algoritm, algoritm_id)
        finally:
            temp_dir.cleanup()

    def test_foreign_key_constraint_is_enforced(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            cheie_repo = CheieRepository(db_manager)

            cheie_invalida = Cheie(
                None,
                9999,
                "cheie_invalida",
                "privata",
                1024,
                "/keys/invalid.pem",
                "2026-03-24",
                "inactiva"
            )

            with self.assertRaises(Exception):
                cheie_repo.insert(cheie_invalida)
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()