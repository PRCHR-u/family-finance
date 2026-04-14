#!/usr/bin/env python3
"""
Тестовый скрипт для проверки импорта XLSX файлов в базу данных
"""

import pandas as pd
from datetime import date, timedelta
import random

# Создаём тестовый файл с долгами
print("Создание тестового XLSX файла...")

data = {
    'creditor': ['СБЕР', 'Альфа-Банк', 'Тинькофф', 'ВТБ', 'МТС Банк'],
    'principal_amount': [100000, 50000, 75000, 30000, 25000],
    'start_date': [
        (date.today() - timedelta(days=30)).isoformat(),
        (date.today() - timedelta(days=60)).isoformat(),
        (date.today() - timedelta(days=90)).isoformat(),
        (date.today() - timedelta(days=15)).isoformat(),
        (date.today() - timedelta(days=45)).isoformat(),
    ],
    'planned_payoff_date': [
        (date.today() + timedelta(days=180)).isoformat(),
        (date.today() + timedelta(days=120)).isoformat(),
        (date.today() + timedelta(days=200)).isoformat(),
        (date.today() + timedelta(days=90)).isoformat(),
        (date.today() + timedelta(days=150)).isoformat(),
    ],
    'interest_rate': [12.5, 15.0, 18.0, 11.0, 16.5],
    'comment': ['Ипотека', 'Кредит наличными', 'Кредитная карта', 'Автокредит', 'Потребительский кредит']
}

df = pd.DataFrame(data)
output_file = 'test_debts.xlsx'
df.to_excel(output_file, index=False)
print(f"✅ Файл {output_file} создан!")
print(f"📊 Строк: {len(df)}")
print(f"📋 Колонки: {list(df.columns)}")
print("\nПример данных:")
print(df.head())
