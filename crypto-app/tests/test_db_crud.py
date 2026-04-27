import tempfile
import unittest
from pathlib import Path

from database.db_manager import DBManager
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.cheie_repository import CheieRepository
from database.repositories.fisier_repository import FisierRepository
from database.repositories.framework_repository import FrameworkRepository
from database.repositories.operatie_repository import OperatieRepository
from database.repositories.performanta_repository import PerformantaRepository
from models.algoritm import Algoritm
from models.cheie import Cheie
from models.fisier import Fisier
from models.framework_model import FrameworkModel
from models.operatie import Operatie
from models.performanta import Performanta


class TestDatabaseCRUD(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
        self.db_manager = DBManager(self.db_path)
        self.db_manager.initialize_database(self.schema_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_key(self, algoritm_id: int, key_size: int, name: str = "cheie_test") -> Cheie:
        return Cheie(
            None,
            algoritm_id,
            name,
            "secret",
            key_size,
            "DB",
            "AA" * key_size,
            "2026-03-24",
            "activa",
        )

    def test_initialize_database_creates_tables(self):
        expected_tables = {"Algoritm", "Cheie", "Fisier", "Framework", "Operatie", "Performanta"}
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        created_tables = {row["name"] for row in rows}
        self.assertTrue(expected_tables.issubset(created_tables))

    def test_algoritm_crud(self):
        alg_repo = AlgoritmRepository(self.db_manager)
        algoritm_id = alg_repo.insert(Algoritm(None, "AES-256-GCM", "simetric"))
        self.assertIsInstance(algoritm_id, int)

        algoritm_din_db = alg_repo.get_by_id(algoritm_id)
        self.assertEqual(algoritm_din_db.nume, "AES-256-GCM")

        self.assertTrue(alg_repo.update(Algoritm(algoritm_id, "AES-128-GCM", "simetric")))
        self.assertEqual(alg_repo.get_by_id(algoritm_id).nume, "AES-128-GCM")

        self.assertTrue(alg_repo.delete(algoritm_id))
        self.assertIsNone(alg_repo.get_by_id(algoritm_id))

    def test_cheie_crud(self):
        alg_repo = AlgoritmRepository(self.db_manager)
        cheie_repo = CheieRepository(self.db_manager)

        algoritm_id = alg_repo.insert(Algoritm(None, "AES-256-GCM", "simetric"))
        cheie_id = cheie_repo.insert(self._build_key(algoritm_id, 32))
        self.assertIsInstance(cheie_id, int)

        cheie_din_db = cheie_repo.get_by_id(cheie_id)
        self.assertEqual(cheie_din_db.nume_cheie, "cheie_test")
        self.assertEqual(cheie_din_db.valoare_cheie_hex, "AA" * 32)

        actualizata = Cheie(
            cheie_id,
            algoritm_id,
            "cheie_noua",
            "secret",
            16,
            "DB",
            "BB" * 16,
            "2026-03-25",
            "inactiva",
        )
        self.assertTrue(cheie_repo.update(actualizata))
        dupa_update = cheie_repo.get_by_id(cheie_id)
        self.assertEqual(dupa_update.nume_cheie, "cheie_noua")
        self.assertEqual(dupa_update.dimensiune_cheie, 16)

        self.assertTrue(cheie_repo.delete(cheie_id))
        self.assertIsNone(cheie_repo.get_by_id(cheie_id))

    def test_fisier_crud(self):
        fisier_repo = FisierRepository(self.db_manager)
        fisier = Fisier(None, "document.txt", "/tmp/document.txt", "hash123", 128, "2026-03-24", "nou")
        fisier_id = fisier_repo.insert(fisier)
        self.assertIsInstance(fisier_id, int)
        self.assertEqual(fisier_repo.get_by_id(fisier_id).nume_fisier, "document.txt")

        actualizat = Fisier(fisier_id, "document2.txt", "/tmp/document2.txt", "hash999", 256, "2026-03-25", "procesat")
        self.assertTrue(fisier_repo.update(actualizat))
        dupa_update = fisier_repo.get_by_id(fisier_id)
        self.assertEqual(dupa_update.status, "procesat")

        self.assertTrue(fisier_repo.delete(fisier_id))
        self.assertIsNone(fisier_repo.get_by_id(fisier_id))

    def test_framework_crud(self):
        framework_repo = FrameworkRepository(self.db_manager)
        framework_id = framework_repo.insert(FrameworkModel(None, "cryptography", "AESGCM + RSA-OAEP", "Python"))
        self.assertIsInstance(framework_id, int)
        self.assertEqual(framework_repo.get_by_id(framework_id).nume, "cryptography")

        actualizat = FrameworkModel(framework_id, "cryptography", "AESGCM + RSA-OAEP + hybrid", "Python")
        self.assertTrue(framework_repo.update(actualizat))
        self.assertEqual(framework_repo.get_by_id(framework_id).versiune, "AESGCM + RSA-OAEP + hybrid")

        self.assertTrue(framework_repo.delete(framework_id))
        self.assertIsNone(framework_repo.get_by_id(framework_id))

    def test_operatie_crud(self):
        alg_repo = AlgoritmRepository(self.db_manager)
        cheie_repo = CheieRepository(self.db_manager)
        fisier_repo = FisierRepository(self.db_manager)
        framework_repo = FrameworkRepository(self.db_manager)
        operatie_repo = OperatieRepository(self.db_manager)

        algoritm_id = alg_repo.insert(Algoritm(None, "AES-256-GCM", "simetric"))
        cheie_id = cheie_repo.insert(self._build_key(algoritm_id, 32, "aes_key"))
        fisier_id = fisier_repo.insert(Fisier(None, "doc.txt", "/tmp/doc.txt", "hash1", 100, "2026-03-24", "nou"))
        framework_id = framework_repo.insert(FrameworkModel(None, "cryptography", "AESGCM + RSA-OAEP", "Python"))

        operatie = Operatie(None, fisier_id, cheie_id, algoritm_id, framework_id, "criptare", "2026-03-24 10:00:00", "succes", "/encrypted/doc.enc", "hash2")
        operatie_id = operatie_repo.insert(operatie)
        self.assertIsInstance(operatie_id, int)
        self.assertEqual(operatie_repo.get_by_id(operatie_id).tip_operatie, "criptare")

        actualizata = Operatie(operatie_id, fisier_id, cheie_id, algoritm_id, framework_id, "decriptare", "2026-03-24 10:05:00", "succes", "/decrypted/doc.txt", "hash3")
        self.assertTrue(operatie_repo.update(actualizata))
        dupa_update = operatie_repo.get_by_id(operatie_id)
        self.assertEqual(dupa_update.tip_operatie, "decriptare")
        self.assertEqual(dupa_update.fisier_rezultat, "/decrypted/doc.txt")

        self.assertTrue(operatie_repo.delete(operatie_id))
        self.assertIsNone(operatie_repo.get_by_id(operatie_id))

    def test_performanta_crud(self):
        alg_repo = AlgoritmRepository(self.db_manager)
        cheie_repo = CheieRepository(self.db_manager)
        fisier_repo = FisierRepository(self.db_manager)
        framework_repo = FrameworkRepository(self.db_manager)
        operatie_repo = OperatieRepository(self.db_manager)
        performanta_repo = PerformantaRepository(self.db_manager)

        algoritm_id = alg_repo.insert(Algoritm(None, "AES-256-GCM", "simetric"))
        cheie_id = cheie_repo.insert(self._build_key(algoritm_id, 32, "aes_key"))
        fisier_id = fisier_repo.insert(Fisier(None, "doc.txt", "/tmp/doc.txt", "hash1", 100, "2026-03-24", "nou"))
        framework_id = framework_repo.insert(FrameworkModel(None, "cryptography", "AESGCM + RSA-OAEP", "Python"))
        operatie_id = operatie_repo.insert(Operatie(None, fisier_id, cheie_id, algoritm_id, framework_id, "criptare", "2026-03-24 10:00:00", "succes", "/encrypted/doc.enc", "hash2"))

        performanta_id = performanta_repo.insert(Performanta(None, operatie_id, 15.5, 2048.0, 128, "test initial"))
        self.assertIsInstance(performanta_id, int)
        self.assertEqual(performanta_repo.get_by_id(performanta_id).observatii, "test initial")

        actualizata = Performanta(performanta_id, operatie_id, 12.0, 1800.0, 256, "performanta imbunatatita")
        self.assertTrue(performanta_repo.update(actualizata))
        dupa_update = performanta_repo.get_by_id(performanta_id)
        self.assertEqual(dupa_update.observatii, "performanta imbunatatita")
        self.assertEqual(dupa_update.dimensiune_input, 256)

        self.assertTrue(performanta_repo.delete(performanta_id))
        self.assertIsNone(performanta_repo.get_by_id(performanta_id))

    def test_foreign_key_constraint_is_enforced(self):
        cheie_repo = CheieRepository(self.db_manager)
        cheie_invalida = Cheie(None, 9999, "cheie_invalida", "secret", 32, "DB", "AA" * 32, "2026-03-24", "inactiva")
        with self.assertRaises(Exception):
            cheie_repo.insert(cheie_invalida)


if __name__ == "__main__":
    unittest.main()