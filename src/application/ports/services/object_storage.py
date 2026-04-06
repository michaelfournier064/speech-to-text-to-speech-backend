from typing import Protocol


class ObjectStorage(Protocol):
    def get_object(self, key: str) -> bytes:
        ...

    def put_object(self, key: str, data: bytes) -> str:
        ...
