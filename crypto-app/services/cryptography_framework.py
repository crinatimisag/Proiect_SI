from __future__ import annotations

import os
from dataclasses import dataclass

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


class CryptographyFramework:
    _SUPPORTED = {
        "AES-128-GCM": CipherDefinition("AES-128-GCM", family="aesgcm", key_size_bytes=16),
        "AES-256-GCM": CipherDefinition("AES-256-GCM", family="aesgcm", key_size_bytes=32),
        "RSA": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
        "RSA-OAEP-2048": CipherDefinition("RSA", family="rsa_hybrid", rsa_key_size_bits=2048),
    }

    def get_cipher_definition(self, algorithm_name: str) -> CipherDefinition:
        try:
            return self._SUPPORTED[algorithm_name.strip().upper()]
        except KeyError as exc:
            raise CryptographyFrameworkError(
                f"Algoritmul '{algorithm_name}' nu este suportat de biblioteca cryptography."
            ) from exc

    def generate_random_key(self, algorithm_name: str) -> bytes:
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            return AESGCM.generate_key(bit_length=cipher.key_size_bytes * 8)
        if cipher.family == "rsa_hybrid":
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=cipher.rsa_key_size_bits)
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        raise CryptographyFrameworkError(f"Familie de algoritm neimplementată: {cipher.family}")

    def describe_key_material(self, algorithm_name: str, key_material: bytes) -> tuple[str, int]:
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            self._validate_aes_key_length(key_material, cipher)
            return "secret", len(key_material)
        private_key = self._load_rsa_private_key(key_material)
        return "privata", private_key.key_size

    def encrypt_bytes(self, algorithm_name: str, key_material: bytes, plaintext: bytes) -> dict[str, bytes]:
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            self._validate_aes_key_length(key_material, cipher)
            nonce = os.urandom(cipher.nonce_size_bytes)
            aesgcm = AESGCM(key_material)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            return {"mode": b"A", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": b""}

        private_key = self._load_rsa_private_key(key_material)
        public_key = private_key.public_key()
        session_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        ciphertext = AESGCM(session_key).encrypt(nonce, plaintext, None)
        wrapped_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return {"mode": b"R", "nonce": nonce, "ciphertext": ciphertext, "wrapped_key": wrapped_key}

    def decrypt_bytes(
        self,
        algorithm_name: str,
        key_material: bytes,
        nonce: bytes,
        ciphertext: bytes,
        wrapped_key: bytes = b"",
    ) -> bytes:
        cipher = self.get_cipher_definition(algorithm_name)
        if cipher.family == "aesgcm":
            self._validate_aes_key_length(key_material, cipher)
            if len(nonce) != cipher.nonce_size_bytes:
                raise CryptographyFrameworkError(
                    f"Nonce invalid: așteptat {cipher.nonce_size_bytes} bytes, primit {len(nonce)}."
                )
            try:
                return AESGCM(key_material).decrypt(nonce, ciphertext, None)
            except InvalidTag as exc:
                raise CryptographyFrameworkError(
                    "Decriptarea AES-GCM a eșuat: cheia este greșită sau fișierul criptat a fost modificat."
                ) from exc

        if not wrapped_key:
            raise CryptographyFrameworkError("Fișierul criptat RSA nu conține cheia de sesiune învelită.")
        private_key = self._load_rsa_private_key(key_material)
        try:
            session_key = private_key.decrypt(
                wrapped_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except ValueError as exc:
            raise CryptographyFrameworkError(
                "Decriptarea RSA a cheii de sesiune a eșuat. Verifică dacă ai ales cheia corectă."
            ) from exc

        try:
            return AESGCM(session_key).decrypt(nonce, ciphertext, None)
        except InvalidTag as exc:
            raise CryptographyFrameworkError(
                "Decriptarea fișierului a eșuat: cheia RSA este greșită sau fișierul a fost modificat."
            ) from exc

    @staticmethod
    def _validate_aes_key_length(key: bytes, cipher: CipherDefinition) -> None:
        if len(key) != cipher.key_size_bytes:
            raise CryptographyFrameworkError(
                f"Cheie invalidă pentru {cipher.algorithm_name}: trebuie {cipher.key_size_bytes} bytes."
            )

    @staticmethod
    def _load_rsa_private_key(key_material: bytes):
        try:
            private_key = serialization.load_pem_private_key(key_material, password=None)
        except ValueError as exc:
            raise CryptographyFrameworkError("Valoarea cheii RSA din DB nu reprezintă o cheie privată PEM validă.") from exc
        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise CryptographyFrameworkError("Cheia salvată nu este o cheie RSA privată validă.")
        return private_key
