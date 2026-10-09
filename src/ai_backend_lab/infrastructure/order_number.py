from datetime import datetime, timezone
from uuid import uuid4


class UuidOrderNumberGenerator:

    def generate(self) -> str:
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = uuid4().hex[:12].upper()
        return f"ORD-{date_part}-{random_part}"
