import json
from dataclasses import dataclass, asdict
from pathlib import Path

__all__ = [
    'Settings'
]


@dataclass(frozen=True)
class Settings:
    token: str
    google_credentials: str
    theme: int = 0xf1a7be

    def save(self, fp: Path) -> None:
        with fp.open('w') as settings:
            json.dump(asdict(self), settings)

    @classmethod
    def load(cls, fp: Path) -> 'Settings':
        with fp.open('r') as settings:
            data = json.load(settings)

        return cls(**data)
