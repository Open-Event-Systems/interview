"""Server settings."""
import base64
from pathlib import Path

import typed_settings as ts
from attrs import Factory


def _load_key_file(settings):
    if settings.encryption_key_file is not None:
        with settings.encryption_key_file.open("rb") as f:
            b64_bytes = f.read()
            bytes_ = base64.b64decode(b64_bytes)
            return ts.Secret(bytes_)


@ts.settings
class Settings:
    encryption_key_file: Path = Path("encryption_key")
    config_file: Path = Path("interviews.yml")
    encryption_key: ts.Secret[bytes] = ts.secret(
        init=False, eq=False, default=Factory(_load_key_file, takes_self=True)
    )


def load_settings() -> Settings:
    """Load the settings."""
    return ts.load(Settings, "oes.interview_old")
