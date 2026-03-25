from config import DB_PATH, SCHEMA_PATH
from database.db_manager import DBManager
from ui.gui import CryptoAppUI


def build_context():
    db_manager = DBManager(DB_PATH)
    db_manager.initialize_database(SCHEMA_PATH)

    return {
        'db_manager': db_manager,
    }


def main():
    app_context = build_context()
    print("Tabelele au fost create.")
    app = CryptoAppUI(app_context)
    app.mainloop()

if __name__ == '__main__':
    main()