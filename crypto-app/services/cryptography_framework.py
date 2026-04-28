from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import hashes, padding as symmetric_padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from config import OPENSSL_PATH
except Exception:
    OPENSSL_PATH = None


class CryptographyFrameworkError(RuntimeError):
    pass


@dataclass(frozen=True)
class CipherDefinition:
    algorithm_name: str
    family: str
    key_size_bytes: int | None = None
    nonce_size_bytes: int = 12
    rsa_key_size_bits: int | None = None


class OpenSSLEngine:
    """Wrapper minimal peste executabilul OpenSSL.

    Important: folosim cheia reală din DB, nu numele cheii ca parolă.
    Pentru AES-CBC folosim -K și -iv, adică raw key + IV.
    """

    def __init__(self, openssl_path: str | None = None):
        self.path = (
            openssl_path
            or OPENSSL_PATH
            or os.environ.get("OPENSSL_PATH")
            or shutil.which("openssl")
            or r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"
        )

    @contextmanager
    def _temp_file(self, data: bytes | None = None):
        fd, name = tempfile.mkstemp()
        os.close(fd)
        path = Path(name)
        if data is not None:
            path.write_bytes(data)
        try:
            yield str(path)
        finally:
            try:
                path.unlink(missing_ok=True)
            except PermissionError:
                pass

    def _call_ssl(self, args: list[str]) -> bytes:
        try:
            result = subprocess.run(
                [self.path] + args,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CryptographyFrameworkError(
                "OpenSSL nu a fost găsit. Instalează OpenSSL sau setează OPENSSL_PATH în config.py."
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise CryptographyFrameworkError(f"Eroare OpenSSL: {stderr or result.returncode}")
        return result.stdout

    def random_bytes(self, size: int) -> bytes:
        data = self._call_ssl(["rand", str(size)])
        if len(data) != size:
            raise CryptographyFrameworkError("OpenSSL nu a generat dimensiunea cerută pentru cheie.")
        return data

    def generate_rsa_key(self, bits: int = 2048) -> bytes:
        with self._temp_file() as private_path:
            self._call_ssl(
                [
                    "genpkey",
                    "-algorithm",
                    "RSA",
                    "-out",
                    private_path,
                    "-pkeyopt",
                    f"rsa_keygen_bits:{bits}",
                ]
            )
            return Path(private_path).read_bytes()

    @staticmethod
    def _openssl_cbc_name(key_material: bytes) -> str:
        if len(key_material) == 16:
            return "aes-128-cbc"
        if len(key_material) == 32:
            return "aes-256-cbc"
        raise CryptographyFrameworkError("Cheie AES-CBC invalidă. Sunt acceptate 16 sau 32 bytes.")

    def encrypt_aes_cbc(self, data: bytes, key_material: bytes) -> tuple[bytes, bytes]:
        iv = self.random_bytes(16)
        cipher_name = self._openssl_cbc_name(key_material)

        with self._temp_file(data) as input_path, self._temp_file() as output_path:
            self._call_ssl(
                [
                    "enc",
                    f"-{cipher_name}",
                    "-e",
                    "-nosalt",
                    "-K",
                    key_material.hex(),
                    "-iv",
                    iv.hex(),
                    "-in",
                    input_path,
                    "-out",
                    output_path,
                ]
            )
            return iv, Path(output_path).read_bytes()

    def decrypt_aes_cbc(self, data: bytes, key_material: bytes, iv: bytes) -> bytes:
        if len(iv) != 16:
            raise CryptographyFrameworkError("IV invalid pentru AES-CBC.")
        cipher_name = self._openssl_cbc_name(key_material)

        with self._temp_file(data) as input_path, self._temp_file() as output_path:
            self._call_ssl(
                [
                    "enc",
                    f"-{cipher_name}",
                    "-d",
                    "-nosalt",
                    "-K",
                    key_material.hex(),
                    "-iv",
                    iv.hex(),
                    "-in",
                    input_path,
                    "-out",
                    output_path,
                ]
            )
            return Path(output_path).read_bytes()

    def _public_key_from_private(self, private_key_pem: bytes) -> bytes:
        with self._temp_file(private_key_pem) as private_path, self._temp_file() as public_path:
            self._call_ssl(["pkey", "-in", private_path, "-pubout", "-out", public_path])
            return Path(public_path).read_bytes()

    def rsa_oaep_encrypt(self, private_key_pem: bytes, data: bytes) -> bytes:
        public_key_pem = self._public_key_from_private(private_key_pem)
        with self._temp_file(public_key_pem) as public_path, self._temp_file(data) as input_path, self._temp_file() as output_path:
            self._call_ssl(
                [
                    "pkeyutl",
                    "-encrypt",
                    "-pubin",
                    "-inkey",
                    public_path,
                    "-in",
                    input_path,
                    "-out",
                    output_path,
                    "-pkeyopt",
                    "rsa_padding_mode:oaep",
                    "-pkeyopt",
                    "rsa_oaep_md:sha256",
                    "-pkeyopt",
                    "rsa_mgf1_md:sha256",
                ]
            )
            return Path(output_path).read_bytes()

    def rsa_oaep_decrypt(self, private_key_pem: bytes, encrypted_data: bytes) -> bytes:
        with self._temp_file(private_key_pem) as private_path, self._temp_file(encrypted_data) as input_path, self._temp_file() as output_path:
            self._call_ssl(
                [
                    "pkeyutl",
                    "-decrypt",
                    "-inkey",
                    private_path,
                    "-in",
                    input_path,
                    "-out",
                    output_path,
                    "-pkeyopt",
                    "rsa_padding_mode:oaep",
                    "-pkeyopt",
                    "rsa_oaep_md:sha256",
                    "-pkeyopt",
                    "rsa_mgf1_md:sha256",
                ]
            )
            return Path(output_path).read_bytes()


class CryptographyFramework:
    _SUPPORTED = {
        "AES-128-GCM": CipherDefinition("AES-128-GCM", family="aesgcm", key_size_bytes=16),
        "AES-256-GCM": CipherDefinition("AES-256-GCM", family="aesgcm", key_size_bytes=32),
        "AES-128-CBC": CipherDefinition("AES-128-CBC", family="aescbc", key_size_bytes=16, nonce_size_bytes=16),
        "AES-256-CBC": CipherDefinition("AES-256-CBC", family="aescbc", key_size_bytes=32, nonce_size_bytes=16),
        "RSA": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP-2048": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
    }

    def __init__(self):
        self._openssl: OpenSSLEngine | None = None

    @property
    def openssl(self) -> OpenSSLEngine:
        if self._openssl is None:
            self._openssl = OpenSSLEngine()
        return self._openssl

    def get_cipher_definition(self, algorithm_name: str) -> CipherDefinition:
        try:
            return self._SUPPORTED[algorithm_name.strip().upper()]
        except KeyError as exc:
            raise CryptographyFrameworkError(f"Algoritmul '{algorithm_name}' nu este suportat.") from exc

    def generate_random_key(self, algorithm_name: str, use_openssl: bool = False) -> bytes:
        cipher = self.get_cipher_definition(algorithm_name)

        if cipher.family in {"aesgcm", "aescbc"}:
            if use_openssl:
                return self.openssl.random_bytes(cipher.key_size_bytes)
            return os.urandom(cipher.key_size_bytes)

        if cipher.family == "rsa_hybrid":
            if use_openssl:
                return self.openssl.generate_rsa_key(cipher.rsa_key_size_bits)
            private_key = rsa.generate_private_key(65537, key_size=cipher.rsa_key_size_bits)
            return private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )

        raise CryptographyFrameworkError(f"Familie neimplementată: {cipher.family}")

    def describe_key_material(self, algorithm_name: str, key_material: bytes) -> tuple[str, int]:
        cipher = self.get_cipher_definition(algorithm_name)

        if cipher.family in {"aesgcm", "aescbc"}:
            if len(key_material) != cipher.key_size_bytes:
                raise CryptographyFrameworkError("Dimensiune cheie invalidă.")
            return "secret", len(key_material) * 8

        try:
            private_key = serialization.load_pem_private_key(key_material, password=None)
            return "privata", private_key.key_size
        except Exception as exc:
            raise CryptographyFrameworkError("Cheie RSA invalidă.") from exc

    def encrypt_bytes(
        self,
        algorithm_name: str,
        key_material: bytes,
        plaintext: bytes,
        use_openssl: bool = False,
        password: str = "",
    ) -> dict[str, bytes]:
        cipher = self.get_cipher_definition(algorithm_name)

        if use_openssl:
            if cipher.family == "aesgcm":
                raise CryptographyFrameworkError(
                    "OpenSSL CLI nu este folosit aici pentru AES-GCM. Pentru OpenSSL selectează AES-128-CBC, AES-256-CBC sau RSA."
                )
            if cipher.family == "aescbc":
                iv, ciphertext = self.openssl.encrypt_aes_cbc(plaintext, key_material)
                return {"mode": b"O", "nonce": iv, "ciphertext": ciphertext, "wrapped_key": b""}
            if cipher.family == "rsa_hybrid":
                session_key = self.openssl.random_bytes(32)
                iv, ciphertext = self.openssl.encrypt_aes_cbc(plaintext, session_key)
                wrapped_key = self.openssl.rsa_oaep_encrypt(key_material, session_key)
                return {"mode": b"S", "nonce": iv, "ciphertext": ciphertext, "wrapped_key": wrapped_key}

        if cipher.family == "aesgcm":
            nonce = os.urandom(cipher.nonce_size_bytes)
            ciphertext = AESGCM(key_material).encrypt(nonce, plaintext, None)
            return {"mode": b"A", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": b""}

        if cipher.family == "aescbc":
            iv, ciphertext = self._encrypt_aes_cbc_pyca(plaintext, key_material)
            return {"mode": b"C", "nonce": iv, "ciphertext": ciphertext, "wrapped_key": b""}

        private_key = serialization.load_pem_private_key(key_material, password=None)
        session_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        ciphertext = AESGCM(session_key).encrypt(nonce, plaintext, None)
        wrapped_key = private_key.public_key().encrypt(
            session_key,
            padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None),
        )
        return {"mode": b"R", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": wrapped_key}

    def decrypt_bytes(
        self,
        algorithm_name: str,
        key_material: bytes,
        nonce: bytes,
        ciphertext: bytes,
        wrapped_key: bytes = b"",
        use_openssl: bool = False,
        password: str = "",
    ) -> bytes:
        cipher = self.get_cipher_definition(algorithm_name)

        if use_openssl:
            if cipher.family == "aesgcm":
                raise CryptographyFrameworkError(
                    "OpenSSL CLI nu este folosit aici pentru AES-GCM. Pentru OpenSSL selectează AES-128-CBC, AES-256-CBC sau RSA."
                )
            if cipher.family == "aescbc":
                return self.openssl.decrypt_aes_cbc(ciphertext, key_material, nonce)
            if cipher.family == "rsa_hybrid":
                session_key = self.openssl.rsa_oaep_decrypt(key_material, wrapped_key)
                return self.openssl.decrypt_aes_cbc(ciphertext, session_key, nonce)

        if cipher.family == "aesgcm":
            return AESGCM(key_material).decrypt(nonce, ciphertext, None)

        if cipher.family == "aescbc":
            return self._decrypt_aes_cbc_pyca(ciphertext, key_material, nonce)

        private_key = serialization.load_pem_private_key(key_material, password=None)
        session_key = private_key.decrypt(
            wrapped_key,
            padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None),
        )
        return AESGCM(session_key).decrypt(nonce, ciphertext, None)

    @staticmethod
    def _encrypt_aes_cbc_pyca(plaintext: bytes, key_material: bytes) -> tuple[bytes, bytes]:
        iv = os.urandom(16)
        padder = symmetric_padding.PKCS7(128).padder()
        padded = padder.update(plaintext) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key_material), modes.CBC(iv)).encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return iv, ciphertext

    @staticmethod
    def _decrypt_aes_cbc_pyca(ciphertext: bytes, key_material: bytes, iv: bytes) -> bytes:
        if len(iv) != 16:
            raise CryptographyFrameworkError("IV invalid pentru AES-CBC.")
        decryptor = Cipher(algorithms.AES(key_material), modes.CBC(iv)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = symmetric_padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
