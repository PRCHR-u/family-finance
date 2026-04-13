import csv
from datetime import date, datetime
from io import StringIO
from pathlib import Path

import openpyxl
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session, aliased

from .auth import create_access_token, get_password_hash, verify_password, decode_access_token
from .database import Base, SessionLocal, engine, get_db
from .models import (
    AuditLog,
    Debt,
    DebtRepayment,
    DebtStatus,
    FinanceRecord,
    RecordStatus,
    User,
    UserRole,
)
from .schemas import (
    AuditLogPage,
    AuditLogRead,
    ChangePasswordRequest,
    DebtCreate,
    DebtRead,
    DebtRepaymentCreate,
    DebtRepaymentRead,
    DebtSummary,
    FinanceRecordCreate,
    FinanceRecordRead,
    FinanceRecordUpdate,
    LoginRequest,
    TokenResponse,
    UserAdminUpdate,
    UserCreate,
    UserRead,
)

app = FastAPI(title="Family Finance API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class ImportResult(BaseModel):
    inserted: int
    updated: int
    skipped: int


def _log_action(
    db: Session,
    action: str,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    details: str | None = None,
):
    db.add(
        AuditLog(
            action=action,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            details=details,
        )
    )


def _ensure_users_table_columns():
    with engine.connect() as conn:
        existing_columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        if "hashed_password" not in existing_columns:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) DEFAULT '' NOT NULL")
            )
            conn.commit()
        if "is_active" not in existing_columns:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL")
            )
            conn.commit()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _ensure_users_table_columns()
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.role == UserRole.ADMIN))
        if not admin:
            db.add(
                User(
                    username="admin",
                    role=UserRole.ADMIN,
                    hashed_password=get_password_hash("admin123456"),
                )
            )
            db.commit()


def _coerce_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace(" ", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _recalculate_debt_balance(db: Session, debt: Debt):
    approved_repayments = db.scalars(
        select(DebtRepayment).where(
            DebtRepayment.debt_id == debt.id,
            DebtRepayment.moderation_status == RecordStatus.APPROVED,
        )
    ).all()
    paid_amount = sum(item.amount for item in approved_repayments)
    debt.current_balance = max(0.0, debt.principal_amount - paid_amount)
    debt.status = DebtStatus.CLOSED if debt.current_balance <= 0 else DebtStatus.ACTIVE


def _debt_total_as_of(db: Session, current_user: User, as_of: date) -> float:
    stmt = select(Debt).where(
        Debt.moderation_status == RecordStatus.APPROVED,
        Debt.start_date <= as_of,
    )
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Debt.user_id == current_user.id)
    debts = db.scalars(stmt).all()
    total = 0.0
    for debt in debts:
        approved_paid = db.scalars(
            select(DebtRepayment).where(
                DebtRepayment.debt_id == debt.id,
                DebtRepayment.moderation_status == RecordStatus.APPROVED,
                DebtRepayment.payment_date <= as_of,
            )
        ).all()
        outstanding = max(0.0, debt.principal_amount - sum(item.amount for item in approved_paid))
        total += outstanding
    return total


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен.")
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь деактивирован.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нужны права администратора.")
    return current_user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует.")
    user = User(
        username=payload.username,
        role=UserRole.USER,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()
    _log_action(db, "auth.register", actor_user_id=user.id, details=f"username={payload.username}")
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь деактивирован.")
    return TokenResponse(access_token=create_access_token(subject=user.username))


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует.")
    user = User(
        username=payload.username,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()
    _log_action(
        db,
        "users.create",
        actor_user_id=admin.id,
        target_user_id=user.id,
        details=f"username={user.username}, role={user.role.value}",
    )
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.scalars(select(User).order_by(User.id.asc())).all()


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user_by_admin(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет данных для обновления.")

    if "username" in updates:
        existing = db.scalar(select(User).where(User.username == updates["username"], User.id != user.id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Логин уже занят.")
        user.username = updates["username"]
    if "role" in updates:
        user.role = updates["role"]
    if "password" in updates:
        user.hashed_password = get_password_hash(updates["password"])
    if "is_active" in updates:
        if user.id == admin.id and updates["is_active"] is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя деактивировать самого себя.")
        user.is_active = updates["is_active"]

    _log_action(
        db,
        "users.update",
        actor_user_id=admin.id,
        target_user_id=user.id,
        details=f"fields={','.join(updates.keys())}",
    )
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}")
def delete_user_by_admin(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя.")
    has_records = db.scalar(
        select(FinanceRecord.id).where(FinanceRecord.user_id == user.id).limit(1)
    )
    if has_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя с финансовыми записями. Сначала деактивируйте его.",
        )
    _log_action(db, "users.delete", actor_user_id=admin.id, target_user_id=user.id, details=user.username)
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален."}


@app.post("/users/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя деактивировать самого себя.")
    user.is_active = False
    _log_action(db, "users.deactivate", actor_user_id=admin.id, target_user_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@app.post("/users/{user_id}/activate", response_model=UserRead)
def activate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")
    user.is_active = True
    _log_action(db, "users.activate", actor_user_id=admin.id, target_user_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/users/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Старый пароль неверен.")
    current_user.hashed_password = get_password_hash(payload.new_password)
    _log_action(db, "users.change_password", actor_user_id=current_user.id)
    db.commit()
    return {"message": "Пароль обновлен."}


@app.post("/debts", response_model=DebtRead, status_code=status.HTTP_201_CREATED)
def create_debt(
    payload: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    moderation_status = RecordStatus.APPROVED if current_user.role == UserRole.ADMIN else RecordStatus.PENDING
    debt = Debt(
        user_id=current_user.id,
        current_balance=payload.principal_amount,
        moderation_status=moderation_status,
        approved_by_id=current_user.id if moderation_status == RecordStatus.APPROVED else None,
        approved_at=datetime.utcnow() if moderation_status == RecordStatus.APPROVED else None,
        **payload.model_dump(),
    )
    db.add(debt)
    db.flush()
    _log_action(
        db,
        "debts.create",
        actor_user_id=current_user.id,
        target_user_id=debt.user_id,
        details=f"debt_id={debt.id}, creditor={debt.creditor_name}",
    )
    db.commit()
    db.refresh(debt)
    return debt


@app.get("/debts", response_model=list[DebtRead])
def list_debts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int | None = Query(default=None),
    debt_status: DebtStatus | None = Query(default=None, alias="status"),
    moderation_status: RecordStatus | None = Query(default=None),
):
    stmt = select(Debt)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Debt.user_id == current_user.id)
    elif user_id is not None:
        stmt = stmt.where(Debt.user_id == user_id)
    if debt_status is not None:
        stmt = stmt.where(Debt.status == debt_status)
    if moderation_status is not None:
        stmt = stmt.where(Debt.moderation_status == moderation_status)
    return db.scalars(stmt.order_by(Debt.start_date.desc(), Debt.id.desc())).all()


@app.post("/debts/{debt_id}/approve", response_model=DebtRead)
def approve_debt(debt_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    debt = db.scalar(select(Debt).where(Debt.id == debt_id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Долг не найден.")
    debt.moderation_status = RecordStatus.APPROVED
    debt.approved_by_id = admin.id
    debt.approved_at = datetime.utcnow()
    _log_action(
        db,
        "debts.approve",
        actor_user_id=admin.id,
        target_user_id=debt.user_id,
        details=f"debt_id={debt.id}",
    )
    db.commit()
    db.refresh(debt)
    return debt


@app.post("/debts/{debt_id}/reject", response_model=DebtRead)
def reject_debt(debt_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    debt = db.scalar(select(Debt).where(Debt.id == debt_id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Долг не найден.")
    debt.moderation_status = RecordStatus.REJECTED
    debt.approved_by_id = None
    debt.approved_at = None
    _log_action(
        db,
        "debts.reject",
        actor_user_id=admin.id,
        target_user_id=debt.user_id,
        details=f"debt_id={debt.id}",
    )
    db.commit()
    db.refresh(debt)
    return debt


@app.post("/debts/{debt_id}/repayments", response_model=DebtRepaymentRead, status_code=status.HTTP_201_CREATED)
def create_debt_repayment(
    debt_id: int,
    payload: DebtRepaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debt = db.scalar(select(Debt).where(Debt.id == debt_id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Долг не найден.")
    if current_user.role != UserRole.ADMIN and debt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нельзя добавлять платеж к чужому долгу.")

    moderation_status = RecordStatus.APPROVED if current_user.role == UserRole.ADMIN else RecordStatus.PENDING
    repayment = DebtRepayment(
        debt_id=debt.id,
        user_id=current_user.id,
        moderation_status=moderation_status,
        approved_by_id=current_user.id if moderation_status == RecordStatus.APPROVED else None,
        approved_at=datetime.utcnow() if moderation_status == RecordStatus.APPROVED else None,
        **payload.model_dump(),
    )
    db.add(repayment)
    if moderation_status == RecordStatus.APPROVED:
        _recalculate_debt_balance(db, debt)
    db.flush()
    _log_action(
        db,
        "debts.repayment.create",
        actor_user_id=current_user.id,
        target_user_id=debt.user_id,
        details=f"debt_id={debt.id}, repayment_id={repayment.id}, amount={repayment.amount}",
    )
    db.commit()
    db.refresh(repayment)
    return repayment


@app.get("/debts/{debt_id}/repayments", response_model=list[DebtRepaymentRead])
def list_debt_repayments(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debt = db.scalar(select(Debt).where(Debt.id == debt_id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Долг не найден.")
    if current_user.role != UserRole.ADMIN and debt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нельзя просматривать чужой долг.")
    stmt = select(DebtRepayment).where(DebtRepayment.debt_id == debt_id)
    return db.scalars(stmt.order_by(DebtRepayment.payment_date.asc(), DebtRepayment.id.asc())).all()


@app.post("/repayments/{repayment_id}/approve", response_model=DebtRepaymentRead)
def approve_repayment(
    repayment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repayment = db.scalar(select(DebtRepayment).where(DebtRepayment.id == repayment_id))
    if not repayment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Погашение не найдено.")
    debt = db.scalar(select(Debt).where(Debt.id == repayment.debt_id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Долг не найден.")
    repayment.moderation_status = RecordStatus.APPROVED
    repayment.approved_by_id = admin.id
    repayment.approved_at = datetime.utcnow()
    _recalculate_debt_balance(db, debt)
    _log_action(
        db,
        "debts.repayment.approve",
        actor_user_id=admin.id,
        target_user_id=debt.user_id,
        details=f"debt_id={debt.id}, repayment_id={repayment.id}",
    )
    db.commit()
    db.refresh(repayment)
    return repayment


@app.post("/repayments/{repayment_id}/reject", response_model=DebtRepaymentRead)
def reject_repayment(
    repayment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repayment = db.scalar(select(DebtRepayment).where(DebtRepayment.id == repayment_id))
    if not repayment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Погашение не найдено.")
    debt = db.scalar(select(Debt).where(Debt.id == repayment.debt_id))
    repayment.moderation_status = RecordStatus.REJECTED
    repayment.approved_by_id = None
    repayment.approved_at = None
    _log_action(
        db,
        "debts.repayment.reject",
        actor_user_id=admin.id,
        target_user_id=debt.user_id if debt else None,
        details=f"repayment_id={repayment.id}",
    )
    db.commit()
    db.refresh(repayment)
    return repayment


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
    return db.scalars(stmt.order_by(FinanceRecord.period_date.asc(), FinanceRecord.id.asc())).all()


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
        record.status = RecordStatus.PENDING
        record.approved_by_id = None
        record.approved_at = None

    db.commit()
    db.refresh(record)
    return record


@app.post("/records/{record_id}/approve", response_model=FinanceRecordRead)
def approve_record(record_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    record = db.scalar(select(FinanceRecord).where(FinanceRecord.id == record_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена.")
    record.status = RecordStatus.APPROVED
    record.approved_by_id = admin.id
    record.approved_at = datetime.utcnow()
    _log_action(
        db,
        "records.approve",
        actor_user_id=admin.id,
        target_user_id=record.user_id,
        details=f"record_id={record.id}",
    )
    db.commit()
    db.refresh(record)
    return record


@app.post("/records/{record_id}/reject", response_model=FinanceRecordRead)
def reject_record(record_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    record = db.scalar(select(FinanceRecord).where(FinanceRecord.id == record_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена.")
    record.status = RecordStatus.REJECTED
    record.approved_by_id = None
    record.approved_at = None
    _log_action(
        db,
        "records.reject",
        actor_user_id=admin.id,
        target_user_id=record.user_id,
        details=f"record_id={record.id}",
    )
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

    day_before = period_from.fromordinal(period_from.toordinal() - 1)
    opening_debt = _debt_total_as_of(db, current_user, day_before)
    closing_debt = _debt_total_as_of(db, current_user, period_to)

    finance_stmt = select(FinanceRecord).where(
        FinanceRecord.status == RecordStatus.APPROVED,
        FinanceRecord.period_date >= period_from,
        FinanceRecord.period_date <= period_to,
    )
    if current_user.role != UserRole.ADMIN:
        finance_stmt = finance_stmt.where(FinanceRecord.user_id == current_user.id)
    records = db.scalars(
        finance_stmt.order_by(FinanceRecord.period_date.asc(), FinanceRecord.id.asc())
    ).all()

    if not records:
        return DebtSummary(
            period_from=period_from,
            period_to=period_to,
            records_count=0,
            opening_debt=opening_debt,
            closing_debt=closing_debt,
            debt_change=closing_debt - opening_debt,
            total_income=0.0,
            total_mandatory_expense=0.0,
            total_urgent_creditcard_repayment=0.0,
        )

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


@app.post("/imports/excel", response_model=ImportResult)
def import_excel(
    file_path: str = "ДОЛГИ.xlsx",
    overwrite: bool = False,
    target_user_id: int | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    import_file = Path(file_path)
    if not import_file.is_absolute():
        import_file = Path.cwd() / import_file
    if not import_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден.")

    target_user = admin if target_user_id is None else db.scalar(select(User).where(User.id == target_user_id))
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Целевой пользователь не найден.")

    wb = openpyxl.load_workbook(import_file, data_only=True)
    ws = wb[wb.sheetnames[0]]

    rows = list(ws.iter_rows(values_only=True))
    income_by_date: dict[date, float] = {}
    for row in rows:
        income_date = _coerce_date(row[14] if len(row) > 14 else None)
        income_amount = _coerce_float(row[13] if len(row) > 13 else None)
        if income_date and income_amount:
            income_by_date[income_date] = income_by_date.get(income_date, 0.0) + income_amount

    inserted = 0
    updated = 0
    skipped = 0

    for row in rows:
        period_date = _coerce_date(row[0] if len(row) > 0 else None)
        debt_total = _coerce_float(row[8] if len(row) > 8 else None)
        if not period_date or debt_total is None:
            continue

        mandatory_expense = _coerce_float(row[7] if len(row) > 7 else None) or 0.0
        urgent_repayment = _coerce_float(row[10] if len(row) > 10 else None) or 0.0
        planned_expense = _coerce_float(row[9] if len(row) > 9 else None) or 0.0
        income = income_by_date.get(period_date, 0.0)

        existing = db.scalar(
            select(FinanceRecord).where(
                FinanceRecord.user_id == target_user.id,
                FinanceRecord.period_date == period_date,
            )
        )
        if existing and not overwrite:
            skipped += 1
            continue

        payload = {
            "income": income,
            "planned_expense": planned_expense,
            "debt_total": debt_total,
            "mandatory_expense": mandatory_expense,
            "urgent_creditcard_repayment": urgent_repayment,
            "comment": "Импорт из Excel",
        }

        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            existing.status = RecordStatus.APPROVED
            existing.approved_by_id = admin.id
            existing.approved_at = datetime.utcnow()
            updated += 1
        else:
            db.add(
                FinanceRecord(
                    user_id=target_user.id,
                    period_date=period_date,
                    status=RecordStatus.APPROVED,
                    approved_by_id=admin.id,
                    approved_at=datetime.utcnow(),
                    **payload,
                )
            )
            inserted += 1

    _log_action(
        db,
        "imports.excel",
        actor_user_id=admin.id,
        target_user_id=target_user.id,
        details=f"file={import_file.name}, inserted={inserted}, updated={updated}, skipped={skipped}",
    )
    db.commit()
    return ImportResult(inserted=inserted, updated=updated, skipped=skipped)


def _build_audit_query(
    action: str | None,
    date_from: date | None,
    date_to: date | None,
    actor_user_id: int | None,
    target_user_id: int | None,
):
    actor_user = aliased(User)
    target_user = aliased(User)
    stmt = (
        select(
            AuditLog,
            actor_user.username.label("actor_username"),
            target_user.username.label("target_username"),
        )
        .outerjoin(actor_user, AuditLog.actor_user_id == actor_user.id)
        .outerjoin(target_user, AuditLog.target_user_id == target_user.id)
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if target_user_id is not None:
        stmt = stmt.where(AuditLog.target_user_id == target_user_id)
    return stmt


def _map_audit_rows(result_rows) -> list[AuditLogRead]:
    return [
        AuditLogRead(
            id=row[0].id,
            action=row[0].action,
            actor_user_id=row[0].actor_user_id,
            actor_username=row[1],
            target_user_id=row[0].target_user_id,
            target_username=row[2],
            details=row[0].details,
            created_at=row[0].created_at,
        )
        for row in result_rows
    ]


@app.get("/audit-logs", response_model=AuditLogPage)
def list_audit_logs(
    action: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    target_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    base_stmt = _build_audit_query(action, date_from, date_to, actor_user_id, target_user_id)
    rows = db.execute(base_stmt).all()
    total_count = len(rows)
    paged_rows = rows[offset : offset + limit]
    return AuditLogPage(
        items=_map_audit_rows(paged_rows),
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@app.get("/audit-logs/export.csv")
def export_audit_logs_csv(
    action: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stmt = _build_audit_query(action, date_from, date_to, actor_user_id, target_user_id)
    stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    logs = _map_audit_rows(db.execute(stmt).all())

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["created_at", "action", "actor_user_id", "actor_username", "target_user_id", "target_username", "details"]
    )
    for item in logs:
        writer.writerow(
            [
                item.created_at.isoformat(),
                item.action,
                item.actor_user_id,
                item.actor_username,
                item.target_user_id,
                item.target_username,
                item.details or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="audit_logs.csv"'},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
