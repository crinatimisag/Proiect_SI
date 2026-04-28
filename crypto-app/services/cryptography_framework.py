from __future__ import annotations
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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
    def __init__(self, openssl_path: str = r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"):
        self.path = openssl_path

    def _call_ssl(self, args: list[str]) -> bytes:
        try:
            result = subprocess.run([self.path] + args, capture_output=True, check=True)
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise CryptographyFrameworkError(f"Eroare OpenSSL: {str(exc)}")

    def generate_rsa_key(self, bits: int = 2048) -> bytes:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            self._call_ssl(["genpkey", "-algorithm", "RSA", "-out", tmp_path, "-pkeyopt", f"rsa_keygen_bits:{bits}"])
            return Path(tmp_path).read_bytes()
        finally:
            if os.path.exists(tmp_path): os.unlink(tmp_path)

    def encrypt_aes_cbc(self, data: bytes, password: str) -> bytes:
        f_in, f_out = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
        try:
            f_in.write(data)
            f_in.close()
            f_out.close()
            self._call_ssl(["enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-in", f_in.name, "-out", f_out.name, "-pass", f"pass:{password}"])
            return Path(f_out.name).read_bytes()
        finally:
            for f in [f_in, f_out]:
                if os.path.exists(f.name): os.unlink(f.name)

    def decrypt_aes_cbc(self, data: bytes, password: str) -> bytes:
        f_in, f_out = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
        try:
            f_in.write(data)
            f_in.close()
            f_out.close()
            self._call_ssl(["enc", "-aes-256-cbc", "-d", "-pbkdf2", "-in", f_in.name, "-out", f_out.name, "-pass", f"pass:{password}"])
            return Path(f_out.name).read_bytes()
        finally:
            for f in [f_in, f_out]:
                if os.path.exists(f.name): os.unlink(f.name)

class CryptographyFramework:
    _SUPPORTED = {
        "AES-128-GCM": CipherDefinition("AES-128-GCM", family="aesgcm", key_size_bytes=16),
        "AES-256-GCM": CipherDefinition("AES-256-GCM", family="aesgcm", key_size_bytes=32),
        "RSA": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP-2048": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
    }

    def __init__(self):
        self.openssl = OpenSSLEngine()

    def get_cipher_definition(self, algorithm_name: str) -> CipherDefinition:
        try:
            return self._SUPPORTED[algorithm_name.strip().upper()]
        except KeyError as exc:
            raise CryptographyFrameworkError(f"Algoritmul '{algorithm_name}' nu este suportat.") from exc

    def generate_random_key(self, algorithm_name: str, use_openssl: bool = False) -> bytes:
        cipher = self.get_cipher_definition(algorithm_name)
        if use_openssl and cipher.family == "rsa_hybrid":
            return self.openssl.generate_rsa_key(cipher.rsa_key_size_bits)
        if cipher.family == "aesgcm":
            return AESGCM.generate_key(bit_length=cipher.key_size_bytes * 8)
        if cipher.family == "rsa_hybrid":
            private_key = rsa.generate_private_key(65537, key_size=cipher.rsa_key_size_bits)
            return private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        raise CryptographyFrameworkError(f"Familie neimplementată: {cipher.family}")

    def describe_key_material(self, algorithm_name: str, key_material: bytes) -> tuple[str, int]:
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            if len(key_material) != cipher.key_size_bytes: raise CryptographyFrameworkError("Dimensiune cheie invalidă.")
            return "secret", len(key_material)
        try:
            private_key = serialization.load_pem_private_key(key_material, password=None)
            return "privata", private_key.key_size
        except Exception:
            raise CryptographyFrameworkError("Cheie RSA invalidă.")

    def encrypt_bytes(self, algorithm_name: str, key_material: bytes, plaintext: bytes, use_openssl: bool = False, password: str = "") -> dict[str, bytes]:
        if use_openssl:
            ciphertext = self.openssl.encrypt_aes_cbc(plaintext, password)
            return {"mode": b"O", "nonce": b"", "ciphertext": ciphertext, "wrapped_key": b""}
        
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            nonce = os.urandom(cipher.nonce_size_bytes)
            ciphertext = AESGCM(key_material).encrypt(nonce, plaintext, None)
            return {"mode": b"A", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": b""}

        private_key = serialization.load_pem_private_key(key_material, password=None)
        session_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        ciphertext = AESGCM(session_key).encrypt(nonce, plaintext, None)
        wrapped_key = private_key.public_key().encrypt(session_key, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
        return {"mode": b"R", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": wrapped_key}

    def decrypt_bytes(self, algorithm_name: str, key_material: bytes, nonce: bytes, ciphertext: bytes, wrapped_key: bytes = b"", use_openssl: bool = False, password: str = "") -> bytes:
        if use_openssl:
            return self.openssl.decrypt_aes_cbc(ciphertext, password)
        
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            return AESGCM(key_material).decrypt(nonce, ciphertext, None)
        
        private_key = serialization.load_pem_private_key(key_material, password=None)
        session_key = private_key.decrypt(wrapped_key, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
        return AESGCM(session_key).decrypt(nonce, ciphertext, None)