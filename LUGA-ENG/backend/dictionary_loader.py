import csv
import json
from pathlib import Path

from translations import PHRASES

DATA_DIR = Path(__file__).parent
DICTIONARY_PATH = DATA_DIR / "dictionary_data.json"
LEGACY_DICTIONARY_PATH = DATA_DIR / "luganda-dictionary.json"
CACHE_PATH = DATA_DIR / "translation_cache.json"


def normalize_key(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _read_json(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        normalize_key(str(luganda)): str(english).strip()
        for luganda, english in data.items()
        if str(luganda).strip() and str(english).strip()
    }


def load_dictionary() -> dict[str, str]:
    dictionary = {normalize_key(
        luganda): english for luganda, english in PHRASES.items()}
    dictionary.update(_read_json(LEGACY_DICTIONARY_PATH))
    dictionary.update(_read_json(DICTIONARY_PATH))
    dictionary.update(_read_json(CACHE_PATH))
    return dictionary


def save_translation(luganda: str, english: str) -> None:
    entries = _read_json(CACHE_PATH)
    entries[normalize_key(luganda)] = english.strip()
    with CACHE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False,
                  indent=2, sort_keys=True)


def import_csv(csv_path: str) -> int:
    imported = _read_json(DICTIONARY_PATH)
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"luganda", "english"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must contain luganda and english columns")
        for row in reader:
            luganda = normalize_key(row.get("luganda", ""))
            english = row.get("english", "").strip()
            if luganda and english:
                imported[luganda] = english

    with DICTIONARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(imported, handle, ensure_ascii=False,
                  indent=2, sort_keys=True)
    return len(imported)
