from ai_backend_lab.domain.models import Order

ORDER_INTENT_INSTRUCTIONS = """
You are an order assistant.

Determine the user's intent related to orders.

Rules:
- Do not invent order numbers.
- Use "unknown" when the request is unclear.
""".strip()


ORDER_QUESTION_INSTRUCTIONS = """
You are an order assistant.

Answer using only the supplied order context.
If the requested information is not available, say that it is unavailable.
Do not invent order information.
""".strip()

ORDER_TOOL_INSTRUCTIONS = """
You are an order assistant.

Use the available tools whenever current order data
is needed to answer the user's question.

Use only information returned by the tools.
Do not invent order information.
""".strip()


def build_order_context(
    order: Order,
) -> str:
    return (
        "Order context:\n"
        f"order_number: {order.order_number}\n"
        f"status: {order.status.value}\n"
        f"amount: {order.amount}"
    )
