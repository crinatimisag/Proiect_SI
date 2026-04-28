from pathlib import Path
import os
import shutil

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "crypto_app.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
KEYS_DIR = BASE_DIR / "keys"
FILES_DIR = BASE_DIR / "files"
ENCRYPTED_DIR = BASE_DIR / "encrypted"
DECRYPTED_DIR = BASE_DIR / "decrypted"
FRAMEWORK_NAME = "cryptography"


OPENSSL_PATH = os.environ.get("OPENSSL_PATH") or shutil.which("openssl") or r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"

DEFAULT_ALGORITHMS = [
    ("AES-128-GCM", "simetric"),
    ("AES-256-GCM", "simetric"),
    ("AES-128-CBC", "simetric"),
    ("AES-256-CBC", "simetric"),
    ("RSA", "asimetric"),
]

for path in (KEYS_DIR, FILES_DIR, ENCRYPTED_DIR, DECRYPTED_DIR):
    path.mkdir(parents=True, exist_ok=True)
