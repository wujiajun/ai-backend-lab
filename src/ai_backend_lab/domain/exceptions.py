class OrderNotFoundError(Exception):
    pass


class OrderCannotBeCancelledError(Exception):
    pass


class InvalidOrderAmountError(Exception):
    pass


class DuplicateOrderError(Exception):
    pass


class OrderRejectedError(Exception):
    pass
