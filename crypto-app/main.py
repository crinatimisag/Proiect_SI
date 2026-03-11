from config import DB_PATH, SCHEMA_PATH
from database.db_manager import DBManager


def build_context():
    db_manager = DBManager(DB_PATH)
    db_manager.initialize_database(SCHEMA_PATH)

    return {
        'db_manager': db_manager,
    }


def main():
    app_context = build_context()
    print("Tabelele au fost create.")

if __name__ == '__main__':
    main()