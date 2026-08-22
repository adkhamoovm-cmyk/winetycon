import asyncio
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Boolean, Float, DateTime, ForeignKey, Integer
from bot.config import DB_URL, DB_PATH

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fullname: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    ombor_balance: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_total: Mapped[float] = mapped_column(Float, default=0.0)
    withdraw_total: Mapped[float] = mapped_column(Float, default=0.0)
    ref_profit_total: Mapped[float] = mapped_column(Float, default=0.0)
    card_name: Mapped[str] = mapped_column(String, nullable=True)
    card_type: Mapped[str] = mapped_column(String, nullable=True)
    card_number: Mapped[str] = mapped_column(String, nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Shop(Base):
    __tablename__ = 'shops'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    tier: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    daily_tasks_done: Mapped[int] = mapped_column(Integer, default=0)
    last_task_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    type: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String)
    photo_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PromoCode(Base):
    __tablename__ = 'promo_codes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    amount: Mapped[float] = mapped_column(Float)
    limit: Mapped[int] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class UserPromo(Base):
    __tablename__ = 'user_promos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    promo_id: Mapped[int] = mapped_column(Integer, ForeignKey('promo_codes.id'))

class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_card_name: Mapped[str] = mapped_column(String, default="Admin")
    admin_card_number: Mapped[str] = mapped_column(String, default="8600123456789012")
    community_link: Mapped[str] = mapped_column(String, default="https://t.me/ETycoon_Community")
    community_id: Mapped[str] = mapped_column(String, default="@ETycoon_Community")

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        if not settings:
            session.add(Settings(id=1))
            await session.commit()
