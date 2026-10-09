from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ai_backend_lab.infrastructure.database.base import Base


class OrderRecord(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    order_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
    )

    customer_name: Mapped[str] = mapped_column(String(100))

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    status: Mapped[str] = mapped_column(String(20))
