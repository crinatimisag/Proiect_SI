from __future__ import annotations

import hashlib
import shutil
import struct
from datetime import datetime
from pathlib import Path
from time import perf_counter

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

from config import DECRYPTED_DIR, ENCRYPTED_DIR, FILES_DIR, FRAMEWORK_NAME
from database.repositories.algoritm_repository import AlgoritmRepository
from database.repositories.cheie_repository import CheieRepository
from database.repositories.fisier_repository import FisierRepository
from database.repositories.framework_repository import FrameworkRepository
from database.repositories.operatie_repository import OperatieRepository
from database.repositories.performanta_repository import PerformantaRepository
from models.cheie import Cheie
from models.fisier import Fisier
from models.operatie import Operatie
from models.performanta import Performanta
from services.cryptography_framework import CryptographyFramework, CryptographyFrameworkError


class CryptoServiceError(RuntimeError):
    pass


class CryptoService:
    FILE_MAGIC = b"CAPP03"

    def __init__(self, db_manager) -> None:
        self.db_manager = db_manager
        self.alg_repo = AlgoritmRepository(db_manager)
        self.cheie_repo = CheieRepository(db_manager)
        self.fisier_repo = FisierRepository(db_manager)
        self.framework_repo = FrameworkRepository(db_manager)
        self.operatie_repo = OperatieRepository(db_manager)
        self.perf_repo = PerformantaRepository(db_manager)
        self.framework = CryptographyFramework()

    def register_file(self, source_path: str | Path) -> Fisier:
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise CryptoServiceError(f"Fișierul '{source}' nu există.")

        destination = self._unique_path(FILES_DIR / source.name)
        shutil.copy2(source, destination)
        return self._insert_file_record(destination, status="importat")

    def generate_key_for_algorithm(self, algorithm_id: int, key_name: str | None = None) -> Cheie:
        algoritm = self._require_algorithm(algorithm_id)
        key_bytes = self.framework.generate_random_key(algoritm.nume)
        key_type, key_dimension = self.framework.describe_key_material(algoritm.nume, key_bytes)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_name = key_name.strip() if key_name and key_name.strip() else f"{algoritm.nume}-key-{timestamp}"

        cheie = Cheie(
            id_cheie=None,
            id_algoritm=algorithm_id,
            nume_cheie=final_name,
            tip_cheie=key_type,
            dimensiune_cheie=key_dimension,
            locatie_cheie="DB",
            valoare_cheie_hex=key_bytes.hex().upper(),
            data_creare=datetime.now().isoformat(timespec="seconds"),
            status="activa",
        )
        key_id = self.cheie_repo.insert(cheie)
        stored = self.cheie_repo.get_by_id(key_id)
        if not stored:
            raise CryptoServiceError("Cheia generată nu a putut fi citită după salvare.")
        return stored

    def encrypt_file(self, file_id: int, key_id: int, algorithm_id: int) -> dict:
        fisier = self._require_file(file_id)
        cheie = self._require_key(key_id)
        algoritm = self._require_algorithm(algorithm_id)
        key_bytes = self._validate_key_for_algorithm(cheie, algoritm.id_algoritm, algoritm.nume)

        input_path = Path(fisier.cale_fisier)
        if not input_path.exists():
            raise CryptoServiceError(f"Fișierul sursă nu mai există pe disc: {input_path}")

        plaintext = input_path.read_bytes()
        memory_before = self._current_memory_kb()
        started = perf_counter()
        encrypted_parts = self.framework.encrypt_bytes(algoritm.nume, key_bytes, plaintext)
        elapsed_ms = (perf_counter() - started) * 1000.0
        memory_after = self._current_memory_kb()

        payload = self._pack_payload(
            encrypted_parts["mode"],
            encrypted_parts["nonce"],
            encrypted_parts["ciphertext"],
            encrypted_parts["wrapped_key"],
        )
        output_path = self._unique_path(ENCRYPTED_DIR / f"{input_path.name}.enc")
        output_path.write_bytes(payload)

        output_record = self._insert_file_record(output_path, status="criptat")
        operatie_id = self._save_operation(
            source_file=fisier,
            key=cheie,
            algorithm_id=algoritm.id_algoritm,
            operation_type="criptare",
            output_path=output_path,
            elapsed_ms=elapsed_ms,
            memory_before=memory_before,
            memory_after=memory_after,
            input_size=len(plaintext),
            observation=f"cryptography / {algoritm.nume}",
        )
        return {"operation_id": operatie_id, "output_file": output_record, "elapsed_ms": elapsed_ms}

    def decrypt_file(self, file_id: int, key_id: int, algorithm_id: int) -> dict:
        fisier = self._require_file(file_id)
        cheie = self._require_key(key_id)
        algoritm = self._require_algorithm(algorithm_id)
        key_bytes = self._validate_key_for_algorithm(cheie, algoritm.id_algoritm, algoritm.nume)

        input_path = Path(fisier.cale_fisier)
        if not input_path.exists():
            raise CryptoServiceError(f"Fișierul selectat nu mai există pe disc: {input_path}")

        mode, nonce, ciphertext, wrapped_key = self._unpack_payload(input_path.read_bytes())
        definition = self.framework.get_cipher_definition(algoritm.nume)
        expected_mode = b"A" if definition.family == "aesgcm" else b"R"
        if mode != expected_mode:
            raise CryptoServiceError(
                "Fișierul criptat nu corespunde algoritmului selectat pentru decriptare."
            )

        memory_before = self._current_memory_kb()
        started = perf_counter()
        plaintext = self.framework.decrypt_bytes(algoritm.nume, key_bytes, nonce, ciphertext, wrapped_key)
        elapsed_ms = (perf_counter() - started) * 1000.0
        memory_after = self._current_memory_kb()

        output_path = self._build_decrypted_path(input_path.name)
        output_path = self._unique_path(output_path)
        output_path.write_bytes(plaintext)

        output_record = self._insert_file_record(output_path, status="decriptat")
        operatie_id = self._save_operation(
            source_file=fisier,
            key=cheie,
            algorithm_id=algoritm.id_algoritm,
            operation_type="decriptare",
            output_path=output_path,
            elapsed_ms=elapsed_ms,
            memory_before=memory_before,
            memory_after=memory_after,
            input_size=len(ciphertext),
            observation=f"cryptography / {algoritm.nume}",
        )
        return {"operation_id": operatie_id, "output_file": output_record, "elapsed_ms": elapsed_ms}

    def _save_operation(
        self,
        source_file: Fisier,
        key: Cheie,
        algorithm_id: int,
        operation_type: str,
        output_path: Path,
        elapsed_ms: float,
        memory_before: float,
        memory_after: float,
        input_size: int,
        observation: str,
    ) -> int:
        framework_id = self._get_framework_id()
        operatie = Operatie(
            id_operatie=None,
            id_fisier=source_file.id_fisier,
            id_cheie=key.id_cheie,
            id_algoritm=algorithm_id,
            id_framework=framework_id,
            tip_operatie=operation_type,
            data_executie=datetime.now().isoformat(timespec="seconds"),
            status="succes",
            fisier_rezultat=str(output_path),
            hash_rezultat=self._sha256_file(output_path),
        )
        operatie_id = self.operatie_repo.insert(operatie)
        self.perf_repo.insert(
            Performanta(
                id_performanta=None,
                id_operatie=operatie_id,
                timp_executie_ms=elapsed_ms,
                memorie_kb=max(memory_after - memory_before, 0.0),
                dimensiune_input=input_size,
                observatii=observation,
            )
        )
        return operatie_id

    def _get_framework_id(self) -> int:
        framework = self.framework_repo.get_by_name(FRAMEWORK_NAME)
        if not framework:
            raise CryptoServiceError(f"Framework-ul '{FRAMEWORK_NAME}' nu este configurat în baza de date.")
        return framework.id_framework

    def _insert_file_record(self, path: Path, status: str) -> Fisier:
        fisier = Fisier(
            id_fisier=None,
            nume_fisier=path.name,
            cale_fisier=str(path),
            hash_initial=self._sha256_file(path),
            dimensiune=path.stat().st_size,
            data_adaugare=datetime.now().isoformat(timespec="seconds"),
            status=status,
        )
        file_id = self.fisier_repo.insert(fisier)
        stored = self.fisier_repo.get_by_id(file_id)
        if not stored:
            raise CryptoServiceError("Fișierul salvat în DB nu a putut fi recitit.")
        return stored

    def _build_decrypted_path(self, encrypted_name: str) -> Path:
        encrypted_path = Path(encrypted_name)
        if encrypted_path.suffix == ".enc":
            original_name = encrypted_path.stem
            original_path = Path(original_name)
            suffix = original_path.suffix
            stem = original_path.stem if suffix else original_path.name
            filename = f"{stem}_decrypted{suffix}"
        else:
            filename = f"{encrypted_path.stem}_decrypted{encrypted_path.suffix}"
        return DECRYPTED_DIR / filename

    def _validate_key_for_algorithm(self, cheie: Cheie, algorithm_id: int, algorithm_name: str) -> bytes:
        if cheie.id_algoritm != algorithm_id:
            raise CryptoServiceError("Cheia selectată nu aparține algoritmului ales.")
        key_bytes = self._hex_to_bytes(cheie.valoare_cheie_hex, "cheia")
        try:
            key_type, key_dimension = self.framework.describe_key_material(algorithm_name, key_bytes)
        except CryptographyFrameworkError as exc:
            raise CryptoServiceError(str(exc)) from exc
        if cheie.tip_cheie and cheie.tip_cheie.strip().lower() not in {key_type, key_type.lower()}:
            raise CryptoServiceError(
                f"Tipul cheii din DB este '{cheie.tip_cheie}', dar algoritmul {algorithm_name} cere '{key_type}'."
            )
        if cheie.dimensiune_cheie != key_dimension:
            raise CryptoServiceError(
                f"Cheia selectată are dimensiunea {cheie.dimensiune_cheie}, dar materialul real indică {key_dimension}."
            )
        return key_bytes

    def _require_file(self, file_id: int):
        fisier = self.fisier_repo.get_by_id(file_id)
        if not fisier:
            raise CryptoServiceError("Fișierul selectat nu există în baza de date.")
        return fisier

    def _require_key(self, key_id: int):
        cheie = self.cheie_repo.get_by_id(key_id)
        if not cheie:
            raise CryptoServiceError("Cheia selectată nu există în baza de date.")
        if not cheie.valoare_cheie_hex:
            raise CryptoServiceError("Cheia selectată nu are valoare salvată în DB.")
        return cheie

    def _require_algorithm(self, algorithm_id: int):
        algoritm = self.alg_repo.get_by_id(algorithm_id)
        if not algoritm:
            raise CryptoServiceError("Algoritmul selectat nu există în baza de date.")
        self.framework.get_cipher_definition(algoritm.nume)
        return algoritm

    @staticmethod
    def _hex_to_bytes(value: str, label: str) -> bytes:
        normalized = "".join(value.strip().split())
        if not normalized:
            raise CryptoServiceError(f"Valoarea pentru {label} este goală.")
        try:
            return bytes.fromhex(normalized)
        except ValueError as exc:
            raise CryptoServiceError(f"Valoarea hex pentru {label} este invalidă.") from exc

    @staticmethod
    def _pack_payload(mode: bytes, nonce: bytes, ciphertext: bytes, wrapped_key: bytes) -> bytes:
        if len(mode) != 1:
            raise CryptoServiceError("Marker-ul de mod trebuie să aibă exact 1 byte.")
        return b"".join(
            [
                CryptoService.FILE_MAGIC,
                mode,
                struct.pack(">I", len(wrapped_key)),
                wrapped_key,
                struct.pack("B", len(nonce)),
                nonce,
                ciphertext,
            ]
        )

    @staticmethod
    def _unpack_payload(payload: bytes) -> tuple[bytes, bytes, bytes, bytes]:
        min_length = len(CryptoService.FILE_MAGIC) + 1 + 4 + 1
        if len(payload) < min_length or not payload.startswith(CryptoService.FILE_MAGIC):
            raise CryptoServiceError("Fișierul selectat nu are antetul așteptat pentru decriptare.")
        cursor = len(CryptoService.FILE_MAGIC)
        mode = payload[cursor:cursor + 1]
        cursor += 1
        wrapped_length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        cursor += 4
        wrapped_key = payload[cursor:cursor + wrapped_length]
        cursor += wrapped_length
        if cursor >= len(payload):
            raise CryptoServiceError("Fișierul criptat este incomplet sau corupt.")
        nonce_length = payload[cursor]
        cursor += 1
        nonce = payload[cursor:cursor + nonce_length]
        cursor += nonce_length
        ciphertext = payload[cursor:]
        if not nonce or not ciphertext:
            raise CryptoServiceError("Fișierul criptat este incomplet sau corupt.")
        return mode, nonce, ciphertext, wrapped_key

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _current_memory_kb() -> float:
        if psutil is None:
            return 0.0
        try:
            return psutil.Process().memory_info().rss / 1024.0
        except Exception:
            return 0.0
