import tempfile
import unittest
from pathlib import Path

from database.db_manager import DBManager
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.framework_repository import FrameworkRepository
from models.algoritm import Algoritm
from models.framework_model import FrameworkModel
from services.crypto_service import CryptoService


class TestCryptoService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.db_path = self.base_dir / "test.db"
        self.schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
        self.db_manager = DBManager(self.db_path)
        self.db_manager.initialize_database(self.schema_path)

        self.alg_repo = AlgoritmRepository(self.db_manager)
        self.framework_repo = FrameworkRepository(self.db_manager)
        for name, tip in (("AES-256-GCM", "simetric"), ("RSA", "asimetric")):
            if not self.alg_repo.get_by_name(name):
                self.alg_repo.insert(Algoritm(None, name, tip))
        if not self.framework_repo.get_by_name("cryptography"):
            self.framework_repo.insert(FrameworkModel(None, "cryptography", "AESGCM + RSA-OAEP", "Python"))

        self.service = CryptoService(self.db_manager)
        self.sample_path = self.base_dir / "sample.txt"
        self.sample_path.write_text("salut lume, test de criptare", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_aes_roundtrip(self):
        algoritm = self.alg_repo.get_by_name("AES-256-GCM")
        key = self.service.generate_key_for_algorithm(algoritm.id_algoritm, "aes_test")
        self.assertEqual(key.tip_cheie, "secret")
        self.assertEqual(key.dimensiune_cheie, 32)

        fisier = self.service.register_file(self.sample_path)
        encrypt_result = self.service.encrypt_file(fisier.id_fisier, key.id_cheie, algoritm.id_algoritm)
        encrypted = encrypt_result["output_file"]
        decrypt_result = self.service.decrypt_file(encrypted.id_fisier, key.id_cheie, algoritm.id_algoritm)
        decrypted_path = Path(decrypt_result["output_file"].cale_fisier)
        self.assertEqual(decrypted_path.read_text(encoding="utf-8"), self.sample_path.read_text(encoding="utf-8"))

    def test_rsa_roundtrip(self):
        algoritm = self.alg_repo.get_by_name("RSA")
        key = self.service.generate_key_for_algorithm(algoritm.id_algoritm, "rsa_test")
        self.assertEqual(key.tip_cheie, "privata")
        self.assertEqual(key.dimensiune_cheie, 2048)

        fisier = self.service.register_file(self.sample_path)
        encrypt_result = self.service.encrypt_file(fisier.id_fisier, key.id_cheie, algoritm.id_algoritm)
        encrypted = encrypt_result["output_file"]
        decrypt_result = self.service.decrypt_file(encrypted.id_fisier, key.id_cheie, algoritm.id_algoritm)
        decrypted_path = Path(decrypt_result["output_file"].cale_fisier)
        self.assertEqual(decrypted_path.read_text(encoding="utf-8"), self.sample_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
