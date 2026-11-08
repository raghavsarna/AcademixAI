"""Storage for uploaded PDFs.

Files are kept on the local disk for now. The interface (save/read/delete by key)
is small on purpose so it can be swapped for object storage such as S3 or R2.
"""

import uuid
from pathlib import Path

from app.config import settings


class LocalStorage:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def save(self, data: bytes, suffix: str = ".pdf") -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        key = f"{uuid.uuid4().hex}{suffix}"
        self._path(key).write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


def get_storage() -> LocalStorage:
    return LocalStorage(settings.upload_dir)
