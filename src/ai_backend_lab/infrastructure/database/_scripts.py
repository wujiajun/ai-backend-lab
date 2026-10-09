
from ai_backend_lab.infrastructure.database.database import session_factory
from ai_backend_lab.infrastructure.database.models import OrderRecord

# with session_factory() as session:
#     order = OrderRecord(
#         id="A001", customer_name="Alice", amount=Decimal("120.00"), status="Paid"
#     )

#     session.add(order)
#     session.commit()


with session_factory() as session:
    order = session.get(OrderRecord, "A001")
    if order is not None:
        order.status = "Cancelled"
        session.flush()
        session.commit()


with session_factory() as session:
    order = session.get(OrderRecord, "A001")
    if order is not None:
        print(
            f"id:{order.id}; customer_name:{order.customer_name}; amount:{order.amount}; status:{order.status}"
        )
