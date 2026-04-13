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


class DebtStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class CreditCardStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

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


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    creditor_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    principal_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_balance: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    planned_payoff_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[DebtStatus] = mapped_column(SqlEnum(DebtStatus), nullable=False, default=DebtStatus.ACTIVE)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)

    moderation_status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus), nullable=False, default=RecordStatus.PENDING
    )
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DebtRepayment(Base):
    __tablename__ = "debt_repayments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    debt_id: Mapped[int] = mapped_column(ForeignKey("debts.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)

    moderation_status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus), nullable=False, default=RecordStatus.PENDING
    )
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    card_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    grace_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    grace_period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    current_debt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[CreditCardStatus] = mapped_column(
        SqlEnum(CreditCardStatus), nullable=False, default=CreditCardStatus.ACTIVE
    )
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)

    moderation_status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus), nullable=False, default=RecordStatus.PENDING
    )
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    details: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
