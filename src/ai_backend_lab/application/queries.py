from dataclasses import dataclass
from enum import StrEnum

from ai_backend_lab.domain.models import OrderStatus


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class OrderSortField(StrEnum):
    ID = "id"
    ORDER_NUMBER = "order_number"
    AMOUNT = "amount"


@dataclass(frozen=True)
class OrderQuery:
    customer_name: str | None = None
    status: OrderStatus | None = None

    limit: int = 20
    offset: int = 0

    sort_by: OrderSortField = OrderSortField.ID
    sort_direction: SortDirection = SortDirection.DESC
