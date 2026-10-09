class SequenceOrderNumberGenerator:
    def __init__(
        self,
        prefix: str = "TEST",
    ):
        self._prefix = prefix
        self._sequence = 0

    def generate(self) -> str:
        self._sequence += 1

        return f"{self._prefix}-{self._sequence:03d}"


class FakeOrderNumberGenerator:
    def __init__(
        self,
        order_number: str = "TEST-ORDER-001",
    ):
        self._order_number = order_number

    def generate(self) -> str:
        return self._order_number
