from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "crypto_app.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
KEYS_DIR = BASE_DIR / "keys"
FILES_DIR = BASE_DIR / "files"
ENCRYPTED_DIR = BASE_DIR / "encrypted"
DECRYPTED_DIR = BASE_DIR / "decrypted"

for path in (KEYS_DIR, FILES_DIR, ENCRYPTED_DIR, DECRYPTED_DIR):
    path.mkdir(parents=True, exist_ok=True)
