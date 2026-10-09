import logging

from ai_backend_lab.observability.context import (
    get_request_id,
)


class RequestIdFilter(logging.Filter):
    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        record.request_id = get_request_id() or "-"

        return True


def configure_logging(
    level: str,
) -> None:
    handler = logging.StreamHandler()

    handler.addFilter(RequestIdFilter())

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "request_id=%(request_id)s "
            "%(message)s"
        )
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(level.upper())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
