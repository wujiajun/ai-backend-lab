from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from .exceptions import InvalidOrderAmountError, OrderCannotBeCancelledError


class OrderStatus(Enum):
    PENDING = "Pending"
    PAID = "Paid"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"


@dataclass
class Order:
    id: int | None
    order_number: str
    customer_name: str
    amount: Decimal
    status: OrderStatus
    tags: list[str] = field(default_factory=list)

    @classmethod
    def create_pending(
        cls, order_number: str, customer_name: str, amount: Decimal
    ) -> "Order":
        if amount <= 0:
            raise InvalidOrderAmountError("Order amount must be greater than 0.")
        return cls(
            id=None,
            order_number=order_number,
            customer_name=customer_name,
            amount=amount,
            status=OrderStatus.PENDING,
        )

    @property
    def is_large_order(self) -> bool:
        return self.amount >= 100.0

    @property
    def can_be_cancelled(self) -> bool:
        return (
            self.status != OrderStatus.CANCELLED and self.status != OrderStatus.SHIPPED
        )

    @staticmethod
    def is_valid_amount(amount: Decimal) -> bool:
        return amount > 0.0

    def cancel(self) -> None:
        if not self.can_be_cancelled:
            raise OrderCannotBeCancelledError(
                f"Order {self.id} cannot be cancelled."
                f"Current status: {self.status.value}"
            )
        self.status = OrderStatus.CANCELLED
