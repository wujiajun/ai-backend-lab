from fastapi import APIRouter, Query, status

from ai_backend_lab.api.dependencies import OrderServiceDep
from ai_backend_lab.api.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
)
from ai_backend_lab.application.queries import (
    OrderQuery,
    OrderSortField,
    SortDirection,
)
from ai_backend_lab.domain.models import OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_number}", response_model=OrderResponse)
def get_order(order_number: str, order_service: OrderServiceDep) -> OrderResponse:
    order = order_service.get_order_or_raise(order_number)
    return OrderResponse.model_validate(order)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    order_service: OrderServiceDep,
    customer_name: str | None = None,
    status: OrderStatus | None = None,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    sort_by: OrderSortField = OrderSortField.ID,
    sort_direction: SortDirection = SortDirection.DESC,
) -> list[OrderResponse]:
    query = OrderQuery(
        customer_name=customer_name,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    order_list = order_service.find_orders(query)
    return [OrderResponse.model_validate(order) for order in order_list]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest, order_service: OrderServiceDep
) -> OrderResponse:
    order = await order_service.create_order(
        customer_name=request.customer_name,
        amount=request.amount,
    )
    return OrderResponse.model_validate(order)


@router.post("/{order_number}/cancel", response_model=OrderResponse)
def cancel_order(order_number: str, order_service: OrderServiceDep) -> OrderResponse:
    order = order_service.cancel_order(order_number=order_number)
    return OrderResponse.model_validate(order)
