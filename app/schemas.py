from datetime import date, datetime

from pydantic import BaseModel, Field

from .models import CreditCardStatus, DebtStatus, RecordStatus, UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.USER


class UserRead(BaseModel):
    id: int
    username: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class UserAdminUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=100)
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    is_active: bool | None = None


class AuditLogRead(BaseModel):
    id: int
    action: str
    actor_user_id: int | None
    actor_username: str | None = None
    target_user_id: int | None
    target_username: str | None = None
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogPage(BaseModel):
    items: list[AuditLogRead]
    total_count: int
    limit: int
    offset: int


class DebtBase(BaseModel):
    creditor_name: str = Field(min_length=2, max_length=120)
    principal_amount: float
    start_date: date
    planned_payoff_date: date | None = None
    interest_rate: float | None = None
    comment: str | None = Field(default=None, max_length=500)


class DebtCreate(DebtBase):
    pass


class DebtRead(DebtBase):
    id: int
    user_id: int
    current_balance: float
    status: DebtStatus
    moderation_status: RecordStatus
    approved_by_id: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DebtRepaymentCreate(BaseModel):
    payment_date: date
    amount: float = Field(gt=0)
    comment: str | None = Field(default=None, max_length=500)


class DebtRepaymentRead(DebtRepaymentCreate):
    id: int
    debt_id: int
    user_id: int
    moderation_status: RecordStatus
    approved_by_id: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreditCardBase(BaseModel):
    card_name: str = Field(min_length=2, max_length=120)
    grace_start_date: date
    grace_period_days: int = Field(gt=0, le=120)
    current_debt: float = Field(ge=0)
    comment: str | None = Field(default=None, max_length=500)


class CreditCardCreate(CreditCardBase):
    pass


class CreditCardRead(CreditCardBase):
    id: int
    user_id: int
    status: CreditCardStatus
    moderation_status: RecordStatus
    approved_by_id: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    grace_end_date: date
    remaining_grace_days: int
    amount_to_pay_urgent: float

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
