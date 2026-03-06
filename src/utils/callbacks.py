from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Act(str, Enum):
    MENU = "m"
    PROF = "p"
    KEY = "k"
    BACK = "b"

    NEW = "n"
    ARCH = "a"

    CONT = "c"       # продолжить тему (topic_id)
    TOPIC = "t"      # открыть карточку темы (topic_id)
    FMT = "f"        # выбрать формат (topic_id, fmt)


@dataclass(frozen=True)
class CB:
    act: Act
    p1: str = ""
    p2: str = ""


def pack(act: Act, p1: str | int | None = None, p2: str | int | None = None) -> str:
    s1 = "" if p1 is None else str(p1)
    s2 = "" if p2 is None else str(p2)
    data = f"{act.value}:{s1}:{s2}"
    # Telegram limit 64 bytes for callback_data
    if len(data.encode("utf-8")) > 64:
        raise ValueError(f"callback_data too long: {data}")
    return data


def unpack(data: str | None) -> CB | None:
    if not data:
        return None
    parts = data.split(":", 2)
    if len(parts) != 3:
        return None
    a, p1, p2 = parts
    try:
        act = Act(a)
    except Exception:
        return None
    return CB(act=act, p1=p1, p2=p2)


def to_int(s: str, default: int | None = None) -> int | None:
    try:
        return int(s)
    except Exception:
        return default