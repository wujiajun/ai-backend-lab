from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ai_backend_lab.domain.models import OrderStatus


class OrderResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_name: str
    amount: Decimal
    status: OrderStatus


class CreateOrderRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
