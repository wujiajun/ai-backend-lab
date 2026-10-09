# import logging

# from ai_backend_lab.domain.models import Order, OrderStatus

# from .config import load_settings

# settings = load_settings()

# logging.basicConfig(
#     level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
# )
# logger = logging.getLogger(__name__)

# orders = [
#     Order("A001", "Alice", 120.0, OrderStatus.PAID),
#     Order("A002", "Bob", 45.5, OrderStatus.PENDING),
#     Order("A003", "Alice", 300.0, OrderStatus.SHIPPED),
#     Order("A004", "Bob", 20.0, OrderStatus.CANCELLED),
#     Order("A005", "Eve", 180.0, OrderStatus.PENDING),
# ]

# # result_a003 = find_order_by_id(orders, "A003")
# # result_a009 = find_order_by_id(orders, "A009")

# # if result_a003 is not None:
# #     print("Order with ID A003:", result_a003)
# # else:
# #     print("Order with ID A003 not found.")

# # if result_a009 is not None:
# #     print("Order with ID A009:", result_a009)
# # else:
# #     print("Order with ID A009 not found.")

# # print("Orders with status PENDING:", find_orders(orders, status=OrderStatus.PENDING))

# # try:
# #     result = cancel_order(orders, "A002")
# # except OrderNotFoundError as e:
# #     logger.error("Order not found: %s", e)
# # except OrderCannotBeCancelledError as e:
# #     logger.error("Order cannot be cancelled: %s", e)

# # try:
# #     result = cancel_order(orders, "A003")
# # except OrderNotFoundError as e:
# #     logger.error("Order not found: %s", e)
# # except OrderCannotBeCancelledError as e:
# #     logger.error("Order cannot be cancelled: %s", e)

# # print(f"Total amount of all orders: ${get_total_amount(orders):.1f}")


# # print(count_orders_by_customer(orders))
# # print(get_unique_customers(orders))
# # print(get_orders_by_id(orders))
# # print(get_total_amount_by_customer(orders))


# # order = orders[0]
# # print(order.is_large_order)
# # print(order.can_be_cancelled)

# # print(Order.is_valid_amount(120.0))
# # print(Order.is_valid_amount(0.0))
# # print(Order.is_valid_amount(-20.0))

# # order2 = Order.create_pending("A006", "Frank", 99.0)
# # print(order2)


# order3 = Order.create_pending("A007", "Grace", 150.0)
# order4 = Order.create_pending("A008", "Heidi", 75.0)

# order3.tags.append("urgent")

# logger.info(order3.tags)
# logger.info(order4.tags)

# logger.info(id(order3.tags))
# logger.info(id(order4.tags))
