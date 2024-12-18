from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import DECIMAL, JSON, VARCHAR, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import TINYINT

from app.db import Base
from app.dto_schemas.auth import Roles


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ukey: Mapped[str] = mapped_column(VARCHAR(12), unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    last_name: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    username: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    email: Mapped[str] = mapped_column(VARCHAR(320), unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    mfa_enabled: Mapped[bool] = mapped_column(insert_default=False)
    role: Mapped[Roles] = mapped_column(insert_default=Roles.USER)
    temporary: Mapped[bool] = mapped_column(insert_default=False)

    rentals: Mapped[List["Rental"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")

    change_requests: Mapped["GameChangeRequest"] = relationship(
        "GameChangeRequest", back_populates="user"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="user"
    )


class GameChangeRequestStatus(Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class GameChangeRequest(Base):
    __tablename__ = "game_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    changes: Mapped[dict] = mapped_column(JSON)  # Store changes as JSON
    status: Mapped[GameChangeRequestStatus] = mapped_column(
        insert_default=GameChangeRequestStatus.PENDING
    )
    moderator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    request_date: Mapped[datetime] = mapped_column(
        insert_default=datetime.now(timezone.utc)
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="change_requests")
    user: Mapped["User"] = relationship("User", back_populates="change_requests")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(VARCHAR(128))
    genre: Mapped[Optional[str]] = mapped_column(VARCHAR(32))
    release_date: Mapped[Optional[date]]
    date_created: Mapped[datetime] = mapped_column(
        insert_default=datetime.now(timezone.utc)
    )
    description: Mapped[str] = mapped_column(VARCHAR(2000))
    game_img_url: Mapped[str] = mapped_column(VARCHAR(2048))
    price: Mapped[Decimal] = mapped_column(DECIMAL(precision=10, scale=2))

    # more

    game_accounts: Mapped[List["GameAccountGame"]] = relationship(
        "GameAccountGame", back_populates="game"
    )
    change_requests: Mapped["GameChangeRequest"] = relationship(
        "GameChangeRequest", back_populates="game"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="game"
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    username: Mapped[str] = mapped_column(VARCHAR(50))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    text: Mapped[str] = mapped_column(VARCHAR(2000), nullable=False)
    rating: Mapped[int] = mapped_column(TINYINT, nullable=False)  # Rating from 1 to 5
    date_created: Mapped[datetime] = mapped_column(
        insert_default=datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")
    game: Mapped["Game"] = relationship("Game", back_populates="feedbacks")


class RentalStatus(Enum):  # nado?
    ACTIVE = "active"
    PENDING = "pending"
    CANCELED = "canceled"


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("game_accounts.steam_id_64"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))

    rental_date: Mapped[datetime] = mapped_column(
        insert_default=datetime.now(timezone.utc)
    )
    return_date: Mapped[Optional[datetime]]

    status: Mapped[RentalStatus] = mapped_column(insert_default=RentalStatus.PENDING)

    user: Mapped["User"] = relationship("User", back_populates="rentals")
    game_account: Mapped["GameAccount"] = relationship("GameAccount")
    game: Mapped["Game"] = relationship("Game")


class GameAccountGame(Base):
    __tablename__ = "game_account_games"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("game_accounts.steam_id_64"), primary_key=True
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    available_status: Mapped[bool] = mapped_column(insert_default=True)

    # Relationships
    game_account: Mapped["GameAccount"] = relationship(
        "GameAccount", back_populates="games"
    )
    game: Mapped["Game"] = relationship("Game", back_populates="game_accounts")


class GameAccount(Base):
    __tablename__ = "game_accounts"

    steam_id_64: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    email: Mapped[str] = mapped_column(VARCHAR(128), unique=True)
    account_name: Mapped[str] = mapped_column(VARCHAR(128), unique=True)
    password: Mapped[str] = mapped_column(VARCHAR(512))  # encrypt? can't hash

    games: Mapped[List["GameAccountGame"]] = relationship(
        "GameAccountGame", back_populates="game_account"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("game_accounts.steam_id_64"))
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(precision=10, scale=2))
    order_date: Mapped[datetime] = mapped_column(
        insert_default=datetime.now(timezone.utc)
    )
    receipt_url: Mapped[str] = mapped_column(VARCHAR(255))

    user: Mapped["User"] = relationship("User", back_populates="orders")
    game_account: Mapped["GameAccount"] = relationship("GameAccount")
    game: Mapped["Game"] = relationship("Game")
