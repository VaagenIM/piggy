#!/usr/bin/env python3
import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict


SHORTLINK_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SHORTLINK_SIZE = 8
UUID_NAMESPACE = uuid.UUID("8f6f6f6d-6f6f-4f6f-8f6f-6f6f6f6f6f6f")
UUID_RETRY_LIMIT = 10000
_SHORTLINKS_BY_CONFIG: Dict[tuple, Dict[str, str]] = {}
_UUIDS_BY_CONFIG: Dict[tuple, Dict[str, str]] = {}


def _generate_shortlink(identity: str, shortlink_alphabet: str, shortlink_size: int) -> str:
    value = int.from_bytes(
        hashlib.sha256(f"piggy-shortlink-v1:{identity}".encode("utf-8")).digest(),
        "big",
    )
    characters = []
    for _ in range(shortlink_size):
        value, remainder = divmod(value, len(shortlink_alphabet))
        characters.append(shortlink_alphabet[remainder])
    return "".join(characters)


def _read_shortlinks(folder: Path, shortlink_alphabet: str, shortlink_size: int) -> Dict[str, str]:
    shortlinks: Dict[str, str] = {}
    for path in folder.rglob("*.oink"):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        identity = data.get("uuid")
        if identity:
            shortlinks[_generate_shortlink(identity, shortlink_alphabet, shortlink_size)] = str(path)
    return shortlinks


def _identity_from_path(path: Path) -> str:
    filename = path.name
    if filename != "meta.json":
        return filename
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("name") or path.parent.name


def generate_uuid(
    path: str | Path,
    piggybank_folder: str = "piggybank",
    shortlink_alphabet: str = SHORTLINK_ALPHABET,
    shortlink_size: int = SHORTLINK_SIZE,
    uuid_namespace: uuid.UUID = UUID_NAMESPACE,
) -> str:
    if not shortlink_alphabet:
        raise ValueError("shortlink_alphabet must not be empty")
    if len(set(shortlink_alphabet)) != len(shortlink_alphabet):
        raise ValueError("shortlink_alphabet must contain unique characters")
    if shortlink_size < 1:
        raise ValueError("shortlink_size must be positive")
    if UUID_RETRY_LIMIT < 1:
        raise ValueError("UUID_RETRY_LIMIT must be positive")
    path = Path(path)
    oink_path = path.with_suffix(".oink")
    if oink_path.is_file():
        with oink_path.open("r", encoding="utf-8") as handle:
            existing_uuid = json.load(handle).get("uuid")
        if existing_uuid:
            return existing_uuid
    identity = _identity_from_path(path)
    base_identity = identity
    folder = Path(piggybank_folder).resolve()
    config = (folder, shortlink_alphabet, shortlink_size, uuid_namespace)
    shortlinks = _SHORTLINKS_BY_CONFIG.setdefault(config, _read_shortlinks(folder, shortlink_alphabet, shortlink_size))
    generated = _UUIDS_BY_CONFIG.setdefault(config, {})
    if identity in generated:
        return generated[identity]
    for attempt in range(UUID_RETRY_LIMIT):
        seed = identity if attempt == 0 else f"{identity}+{attempt}"
        candidate = str(uuid.uuid5(uuid_namespace, seed))
        shortlink = _generate_shortlink(candidate, shortlink_alphabet, shortlink_size)
        if shortlink not in shortlinks:
            shortlinks[shortlink] = path
            generated[base_identity] = candidate
            return candidate
    conflict = shortlinks.get(shortlink, "unknown page")
    raise RuntimeError(
        f"Unable to generate a unique UUID for {path}; " f"shortlink {shortlink} is already used by {conflict}"
    )
