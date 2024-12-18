from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.managers.exceptions import UserNotFound
from app.db.models import User
from app.dto_schemas.auth import Roles
from app.dto_schemas.user import EmailOnlyUser, UserCreate
from app.utils import generate_ukey


async def get_user_by_id(db_session: AsyncSession, user_id: int) -> User | None:
    user = (await db_session.scalars(select(User).where(User.id == user_id))).first()
    return user


async def get_users(db_session: AsyncSession) -> List[User]:
    return list((await db_session.scalars(select(User))).all())


async def add_user(db_session: AsyncSession, user_create_model: UserCreate) -> User:
    user = User(
        ukey=generate_ukey(),
        username=user_create_model.username,
        first_name=user_create_model.first_name or None,
        last_name=user_create_model.last_name or None,
        email=user_create_model.email,
        hashed_password=user_create_model.password,
        role=Roles.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def add_temp_user(
    db_session: AsyncSession, user_create_model: EmailOnlyUser
) -> User:
    user = User(ukey=generate_ukey(), email=user_create_model.email, temporary=True)

    db_session.add(user)
    await db_session.commit()
    return user


async def update_user(db_session: AsyncSession, user: User) -> User:
    db_session.add(user)
    await db_session.commit()
    return user


async def get_user_by_email(db_session: AsyncSession, email: str) -> User | None:
    user = (await db_session.scalars(select(User).where(User.email == email))).first()
    return user


async def get_user_by_ukey(db_session: AsyncSession, ukey: str) -> User | None:
    user = (await db_session.scalars(select(User).where(User.ukey == ukey))).first()
    return user


async def update_role_by_email(
    db_session: AsyncSession, email: str, role: Roles
) -> User:
    user = (await db_session.scalars(select(User).where(User.email == email))).first()
    if not user:
        raise UserNotFound()

    user.role = role
    await db_session.commit()
    return user


async def update_password_by_id(
    db_session: AsyncSession, user_id: str, new_password: str
) -> User:
    user = (await db_session.scalars(select(User).where(User.id == user_id))).first()
    if not user:
        raise UserNotFound()

    user.hashed_password = new_password
    await db_session.commit()
    return user
