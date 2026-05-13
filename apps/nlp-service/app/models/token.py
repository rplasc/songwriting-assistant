from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Token:
    text: str
    normalized: str
