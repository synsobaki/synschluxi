from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CB:
    section: str
    action: str
    value: str = "0"


# legacy compatibility field for existing handlers
    @property
    def act(self) -> str:
        return self.action

    @property
    def p1(self) -> str:
        return self.value

    @property
    def p2(self) -> str:
        return ""


def pack(section: str, action: str, value: str | int | None = "0") -> str:
    v = "0" if value is None else str(value)
    data = f"{section}:{action}:{v}"
    if len(data.encode("utf-8")) > 64:
        raise ValueError(f"callback_data too long: {data}")
    return data


def unpack(data: str | None) -> CB | None:
    if not data:
        return None
    parts = data.split(":", 2)
    if len(parts) != 3:
        return None
    section, action, value = parts
    return CB(section=section, action=action, value=value)


def to_int(s: str, default: int | None = None) -> int | None:
    try:
        return int(s)
    except Exception:
        return default
