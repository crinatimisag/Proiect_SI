from config import DB_PATH, DEFAULT_ALGORITHMS, FRAMEWORK_NAME, SCHEMA_PATH
from database.db_manager import DBManager
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.framework_repository import FrameworkRepository
from models.algoritm import Algoritm
from models.framework_model import FrameworkModel
from ui.gui import CryptoAppUI


def build_context():
    db_manager = DBManager(DB_PATH)
    db_manager.initialize_database(SCHEMA_PATH)
    seed_reference_data(db_manager)
    return {"db_manager": db_manager}


def seed_reference_data(db_manager: DBManager) -> None:
    alg_repo = AlgoritmRepository(db_manager)
    framework_repo = FrameworkRepository(db_manager)

    for algorithm_name, tip in DEFAULT_ALGORITHMS:
        if not alg_repo.get_by_name(algorithm_name):
            alg_repo.insert(Algoritm(None, algorithm_name, tip))

    existing_framework = framework_repo.get_by_name(FRAMEWORK_NAME)
    if not existing_framework:
        framework_repo.insert(
            FrameworkModel(None, FRAMEWORK_NAME, "cryptography / AESGCM + RSA-OAEP", "Python")
        )


def main():
    app_context = build_context()
    print("Baza de date este pregătită. Pornesc interfața.")
    app = CryptoAppUI(app_context)
    app.mainloop()


if __name__ == "__main__":
    main()