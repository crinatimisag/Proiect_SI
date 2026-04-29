from __future__ import annotations

import hashlib
import shutil
import struct
import os
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

    def make_key(self, algorithm_id: int, key_name: str | None = None, framework_id: int | None = None) -> Cheie:
        algoritm = self._require_algorithm(algorithm_id)
        use_ssl, use_pycryptodome = self._framework_flags(framework_id)

        key_bytes = self.framework.generate_random_key(
            algoritm.nume,
            use_openssl=use_ssl,
            use_pycryptodome=use_pycryptodome
        )
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
        return self.cheie_repo.get_by_id(key_id)

    def encrypt_file(self, file_id: int, key_id: int, algorithm_id: int, framework_id: int) -> dict:
        fisier = self._require_file(file_id)
        cheie = self._require_key(key_id)
        algoritm = self._require_algorithm(algorithm_id)
        fr = self.framework_repo.get_by_id(framework_id)
        
        use_ssl, use_pycryptodome = self._framework_flags(framework_id)
        key_bytes = self._validate_key_for_algorithm(cheie, algoritm.id_algoritm, algoritm.nume)

        input_path = Path(fisier.cale_fisier)
        plaintext = input_path.read_bytes()

        memory_before = self._current_memory_kb()
        started = perf_counter()
        
        enc_res = self.framework.encrypt_bytes(
            algoritm.nume, 
            key_bytes, 
            plaintext, 
            use_openssl=use_ssl,
            use_pycryptodome=use_pycryptodome,
            password=cheie.nume_cheie
        )
        
        elapsed_ms = (perf_counter() - started) * 1000.0
        memory_after = self._current_memory_kb()

        payload = self._pack_payload(
            enc_res["mode"],
            enc_res["nonce"],
            enc_res["ciphertext"],
            enc_res["wrapped_key"],
        )
        
        output_path = self._unique_path(ENCRYPTED_DIR / f"{input_path.name}.enc")
        output_path.write_bytes(payload)

        output_record = self._insert_file_record(output_path, status="criptat")
        operatie_id = self._save_operation(
            source_file=fisier,
            key=cheie,
            algorithm_id=algoritm.id_algoritm,
            framework_id=framework_id,
            operation_type="criptare",
            output_path=output_path,
            elapsed_ms=elapsed_ms,
            memory_before=memory_before,
            memory_after=memory_after,
            input_size=len(plaintext),
            observation=f"{fr.nume} / {algoritm.nume}",
        )
        
        return {"operation_id": operatie_id, "output_file": output_record, "elapsed_ms": elapsed_ms}

    def decrypt_file(self, file_id: int, key_id: int, algorithm_id: int, framework_id: int) -> dict:
        fisier = self._require_file(file_id)
        cheie = self._require_key(key_id)
        algoritm = self._require_algorithm(algorithm_id)
        fr = self.framework_repo.get_by_id(framework_id)
        
        use_ssl, use_pycryptodome = self._framework_flags(framework_id)
        key_bytes = self._validate_key_for_algorithm(cheie, algoritm.id_algoritm, algoritm.nume)

        input_path = Path(fisier.cale_fisier)
        mode, nonce, ciphertext, wrapped_key = self._unpack_payload(input_path.read_bytes())

        memory_before = self._current_memory_kb()
        started = perf_counter()
        
        plaintext = self.framework.decrypt_bytes(
            algoritm.nume, 
            key_bytes, 
            nonce, 
            ciphertext, 
            wrapped_key, 
            use_openssl=use_ssl,
            use_pycryptodome=use_pycryptodome,
            password=cheie.nume_cheie
        )
        
        elapsed_ms = (perf_counter() - started) * 1000.0
        memory_after = self._current_memory_kb()

        output_path = self._unique_path(self._build_decrypted_path(input_path.name))
        output_path.write_bytes(plaintext)

        output_record = self._insert_file_record(output_path, status="decriptat")
        operatie_id = self._save_operation(
            source_file=fisier,
            key=cheie,
            algorithm_id=algoritm.id_algoritm,
            framework_id=framework_id,
            operation_type="decriptare",
            output_path=output_path,
            elapsed_ms=elapsed_ms,
            memory_before=memory_before,
            memory_after=memory_after,
            input_size=len(ciphertext),
            observation=f"{fr.nume} / {algoritm.nume}",
        )
        
        return {"operation_id": operatie_id, "output_file": output_record, "elapsed_ms": elapsed_ms}

    def _framework_flags(self, framework_id: int | None) -> tuple[bool, bool]:
        fr = self.framework_repo.get_by_id(framework_id) if framework_id else None
        nume_frame = fr.nume.lower() if fr else ""
        return "openssl" in nume_frame, "pycryptodome" in nume_frame

    def _save_operation(self, source_file, key, algorithm_id, framework_id, operation_type, output_path, elapsed_ms, memory_before, memory_after, input_size, observation) -> int:
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
        return self.fisier_repo.get_by_id(file_id)

    def _validate_key_for_algorithm(self, cheie: Cheie, algorithm_id: int, algorithm_name: str) -> bytes:
        if cheie.id_algoritm != algorithm_id:
            raise CryptoServiceError("Cheia selectată nu aparține algoritmului ales.")
        return bytes.fromhex(cheie.valoare_cheie_hex)

    def _require_file(self, file_id: int):
        f = self.fisier_repo.get_by_id(file_id)
        if not f: raise CryptoServiceError("Fișier inexistent.")
        return f

    def _require_key(self, key_id: int):
        k = self.cheie_repo.get_by_id(key_id)
        if not k: raise CryptoServiceError("Cheie inexistentă.")
        return k

    def _require_algorithm(self, algorithm_id: int):
        a = self.alg_repo.get_by_id(algorithm_id)
        if not a: raise CryptoServiceError("Algoritm inexistent.")
        return a

    def _pack_payload(self, mode: bytes, nonce: bytes, ciphertext: bytes, wrapped_key: bytes) -> bytes:
        return b"".join([
            self.FILE_MAGIC,
            mode,
            struct.pack(">I", len(wrapped_key)),
            wrapped_key,
            struct.pack("B", len(nonce)),
            nonce,
            ciphertext
        ])

    def _unpack_payload(self, payload: bytes) -> tuple[bytes, bytes, bytes, bytes]:
        cursor = len(self.FILE_MAGIC)
        if not payload.startswith(self.FILE_MAGIC):
            raise CryptoServiceError("Header invalid.")
        mode = payload[cursor:cursor + 1]
        cursor += 1
        wrapped_len = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        cursor += 4
        wrapped_key = payload[cursor:cursor + wrapped_len]
        cursor += wrapped_len
        nonce_len = payload[cursor]
        cursor += 1
        nonce = payload[cursor:cursor + nonce_len]
        cursor += nonce_len
        ciphertext = payload[cursor:]
        return mode, nonce, ciphertext, wrapped_key

    def _build_decrypted_path(self, name: str) -> Path:
        p = Path(name)
        new_name = p.stem.replace(".enc", "") + "_decrypted" + p.suffix.replace(".enc", "")
        return DECRYPTED_DIR / new_name

    def _sha256_file(self, path: Path) -> str:
        sha = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def _unique_path(self, path: Path) -> Path:
        if not path.exists(): return path
        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists(): return candidate
            counter += 1

    def _current_memory_kb(self) -> float:
        if psutil is None: return 0.0
        return psutil.Process().memory_info().rss / 1024.0