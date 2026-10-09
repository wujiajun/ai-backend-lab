"""add internal order id and order number

Revision ID: f4a0f15493b0
Revises: 56a8761028e8
Create Date: 2026-09-29 12:13:16.785653

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a0f15493b0"
down_revision: Union[str, Sequence[str], None] = "56a8761028e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders_new",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "order_number",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "customer_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_orders"),
        ),
        sa.UniqueConstraint(
            "order_number",
            name=op.f("uq_orders_order_number"),
        ),
    )

    op.execute("""
    INSERT INTO orders_new (
        order_number,
        customer_name,
        amount,
        status
    )
    SELECT
        id,
        customer_name,
        amount,
        status
    FROM orders
    """)

    op.drop_table("orders")

    op.rename_table(
        "orders_new",
        "orders",
    )


def downgrade() -> None:
    op.create_table(
        "orders_old",
        sa.Column(
            "id",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "customer_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_orders"),
        ),
    )

    op.execute("""
        INSERT INTO orders_old (
            id,
            customer_name,
            amount,
            status
        )
        SELECT
            order_number,
            customer_name,
            amount,
            status
        FROM orders
        """)

    op.drop_table("orders")

    op.rename_table(
        "orders_old",
        "orders",
    )
