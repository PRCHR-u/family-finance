"""
Утилиты для анализа долгов и планирования бюджета.
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Debt, DebtRepayment, Expense, FinanceRecord, Income, RecordStatus, User, UserRole


def get_debt_change_analysis(
    db: Session,
    current_user: User,
    period_from: date,
    period_to: date,
) -> dict:
    """
    Анализирует прирост и уменьшение долга за указанный период.
    
    Возвращает детальную информацию об изменении долгов:
    - opening_debt: долг на начало периода
    - closing_debt: долг на конец периода
    - debt_change: абсолютное изменение долга
    - new_debts: новые долги, созданные в периоде
    - repayments: платежи по долгам в периоде
    - debt_increase: сумма новых долгов
    - debt_decrease: сумма погашений
    - net_change: чистое изменение (увеличение - уменьшение)
    """
    # Долг на день до начала периода
    day_before = period_from.fromordinal(period_from.toordinal() - 1)
    opening_debt = _debt_total_as_of(db, current_user, day_before)
    closing_debt = _debt_total_as_of(db, current_user, period_to)
    
    # Новые долги, созданные в периоде
    new_debts_stmt = select(Debt).where(
        Debt.moderation_status == RecordStatus.APPROVED,
        Debt.start_date >= period_from,
        Debt.start_date <= period_to,
    )
    if current_user.role != UserRole.ADMIN:
        new_debts_stmt = new_debts_stmt.where(Debt.user_id == current_user.id)
    
    new_debts = db.scalars(new_debts_stmt.order_by(Debt.start_date)).all()
    debt_increase = sum(debt.principal_amount for debt in new_debts)
    
    # Платежи по долгам в периоде
    repayments_stmt = select(DebtRepayment).where(
        DebtRepayment.moderation_status == RecordStatus.APPROVED,
        DebtRepayment.payment_date >= period_from,
        DebtRepayment.payment_date <= period_to,
    )
    if current_user.role != UserRole.ADMIN:
        repayments_stmt = repayments_stmt.where(DebtRepayment.user_id == current_user.id)
    
    repayments = db.scalars(repayments_stmt.order_by(DebtRepayment.payment_date)).all()
    debt_decrease = sum(rep.amount for rep in repayments)
    
    # Чистое изменение
    net_change = debt_increase - debt_decrease
    
    return {
        "period_from": period_from,
        "period_to": period_to,
        "opening_debt": opening_debt,
        "closing_debt": closing_debt,
        "debt_change": closing_debt - opening_debt,
        "new_debts": [
            {
                "id": debt.id,
                "creditor_name": debt.creditor_name,
                "principal_amount": debt.principal_amount,
                "start_date": debt.start_date,
            }
            for debt in new_debts
        ],
        "repayments": [
            {
                "id": rep.id,
                "debt_id": rep.debt_id,
                "amount": rep.amount,
                "payment_date": rep.payment_date,
                "comment": rep.comment,
            }
            for rep in repayments
        ],
        "debt_increase": debt_increase,
        "debt_decrease": debt_decrease,
        "net_change": net_change,
    }


def _debt_total_as_of(db: Session, current_user: User, as_of: date) -> float:
    """Вычисляет общую сумму долга на указанную дату."""
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


def calculate_weekly_budget(
    db: Session,
    current_user: User,
    reference_date: Optional[date] = None,
    weeks_ahead: int = 1,
) -> dict:
    """
    Рассчитывает недельный бюджет на основе анализа расходов.
    
    Анализирует:
    - Обязательные расходы (mandatory expenses)
    - Запланированные траты из finance records
    - Доходы за период
    
    Параметры:
    - reference_date: дата, с которой начинается расчет (по умолчанию сегодня)
    - weeks_ahead: количество недель для планирования (по умолчанию 1)
    
    Возвращает:
    - weekly_budget: общий бюджет на неделю
    - daily_budget: средний дневной бюджет
    - mandatory_expenses: обязательные расходы
    - planned_expenses: запланированные расходы
    - available_income: доступный доход
    - recommendation: рекомендация по бюджету
    """
    from calendar import monthrange
    
    if reference_date is None:
        reference_date = date.today()
    
    # Определяем начало недели (понедельник)
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    end_of_week = start_of_week + timedelta(days=7 * weeks_ahead - 1)
    
    # Получаем обязательные расходы на этот период
    mandatory_expenses_stmt = select(Expense).where(
        Expense.user_id == current_user.id if current_user.role != UserRole.ADMIN else True,
        Expense.is_mandatory == True,
        Expense.is_completed == False,
        Expense.due_date >= start_of_week,
        Expense.due_date <= end_of_week,
    )
    mandatory_expenses = db.scalars(mandatory_expenses_stmt).all()
    total_mandatory = sum(e.amount for e in mandatory_expenses)
    
    # Получаем доходы за период
    income_stmt = select(Income).where(
        Income.user_id == current_user.id if current_user.role != UserRole.ADMIN else True,
        Income.moderation_status == RecordStatus.APPROVED,
        Income.income_date >= start_of_week,
        Income.income_date <= end_of_week,
    )
    incomes = db.scalars(income_stmt).all()
    total_income = sum(i.amount for i in incomes)
    
    # Получаем последние финансовые записи для оценки обычных расходов
    finance_records_stmt = select(FinanceRecord).where(
        FinanceRecord.status == RecordStatus.APPROVED,
        FinanceRecord.period_date <= reference_date,
    )
    if current_user.role != UserRole.ADMIN:
        finance_records_stmt = finance_records_stmt.where(FinanceRecord.user_id == current_user.id)
    
    finance_records = db.scalars(
        finance_records_stmt.order_by(FinanceRecord.period_date.desc()).limit(4)
    ).all()
    
    # Средние плановые расходы за последние периоды
    avg_planned_expense = 0.0
    if finance_records:
        avg_planned_expense = sum(r.planned_expense for r in finance_records) / len(finance_records)
    
    # Общий бюджет на неделю
    weekly_budget = total_mandatory + avg_planned_expense
    
    # Дневной бюджет
    daily_budget = weekly_budget / (7 * weeks_ahead)
    
    # Доступный доход (доходы за период + остаток от предыдущих периодов)
    available_income = total_income
    
    # Рекомендация
    if available_income >= weekly_budget:
        surplus = available_income - weekly_budget
        recommendation = f"Бюджет сбалансирован. Излишек: {surplus:.2f}. Рекомендуется направить на погашение долгов или сбережения."
    else:
        deficit = weekly_budget - available_income
        recommendation = f"Внимание! Дефицит бюджета: {deficit:.2f}. Рекомендуется сократить необязательные расходы."
    
    return {
        "period_start": start_of_week,
        "period_end": end_of_week,
        "weeks_count": weeks_ahead,
        "weekly_budget": weekly_budget,
        "daily_budget": daily_budget,
        "mandatory_expenses": {
            "total": total_mandatory,
            "count": len(mandatory_expenses),
            "items": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": e.amount,
                    "due_date": e.due_date,
                    "category": e.category.value if e.category else None,
                }
                for e in mandatory_expenses
            ],
        },
        "planned_expenses": {
            "average_weekly": avg_planned_expense,
        },
        "income": {
            "total": total_income,
            "count": len(incomes),
            "items": [
                {
                    "id": i.id,
                    "description": i.description,
                    "amount": i.amount,
                    "income_date": i.income_date,
                    "category": i.category.value if i.category else None,
                }
                for i in incomes
            ],
        },
        "available_income": available_income,
        "balance": available_income - weekly_budget,
        "recommendation": recommendation,
    }


def calculate_daily_budget(
    db: Session,
    current_user: User,
    target_date: Optional[date] = None,
) -> dict:
    """
    Рассчитывает ежедневный бюджет на конкретный день.
    
    Учитывает:
    - Обязательные расходы на этот день
    - Пропорциональную часть недельного бюджета
    - Доступные средства
    
    Параметры:
    - target_date: дата расчета (по умолчанию сегодня)
    
    Возвращает:
    - date: дата расчета
    - mandatory_expenses: обязательные расходы на день
    - discretionary_budget: дискреционный бюджет (на необязательные траты)
    - total_budget: общий бюджет на день
    - recommendations: рекомендации
    """
    if target_date is None:
        target_date = date.today()
    
    # Обязательные расходы на конкретный день
    mandatory_expenses_stmt = select(Expense).where(
        Expense.user_id == current_user.id if current_user.role != UserRole.ADMIN else True,
        Expense.is_mandatory == True,
        Expense.is_completed == False,
        Expense.due_date == target_date,
    )
    mandatory_expenses = db.scalars(mandatory_expenses_stmt).all()
    total_mandatory = sum(e.amount for e in mandatory_expenses)
    
    # Получаем недельный бюджет для расчета дневной пропорции
    weekly_data = calculate_weekly_budget(db, current_user, target_date, weeks_ahead=1)
    base_daily_budget = weekly_data["daily_budget"]
    
    # Дискреционный бюджет (после обязательных трат)
    discretionary_budget = base_daily_budget - total_mandatory
    
    # Рекомендации
    recommendations = []
    if discretionary_budget > 0:
        recommendations.append(f"Свободных средств на день: {discretionary_budget:.2f}")
        if discretionary_budget > base_daily_budget * 0.5:
            recommendations.append("Хороший день для дополнительных покупок или досуга.")
    elif discretionary_budget < 0:
        recommendations.append(f"Превышение обязательных расходов на {-discretionary_budget:.2f}")
        recommendations.append("Рекомендуется пересмотреть планы на день или использовать резерв.")
    else:
        recommendations.append("Все средства распределены на обязательные расходы.")
    
    # Проверка на особые даты (конец месяца, зарплата и т.д.)
    if target_date.day == 1:
        recommendations.append("Начало месяца - спланируйте крупные обязательные платежи.")
    if target_date.day in [10, 11, 12]:  # Примерные даты зарплаты
        recommendations.append("Возможное поступление дохода - обновите данные о доходах.")
    
    return {
        "date": target_date,
        "mandatory_expenses": {
            "total": total_mandatory,
            "count": len(mandatory_expenses),
            "items": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": e.amount,
                    "category": e.category.value if e.category else None,
                }
                for e in mandatory_expenses
            ],
        },
        "base_daily_budget": base_daily_budget,
        "discretionary_budget": discretionary_budget,
        "total_budget": base_daily_budget,
        "recommendations": recommendations,
    }


def get_budget_summary(
    db: Session,
    current_user: User,
    period_from: date,
    period_to: date,
) -> dict:
    """
    Сводная информация о бюджете за период.
    
    Объединяет анализ долгов и бюджетирование.
    """
    debt_analysis = get_debt_change_analysis(db, current_user, period_from, period_to)
    weekly_budget = calculate_weekly_budget(db, current_user, period_from, weeks_ahead=1)
    
    days_in_period = (period_to - period_from).days + 1
    weeks_in_period = max(1, days_in_period // 7)
    
    return {
        "period": {
            "from": period_from,
            "to": period_to,
            "days": days_in_period,
            "weeks": weeks_in_period,
        },
        "debt_analysis": debt_analysis,
        "budget_overview": {
            "weekly_average": weekly_budget["weekly_budget"],
            "daily_average": weekly_budget["daily_budget"],
            "total_mandatory_expenses": debt_analysis.get("total_mandatory_expense", 0),
        },
        "financial_health": {
            "debt_trend": "increasing" if debt_analysis["net_change"] > 0 else "decreasing" if debt_analysis["net_change"] < 0 else "stable",
            "budget_balance": "surplus" if weekly_budget["balance"] > 0 else "deficit" if weekly_budget["balance"] < 0 else "balanced",
        },
    }
