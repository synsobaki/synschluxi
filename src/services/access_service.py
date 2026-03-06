from __future__ import annotations

import re

KEY_RE = re.compile(r"^UMK-[A-Z0-9]{4}-[A-Z0-9]{4}$")


def normalize_key(key: str) -> str:
    return key.strip().upper()


def validate_key(key: str) -> bool:
    return bool(KEY_RE.match(normalize_key(key)))


def mask_key(key: str) -> str:
    k = normalize_key(key)
    return k[:4] + "****-" + k[-4:]
