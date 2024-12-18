from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order


async def add_order(db_session: AsyncSession, order: Order) -> Order:
    db_session.add(order)
    await db_session.commit()
    return order


async def get_orders_by_user_id(db_session: AsyncSession, user_id: int) -> List[Order]:
    orders = list(
        (
            await db_session.scalars(
                select(Order).where(Order.user_id == user_id).limit(10)
            )
        ).all()
    )  # add offset later
    return orders
