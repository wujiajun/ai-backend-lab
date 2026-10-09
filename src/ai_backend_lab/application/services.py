import asyncio
import logging
from decimal import Decimal

from ai_backend_lab.application.ports.order_numbers import OrderNumberGenerator
from ai_backend_lab.application.ports.risk import (
    RiskGateway,
)
from ai_backend_lab.application.ports.unit_of_work import UnitOfWork
from ai_backend_lab.application.queries import OrderQuery
from ai_backend_lab.domain.exceptions import OrderNotFoundError, OrderRejectedError
from ai_backend_lab.domain.models import Order

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        uow: UnitOfWork,
        order_number_generator: OrderNumberGenerator,
        risk_gateway: RiskGateway,
    ):
        self._uow = uow
        self._order_number_generator = order_number_generator
        self._risk_gateway = risk_gateway

    def get_order(self, order_number: str) -> Order | None:
        with self._uow:
            return self._uow.orders.find_by_order_number(order_number=order_number)

    def get_order_or_raise(
        self,
        order_number: str,
    ) -> Order:
        with self._uow:
            order = self._uow.orders.find_by_order_number(order_number)
            if order is None:
                raise OrderNotFoundError(f"Order {order_number} not found.")
            return order

    def cancel_order(self, order_number: str) -> Order:
        with self._uow:
            logger.info("Starting cancel_order for order_number: %s", order_number)
            order = self.get_order_or_raise(order_number)
            order.cancel()
            self._uow.orders.update(order)
            self._uow.commit()
            logger.info(
                "Order cancelled " "order_id=%s order_number=%s",
                order.id,
                order.order_number,
            )
            return order

    def find_orders(
        self,
        query: OrderQuery,
    ) -> list[Order]:
        with self._uow:
            return self._uow.orders.find(query)

    # def get_total_amount(
    #     orders: list[Order],
    # ) -> float:
    #     total_amount: float = 0.0
    #     for order in orders:
    #         total_amount += order.amount
    #     return total_amount

    # def get_customer_names(
    #     orders: list[Order],
    # ) -> list[str]:
    #     return [order.customer_name for order in orders]

    async def create_order(
        self,
        customer_name: str,
        amount: Decimal,
    ) -> Order:
        assesment = await self._risk_gateway.assess(
            customer_name=customer_name, amount=amount
        )
        if not assesment.approved:
            raise OrderRejectedError(
                assesment.reason or "Order rejected by risk assessment."
            )

        order_number = self._order_number_generator.generate()
        order = Order.create_pending(
            order_number=order_number,
            customer_name=customer_name,
            amount=amount,
        )

        await asyncio.to_thread(
            self._persist_order,
            order,
        )

        logger.info(
            "Order created order_id=%s order_number=%s",
            order.id,
            order.order_number,
        )

        return order

    def _persist_order(
        self,
        order: Order,
    ) -> None:
        with self._uow:
            self._uow.orders.add(order)
            self._uow.commit()

    # def count_orders_by_customer(
    #     orders: list[Order],
    # ) -> dict[str, int]:
    #     customer_order_count: dict[str, int] = {}
    #     for order in orders:
    #         customer_order_count[order.customer_name] = (
    #             customer_order_count.get(order.customer_name, 0) + 1
    #         )
    #     return customer_order_count

    # def get_unique_customers(
    #     orders: list[Order],
    # ) -> set[str]:
    #     return {order.customer_name for order in orders}

    # def get_orders_by_id(
    #     orders: list[Order],
    # ) -> dict[str, Order]:
    #     return {order.id: order for order in orders}

    # def get_total_amount_by_customer(
    #     orders: list[Order],
    # ) -> dict[str, float]:
    #     customer_total_amount: dict[str, float] = {}
    #     for order in orders:
    #         customer_total_amount[order.customer_name] = (
    #             customer_total_amount.get(order.customer_name, 0.0) + order.amount
    #         )
    #     return customer_total_amount
