from enum import StrEnum

from pydantic import BaseModel


class OrderAction(StrEnum):
    FIND = "find"
    CANCEL = "cancel"
    GET_STATUS = "get_status"
    UNKNOWN = "unknown"


class OrderIntent(BaseModel):
    action: OrderAction
    order_number: str | None = None
