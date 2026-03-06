from __future__ import annotations

import secrets
import string


def generate_key() -> str:
    """
    Генерит ключ вида UMK-XXXX-XXXX (A-Z, 0-9).
    Используем secrets (криптостойкий), а не random.
    """
    alphabet = string.ascii_uppercase + string.digits
    part1 = "".join(secrets.choice(alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"UMK-{part1}-{part2}"