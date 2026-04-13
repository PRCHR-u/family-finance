from datetime import date, datetime

from pydantic import BaseModel, Field

from .models import RecordStatus, UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.USER


class UserRead(BaseModel):
    id: int
    username: str
    role: UserRole

    class Config:
        from_attributes = True


class FinanceRecordBase(BaseModel):
    period_date: date
    income: float = 0.0
    planned_expense: float = 0.0
    debt_total: float = 0.0
    mandatory_expense: float = 0.0
    urgent_creditcard_repayment: float = 0.0
    comment: str | None = Field(default=None, max_length=500)


class FinanceRecordCreate(FinanceRecordBase):
    pass


class FinanceRecordUpdate(FinanceRecordBase):
    pass


class FinanceRecordRead(FinanceRecordBase):
    id: int
    user_id: int
    status: RecordStatus
    approved_by_id: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DebtSummary(BaseModel):
    period_from: date
    period_to: date
    records_count: int
    opening_debt: float
    closing_debt: float
    debt_change: float
    total_income: float
    total_mandatory_expense: float
    total_urgent_creditcard_repayment: float
