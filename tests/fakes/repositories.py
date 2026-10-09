from ai_backend_lab.application.ports.repositories import OrderRepository
from ai_backend_lab.application.queries import (
    OrderQuery,
    OrderSortField,
    SortDirection,
)
from ai_backend_lab.domain.exceptions import DuplicateOrderError
from ai_backend_lab.domain.models import Order


class InMemoryOrderRepository(OrderRepository):
    def __init__(
        self,
        orders: list[Order] | None = None,
    ):
        self._orders = list(orders or [])

    def find_by_id(
        self,
        order_id: int,
    ) -> Order | None:
        for order in self._orders:
            if order.id == order_id:
                return order

        return None

    def find_by_order_number(self, order_number: str) -> Order | None:
        for order in self._orders:
            if order.order_number == order_number:
                return order
        return None

    def find(
        self,
        query: OrderQuery,
    ) -> list[Order]:
        orders = [
            order
            for order in self._orders
            if (
                query.customer_name is None
                or order.customer_name == query.customer_name
            )
            and (query.status is None or order.status == query.status)
        ]

        def key(order):
            if query.sort_by == OrderSortField.ID:
                return order.id or 0
            if query.sort_by == OrderSortField.ORDER_NUMBER:
                return order.order_number
            return order.amount

        orders.sort(
            key=key,
            reverse=(query.sort_direction == SortDirection.DESC),
        )

        return orders[query.offset : query.offset + query.limit]

    def add(
        self,
        order: Order,
    ) -> None:
        if order.order_number is None:
            raise ValueError("Order_number is null.")
        existing = self.find_by_order_number(order.order_number)
        if existing is not None:
            raise DuplicateOrderError(f"Order {order.order_number} already exists.")

        if order.id is None:
            existing_ids = [
                existing.id for existing in self._orders if existing.id is not None
            ]

        order.id = max(existing_ids, default=0) + 1
        self._orders.append(order)

    def update(self, order: Order) -> None:
        for index, existing in enumerate(self._orders):
            if existing.id == order.id:
                self._orders[index] = order
                return
