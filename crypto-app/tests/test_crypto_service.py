import subprocess
import tempfile
import unittest
from pathlib import Path

import config
import services.crypto_service as crypto_service_module
from database.db_manager import DBManager
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.framework_repository import FrameworkRepository
from models.algoritm import Algoritm
from models.framework_model import FrameworkModel
from services.crypto_service import CryptoService
from services.cryptography_framework import CryptographyFrameworkError


class TestCryptoService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        self.files_dir = self.base_dir / "files"
        self.encrypted_dir = self.base_dir / "encrypted"
        self.decrypted_dir = self.base_dir / "decrypted"
        for directory in (self.files_dir, self.encrypted_dir, self.decrypted_dir):
            directory.mkdir(parents=True, exist_ok=True)

        crypto_service_module.FILES_DIR = self.files_dir
        crypto_service_module.ENCRYPTED_DIR = self.encrypted_dir
        crypto_service_module.DECRYPTED_DIR = self.decrypted_dir

        self.db_path = self.base_dir / "test.db"
        self.schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
        self.db_manager = DBManager(self.db_path)
        self.db_manager.initialize_database(self.schema_path)

        self.alg_repo = AlgoritmRepository(self.db_manager)
        self.framework_repo = FrameworkRepository(self.db_manager)

        for name, tip in (
            ("AES-256-GCM", "simetric"),
            ("AES-256-CBC", "simetric"),
            ("RSA", "asimetric"),
        ):
            if not self.alg_repo.get_by_name(name):
                self.alg_repo.insert(Algoritm(None, name, tip))

        if not self.framework_repo.get_by_name("cryptography"):
            self.framework_repo.insert(
                FrameworkModel(None, "cryptography", "AES-GCM/CBC + RSA-OAEP", "Python")
            )
        if not self.framework_repo.get_by_name("OpenSSL CLI"):
            self.framework_repo.insert(
                FrameworkModel(None, "OpenSSL CLI", "OpenSSL binary", "C / Binary")
            )

        self.cryptography_framework = self.framework_repo.get_by_name("cryptography")
        self.openssl_framework = self.framework_repo.get_by_name("OpenSSL CLI")

        self.service = CryptoService(self.db_manager)
        self.sample_path = self.base_dir / "sample.txt"
        self.sample_bytes = (
            "salut lume, test de criptare\n".encode("utf-8")
            + bytes(range(32))
            + b"\ncontinut binar + text"
        )
        self.sample_path.write_bytes(self.sample_bytes)

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def _openssl_available() -> bool:
        openssl_path = config.OPENSSL_PATH
        try:
            subprocess.run(
                [openssl_path, "version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except Exception:
            return False

    def _roundtrip(self, algorithm_name: str, framework_id: int, key_name: str):
        algoritm = self.alg_repo.get_by_name(algorithm_name)
        self.assertIsNotNone(algoritm)

        key = self.service.make_key(algoritm.id_algoritm, key_name, framework_id)
        self.assertEqual(key.id_algoritm, algoritm.id_algoritm)
        self.assertTrue(key.valoare_cheie_hex)

        fisier = self.service.register_file(self.sample_path)
        encrypt_result = self.service.encrypt_file(
            fisier.id_fisier,
            key.id_cheie,
            algoritm.id_algoritm,
            framework_id,
        )
        encrypted = encrypt_result["output_file"]
        encrypted_path = Path(encrypted.cale_fisier)
        self.assertTrue(encrypted_path.exists())
        self.assertNotEqual(encrypted_path.read_bytes(), self.sample_bytes)

        decrypt_result = self.service.decrypt_file(
            encrypted.id_fisier,
            key.id_cheie,
            algoritm.id_algoritm,
            framework_id,
        )
        decrypted_path = Path(decrypt_result["output_file"].cale_fisier)
        self.assertTrue(decrypted_path.exists())
        self.assertEqual(decrypted_path.read_bytes(), self.sample_bytes)

        self._assert_operation_and_performance_were_saved(algorithm_name)

    def _assert_operation_and_performance_were_saved(self, algorithm_name: str):
        with self.db_manager.get_connection() as conn:
            operations = conn.execute("SELECT * FROM Operatie ORDER BY id_operatie").fetchall()
            performances = conn.execute("SELECT * FROM Performanta ORDER BY id_performanta").fetchall()

        self.assertGreaterEqual(len(operations), 2)
        self.assertGreaterEqual(len(performances), 2)
        self.assertEqual(operations[-2]["tip_operatie"], "criptare")
        self.assertEqual(operations[-1]["tip_operatie"], "decriptare")
        self.assertIn(algorithm_name, performances[-2]["observatii"])
        self.assertIn(algorithm_name, performances[-1]["observatii"])
        self.assertGreaterEqual(performances[-2]["timp_executie_ms"], 0)
        self.assertGreaterEqual(performances[-1]["timp_executie_ms"], 0)

    def test_cryptography_aes_gcm_roundtrip(self):
        self._roundtrip(
            algorithm_name="AES-256-GCM",
            framework_id=self.cryptography_framework.id_framework,
            key_name="aes_gcm_pyca_test",
        )

    def test_cryptography_rsa_roundtrip(self):
        self._roundtrip(
            algorithm_name="RSA",
            framework_id=self.cryptography_framework.id_framework,
            key_name="rsa_pyca_test",
        )

    @unittest.skipUnless(_openssl_available.__func__(), "OpenSSL nu este disponibil pe acest sistem")
    def test_openssl_aes_cbc_roundtrip(self):
        self._roundtrip(
            algorithm_name="AES-256-CBC",
            framework_id=self.openssl_framework.id_framework,
            key_name="aes_cbc_openssl_test",
        )

    @unittest.skipUnless(_openssl_available.__func__(), "OpenSSL nu este disponibil pe acest sistem")
    def test_openssl_rsa_hybrid_roundtrip(self):
        self._roundtrip(
            algorithm_name="RSA",
            framework_id=self.openssl_framework.id_framework,
            key_name="rsa_openssl_test",
        )

    @unittest.skipUnless(_openssl_available.__func__(), "OpenSSL nu este disponibil pe acest sistem")
    def test_openssl_does_not_accept_aes_gcm_cli_mode(self):
        algoritm = self.alg_repo.get_by_name("AES-256-GCM")
        key = self.service.make_key(
            algoritm.id_algoritm,
            "aes_gcm_openssl_rejected_test",
            self.openssl_framework.id_framework,
        )
        fisier = self.service.register_file(self.sample_path)

        with self.assertRaises(CryptographyFrameworkError):
            self.service.encrypt_file(
                fisier.id_fisier,
                key.id_cheie,
                algoritm.id_algoritm,
                self.openssl_framework.id_framework,
            )


if __name__ == "__main__":
    unittest.main()
