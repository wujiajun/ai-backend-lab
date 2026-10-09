from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_backend_lab.application.ports.repositories import OrderRepository
from ai_backend_lab.application.queries import OrderQuery, OrderSortField, SortDirection
from ai_backend_lab.domain.exceptions import DuplicateOrderError
from ai_backend_lab.domain.models import Order
from ai_backend_lab.infrastructure.database.mappers import (
    order_record_to_domain,
    order_to_record,
)
from ai_backend_lab.infrastructure.database.models import OrderRecord


class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, order_id: int) -> Order | None:
        record = self._session.get(OrderRecord, order_id)
        if record is None:
            return None

        return order_record_to_domain(record)

    def find_by_order_number(self, order_number: str) -> Order | None:
        statement = select(OrderRecord).where(OrderRecord.order_number == order_number)
        record = self._session.scalar(statement=statement)
        if record is None:
            return None
        return order_record_to_domain(record)

    def find(self, order_query: OrderQuery) -> list[Order]:
        statement = select(OrderRecord)
        if order_query.customer_name is not None:
            statement = statement.where(
                OrderRecord.customer_name == order_query.customer_name
            )

        if order_query.status is not None:
            statement = statement.where(OrderRecord.status == order_query.status.value)

        sort_columns = {
            OrderSortField.ID: OrderRecord.id,
            OrderSortField.ORDER_NUMBER: (OrderRecord.order_number),
            OrderSortField.AMOUNT: OrderRecord.amount,
        }

        sort_column = sort_columns[order_query.sort_by]

        if order_query.sort_direction == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())

        statement = statement.limit(order_query.limit).offset(order_query.offset)

        records = self._session.scalars(statement).all()

        return [order_record_to_domain(record) for record in records]

    def add(self, order: Order) -> None:
        record = order_to_record(order)
        self._session.add(record)
        try:
            self._session.flush()
        except IntegrityError as exc:
            mysql_error_code = exc.orig.args[0] if exc.orig is not None else None

            if mysql_error_code is not None and mysql_error_code == 1062:
                raise DuplicateOrderError(
                    f"Order {order.order_number} already exists."
                ) from exc

            raise
        order.id = record.id

    def update(self, order: Order) -> None:
        if order.id is None:
            raise ValueError("Cannot update an order without a database id.")
        record = self._session.get(OrderRecord, order.id)

        if record is None:
            raise RuntimeError(f"Order {order.id} does not exist.")

        record.customer_name = order.customer_name
        record.amount = order.amount
        record.status = order.status.value
