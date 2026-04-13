from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import FinanceRecord, RecordStatus, User, UserRole
from .schemas import (
    DebtSummary,
    FinanceRecordCreate,
    FinanceRecordRead,
    FinanceRecordUpdate,
    UserCreate,
    UserRead,
)

app = FastAPI(title="Family Finance API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        any_admin = db.scalar(select(User).where(User.role == UserRole.ADMIN))
        if not any_admin:
            db.add(User(username="admin", role=UserRole.ADMIN))
            db.commit()


def _find_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(select(User).where(User.id == user_id))


def get_current_user(
    x_user_id: Annotated[int | None, Header()] = None, db: Session = Depends(get_db)
) -> User:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Передайте заголовок X-User-Id.",
        )
    user = _find_user_by_id(db, x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нужны права администратора.")
    return current_user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует.")
    user = User(username=payload.username, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/records", response_model=FinanceRecordRead, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: FinanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    initial_status = RecordStatus.APPROVED if current_user.role == UserRole.ADMIN else RecordStatus.PENDING
    record = FinanceRecord(
        user_id=current_user.id,
        status=initial_status,
        approved_by_id=current_user.id if initial_status == RecordStatus.APPROVED else None,
        approved_at=datetime.utcnow() if initial_status == RecordStatus.APPROVED else None,
        **payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/records", response_model=list[FinanceRecordRead])
def list_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: RecordStatus | None = Query(default=None, alias="status"),
    user_id: int | None = Query(default=None),
):
    stmt = select(FinanceRecord)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(FinanceRecord.user_id == current_user.id)
    elif user_id is not None:
        stmt = stmt.where(FinanceRecord.user_id == user_id)

    if status_filter is not None:
        stmt = stmt.where(FinanceRecord.status == status_filter)

    stmt = stmt.order_by(FinanceRecord.period_date.asc(), FinanceRecord.id.asc())
    return db.scalars(stmt).all()


@app.put("/records/{record_id}", response_model=FinanceRecordRead)
def update_record(
    record_id: int,
    payload: FinanceRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.scalar(select(FinanceRecord).where(FinanceRecord.id == record_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена.")

    if current_user.role != UserRole.ADMIN and record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нельзя менять чужую запись.")

    for key, value in payload.model_dump().items():
        setattr(record, key, value)

    if current_user.role == UserRole.ADMIN:
        record.status = RecordStatus.APPROVED
        record.approved_by_id = current_user.id
        record.approved_at = datetime.utcnow()
    else:
        # Любое изменение пользователя должно быть переподтверждено админом.
        record.status = RecordStatus.PENDING
        record.approved_by_id = None
        record.approved_at = None

    db.commit()
    db.refresh(record)
    return record


@app.post("/records/{record_id}/approve", response_model=FinanceRecordRead)
def approve_record(
    record_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    record = db.scalar(select(FinanceRecord).where(FinanceRecord.id == record_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена.")
    record.status = RecordStatus.APPROVED
    record.approved_by_id = admin.id
    record.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


@app.post("/records/{record_id}/reject", response_model=FinanceRecordRead)
def reject_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    record = db.scalar(select(FinanceRecord).where(FinanceRecord.id == record_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена.")
    record.status = RecordStatus.REJECTED
    record.approved_by_id = None
    record.approved_at = None
    db.commit()
    db.refresh(record)
    return record


@app.get("/analytics/debt-summary", response_model=DebtSummary)
def debt_summary(
    period_from: date,
    period_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if period_from > period_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный диапазон дат.")

    stmt = select(FinanceRecord).where(
        FinanceRecord.status == RecordStatus.APPROVED,
        FinanceRecord.period_date >= period_from,
        FinanceRecord.period_date <= period_to,
    )
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(FinanceRecord.user_id == current_user.id)

    records = db.scalars(stmt.order_by(FinanceRecord.period_date.asc(), FinanceRecord.id.asc())).all()

    if not records:
        return DebtSummary(
            period_from=period_from,
            period_to=period_to,
            records_count=0,
            opening_debt=0.0,
            closing_debt=0.0,
            debt_change=0.0,
            total_income=0.0,
            total_mandatory_expense=0.0,
            total_urgent_creditcard_repayment=0.0,
        )

    opening_debt = records[0].debt_total
    closing_debt = records[-1].debt_total
    return DebtSummary(
        period_from=period_from,
        period_to=period_to,
        records_count=len(records),
        opening_debt=opening_debt,
        closing_debt=closing_debt,
        debt_change=closing_debt - opening_debt,
        total_income=sum(item.income for item in records),
        total_mandatory_expense=sum(item.mandatory_expense for item in records),
        total_urgent_creditcard_repayment=sum(item.urgent_creditcard_repayment for item in records),
    )
