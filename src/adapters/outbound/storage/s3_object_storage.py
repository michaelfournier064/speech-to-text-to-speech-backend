from pathlib import Path


class S3ObjectStorage:
    """Filesystem-backed storage adapter with an S3-like interface."""

    def __init__(self, root_dir: str) -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def get_object(self, key: str) -> bytes:
        file_path = self._root_dir / key
        if not file_path.exists():
            raise FileNotFoundError(f"Object '{key}' was not found")
        return file_path.read_bytes()

    def put_object(self, key: str, data: bytes) -> str:
        file_path = self._root_dir / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return key
