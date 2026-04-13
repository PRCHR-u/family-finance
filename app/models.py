from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class RecordStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False, default=UserRole.USER)

    records: Mapped[list["FinanceRecord"]] = relationship(
        "FinanceRecord", back_populates="owner", foreign_keys="FinanceRecord.user_id"
    )


class FinanceRecord(Base):
    __tablename__ = "finance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    period_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    planned_expense: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    debt_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mandatory_expense: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    urgent_creditcard_repayment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus), nullable=False, default=RecordStatus.PENDING
    )

    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner: Mapped["User"] = relationship("User", back_populates="records", foreign_keys=[user_id])
