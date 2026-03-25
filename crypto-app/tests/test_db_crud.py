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
from models.framework_model import FrameworkModel
from models.fisier import Fisier
from models.operatie import Operatie
from models.performanta import Performanta
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

            algoritm_actualizat = Algoritm(algoritm_id, "AES-256", "simetric")
            self.assertTrue(alg_repo.update(algoritm_actualizat))

            dupa_update = alg_repo.get_by_id(algoritm_id)
            self.assertEqual(dupa_update.nume, "AES-256")

            self.assertTrue(alg_repo.delete(algoritm_id))
            self.assertIsNone(alg_repo.get_by_id(algoritm_id))
        finally:
            temp_dir.cleanup()


    def test_cheie_crud(self):
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
            self.assertIsInstance(cheie_id, int)

            cheie_din_db = cheie_repo.get_by_id(cheie_id)
            self.assertIsNotNone(cheie_din_db)
            self.assertEqual(cheie_din_db.nume_cheie, "cheie_test")
            self.assertEqual(cheie_din_db.id_algoritm, algoritm_id)

            cheie_actualizata = Cheie(
                cheie_id,
                algoritm_id,
                "cheie_noua",
                "publica",
                4096,
                "/keys/test2.pem",
                "2026-03-25",
                "inactiva"
            )
            self.assertTrue(cheie_repo.update(cheie_actualizata))

            dupa_update = cheie_repo.get_by_id(cheie_id)
            self.assertEqual(dupa_update.nume_cheie, "cheie_noua")
            self.assertEqual(dupa_update.tip_cheie, "publica")

            self.assertTrue(cheie_repo.delete(cheie_id))
            self.assertIsNone(cheie_repo.get_by_id(cheie_id))
        finally:
            temp_dir.cleanup()


    def test_fisier_crud(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            fisier_repo = FisierRepository(db_manager)

            fisier = Fisier(
                None,
                "document.txt",
                "/tmp/document.txt",
                "hash123",
                128,
                "2026-03-24",
                "nou"
            )
            fisier_id = fisier_repo.insert(fisier)
            self.assertIsInstance(fisier_id, int)

            fisier_din_db = fisier_repo.get_by_id(fisier_id)
            self.assertIsNotNone(fisier_din_db)
            self.assertEqual(fisier_din_db.nume_fisier, "document.txt")

            fisier_actualizat = Fisier(
                fisier_id,
                "document2.txt",
                "/tmp/document2.txt",
                "hash999",
                256,
                "2026-03-25",
                "procesat"
            )
            self.assertTrue(fisier_repo.update(fisier_actualizat))

            dupa_update = fisier_repo.get_by_id(fisier_id)
            self.assertEqual(dupa_update.nume_fisier, "document2.txt")
            self.assertEqual(dupa_update.status, "procesat")

            self.assertTrue(fisier_repo.delete(fisier_id))
            self.assertIsNone(fisier_repo.get_by_id(fisier_id))
        finally:
            temp_dir.cleanup()


    def test_framework_crud(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            framework_repo = FrameworkRepository(db_manager)

            framework = FrameworkModel(None, "PyCryptodome", "3.20.0", "Python")
            framework_id = framework_repo.insert(framework)
            self.assertIsInstance(framework_id, int)

            framework_din_db = framework_repo.get_by_id(framework_id)
            self.assertIsNotNone(framework_din_db)
            self.assertEqual(framework_din_db.nume, "PyCryptodome")

            framework_actualizat = FrameworkModel(framework_id, "OpenSSL", "3.0", "C")
            self.assertTrue(framework_repo.update(framework_actualizat))

            dupa_update = framework_repo.get_by_id(framework_id)
            self.assertEqual(dupa_update.nume, "OpenSSL")
            self.assertEqual(dupa_update.limbaj_programare, "C")

            self.assertTrue(framework_repo.delete(framework_id))
            self.assertIsNone(framework_repo.get_by_id(framework_id))
        finally:
            temp_dir.cleanup()


    def test_operatie_crud(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            alg_repo = AlgoritmRepository(db_manager)
            cheie_repo = CheieRepository(db_manager)
            fisier_repo = FisierRepository(db_manager)
            framework_repo = FrameworkRepository(db_manager)
            operatie_repo = OperatieRepository(db_manager)

            algoritm_id = alg_repo.insert(Algoritm(None, "RSA", "asimetric", None))
            cheie_id = cheie_repo.insert(
                Cheie(None, algoritm_id, "rsa_key", "privata", 2048, "/keys/rsa.pem", "2026-03-24", "activa")
            )
            fisier_id = fisier_repo.insert(
                Fisier(None, "doc.txt", "/tmp/doc.txt", "hash1", 100, "2026-03-24", "nou")
            )
            framework_id = framework_repo.insert(
                FrameworkModel(None, "PyCryptodome", "3.20.0", "Python")
            )

            operatie = Operatie(
                None,
                fisier_id,
                cheie_id,
                algoritm_id,
                framework_id,
                "criptare",
                "2026-03-24 10:00:00",
                "succes",
                "/encrypted/doc.enc",
                "hash2"
            )
            operatie_id = operatie_repo.insert(operatie)
            self.assertIsInstance(operatie_id, int)

            operatie_din_db = operatie_repo.get_by_id(operatie_id)
            self.assertIsNotNone(operatie_din_db)
            self.assertEqual(operatie_din_db.tip_operatie, "criptare")

            operatie_actualizata = Operatie(
                operatie_id,
                fisier_id,
                cheie_id,
                algoritm_id,
                framework_id,
                "decriptare",
                "2026-03-24 10:05:00",
                "succes",
                "/decrypted/doc.txt",
                "hash3"
            )
            self.assertTrue(operatie_repo.update(operatie_actualizata))

            dupa_update = operatie_repo.get_by_id(operatie_id)
            self.assertEqual(dupa_update.tip_operatie, "decriptare")
            self.assertEqual(dupa_update.fisier_rezultat, "/decrypted/doc.txt")

            self.assertTrue(operatie_repo.delete(operatie_id))
            self.assertIsNone(operatie_repo.get_by_id(operatie_id))
        finally:
            temp_dir.cleanup()


    def test_performanta_crud(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            db_path = Path(temp_dir.name) / "test.db"
            schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

            db_manager = DBManager(db_path)
            db_manager.initialize_database(schema_path)

            alg_repo = AlgoritmRepository(db_manager)
            cheie_repo = CheieRepository(db_manager)
            fisier_repo = FisierRepository(db_manager)
            framework_repo = FrameworkRepository(db_manager)
            operatie_repo = OperatieRepository(db_manager)
            performanta_repo = PerformantaRepository(db_manager)

            algoritm_id = alg_repo.insert(Algoritm(None, "RSA", "asimetric", None))
            cheie_id = cheie_repo.insert(
                Cheie(None, algoritm_id, "rsa_key", "privata", 2048, "/keys/rsa.pem", "2026-03-24", "activa")
            )
            fisier_id = fisier_repo.insert(
                Fisier(None, "doc.txt", "/tmp/doc.txt", "hash1", 100, "2026-03-24", "nou")
            )
            framework_id = framework_repo.insert(
                FrameworkModel(None, "PyCryptodome", "3.20.0", "Python")
            )
            operatie_id = operatie_repo.insert(
                Operatie(
                    None,
                    fisier_id,
                    cheie_id,
                    algoritm_id,
                    framework_id,
                    "criptare",
                    "2026-03-24 10:00:00",
                    "succes",
                    "/encrypted/doc.enc",
                    "hash2"
                )
            )

            performanta = Performanta(None, operatie_id, 15.5, 2048.0, 128, "test initial")
            performanta_id = performanta_repo.insert(performanta)
            self.assertIsInstance(performanta_id, int)

            performanta_din_db = performanta_repo.get_by_id(performanta_id)
            self.assertIsNotNone(performanta_din_db)
            self.assertEqual(performanta_din_db.observatii, "test initial")

            performanta_actualizata = Performanta(
                performanta_id,
                operatie_id,
                12.0,
                1800.0,
                256,
                "performanta imbunatatita"
            )
            self.assertTrue(performanta_repo.update(performanta_actualizata))

            dupa_update = performanta_repo.get_by_id(performanta_id)
            self.assertEqual(dupa_update.observatii, "performanta imbunatatita")
            self.assertEqual(dupa_update.dimensiune_input, 256)

            self.assertTrue(performanta_repo.delete(performanta_id))
            self.assertIsNone(performanta_repo.get_by_id(performanta_id))
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