import sqlite3
from pathlib import Path


class DBManager:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self, schema_path: str | Path):
        with self.get_connection() as conn:
            with open(schema_path, 'r', encoding='utf-8') as schema_file:
                conn.executescript(schema_file.read())
