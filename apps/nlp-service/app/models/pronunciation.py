from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pronunciation:
    phonemes: tuple[str, ...]
    syllables: int
