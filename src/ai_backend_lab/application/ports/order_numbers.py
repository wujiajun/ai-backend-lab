from typing import Protocol


class OrderNumberGenerator(Protocol):
    def generate(self) -> str: ...
