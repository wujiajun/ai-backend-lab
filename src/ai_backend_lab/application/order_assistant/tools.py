from decimal import Decimal

from pydantic import BaseModel

from ai_backend_lab.application.ports.llm import (
    LLMToolDefinition,
)
from ai_backend_lab.domain.models import (
    OrderStatus,
)


class GetOrderArguments(BaseModel):
    order_number: str


class GetOrderToolOutput(BaseModel):
    found: bool
    order_number: str
    status: OrderStatus | None = None
    amount: Decimal | None = None


GET_ORDER_TOOL = LLMToolDefinition(
    name="get_order",
    description=(
        "Get an order by its business order number. "
        "Use this when the user asks for information "
        "about a specific order."
    ),
    parameters={
        "type": "object",
        "properties": {
            "order_number": {
                "type": "string",
                "description": (
                    "The business order number, " "for example ORD-20261005-ABC123."
                ),
            },
        },
        "required": ["order_number"],
        "additionalProperties": False,
    },
)


class CancelOrderArguments(BaseModel):
    order_number: str


class CancelOrderToolOutput(BaseModel):
    ok: bool
    order_number: str
    status: OrderStatus | None = None
    error_code: str | None = None
    message: str | None = None


CANCEL_ORDER_TOOL = LLMToolDefinition(
    name="cancel_order",
    description=(
        "Cancel an existing order. "
        "Use this only when the user explicitly asks "
        "to cancel an order."
    ),
    parameters={
        "type": "object",
        "properties": {
            "order_number": {
                "type": "string",
                "description": ("The business order number to cancel."),
            },
        },
        "required": [
            "order_number",
        ],
        "additionalProperties": False,
    },
)
