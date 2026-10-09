from ai_backend_lab.domain.models import Order, OrderStatus
from ai_backend_lab.infrastructure.database.models import OrderRecord


def order_record_to_domain(order_record: OrderRecord) -> Order:
    return Order(
        id=order_record.id,
        order_number=order_record.order_number,
        customer_name=order_record.customer_name,
        amount=order_record.amount,
        status=OrderStatus(order_record.status),
    )


def order_to_record(order: Order) -> OrderRecord:
    record = OrderRecord(
        order_number=order.order_number,
        customer_name=order.customer_name,
        amount=order.amount,
        status=order.status.value,
    )
    if order.id is not None:
        record.id = order.id
    return record
