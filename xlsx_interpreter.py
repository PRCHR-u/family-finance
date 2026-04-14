#!/usr/bin/env python3
"""
XLSX Interpreter - Универсальная утилита для работы с Excel файлами
Поддерживает чтение, просмотр, конвертацию и базовую обработку данных
"""

import pandas as pd
import json
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any


class XLSXInterpreter:
    """Класс для интерпретации и обработки XLSX файлов"""
    
    def __init__(self, file_path: str):
        """
        Инициализация интерпретатора
        
        Args:
            file_path: Путь к XLSX файлу
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        self.xlsx_file = pd.ExcelFile(self.file_path)
        self.sheet_names = self.xlsx_file.sheet_names
    
    def get_info(self) -> Dict[str, Any]:
        """Получить общую информацию о файле"""
        info = {
            'filename': self.file_path.name,
            'path': str(self.file_path.absolute()),
            'sheet_count': len(self.sheet_names),
            'sheets': []
        }
        
        for sheet in self.sheet_names:
            df = pd.read_excel(self.xlsx_file, sheet_name=sheet)
            sheet_info = {
                'name': sheet,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            info['sheets'].append(sheet_info)
        
        return info
    
    def read_sheet(self, sheet_name: Optional[str] = None, 
                   nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Прочитать лист из Excel файла
        
        Args:
            sheet_name: Имя листа (по умолчанию первый лист)
            nrows: Количество строк для чтения (по умолчанию все)
            
        Returns:
            DataFrame с данными
        """
        if sheet_name is None:
            sheet_name = self.sheet_names[0]
        
        if sheet_name not in self.sheet_names:
            raise ValueError(f"Лист '{sheet_name}' не найден. Доступные листы: {self.sheet_names}")
        
        df = pd.read_excel(self.xlsx_file, sheet_name=sheet_name, nrows=nrows)
        return df
    
    def to_dict(self, sheet_name: Optional[str] = None, 
                orient: str = 'records') -> List[Dict]:
        """
        Конвертировать лист в список словарей
        
        Args:
            sheet_name: Имя листа
            orient: Формат ориентации данных ('records', 'list', 'split', etc.)
            
        Returns:
            Список словарей с данными
        """
        df = self.read_sheet(sheet_name)
        return df.to_dict(orient=orient)
    
    def to_json(self, sheet_name: Optional[str] = None, 
                indent: int = 2, 
                output_file: Optional[str] = None) -> str:
        """
        Конвертировать лист в JSON
        
        Args:
            sheet_name: Имя листа
            indent: Отступ для форматирования
            output_file: Путь для сохранения файла (опционально)
            
        Returns:
            JSON строка
        """
        data = self.to_dict(sheet_name)
        json_str = json.dumps(data, ensure_ascii=False, indent=indent, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"Данные сохранены в файл: {output_file}")
        
        return json_str
    
    def to_csv(self, sheet_name: Optional[str] = None,
               output_file: Optional[str] = None,
               sep: str = ',') -> str:
        """
        Конвертировать лист в CSV
        
        Args:
            sheet_name: Имя листа
            output_file: Путь для сохранения файла
            sep: Разделитель колонок
            
        Returns:
            CSV строка
        """
        df = self.read_sheet(sheet_name)
        csv_str = df.to_csv(index=False, sep=sep)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_str)
            print(f"Данные сохранены в файл: {output_file}")
        
        return csv_str
    
    def filter_data(self, sheet_name: Optional[str] = None,
                    column: str = None,
                    value: Any = None,
                    condition: str = 'eq') -> pd.DataFrame:
        """
        Фильтровать данные по условию
        
        Args:
            sheet_name: Имя листа
            column: Колонка для фильтрации
            value: Значение для сравнения
            condition: Условие ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'contains')
            
        Returns:
            Отфильтрованный DataFrame
        """
        df = self.read_sheet(sheet_name)
        
        if column is None or value is None:
            return df
        
        if column not in df.columns:
            raise ValueError(f"Колонка '{column}' не найдена. Доступные колонки: {list(df.columns)}")
        
        if condition == 'eq':
            result = df[df[column] == value]
        elif condition == 'ne':
            result = df[df[column] != value]
        elif condition == 'gt':
            result = df[df[column] > value]
        elif condition == 'lt':
            result = df[df[column] < value]
        elif condition == 'ge':
            result = df[df[column] >= value]
        elif condition == 'le':
            result = df[df[column] <= value]
        elif condition == 'contains':
            result = df[df[column].astype(str).str.contains(str(value), na=False)]
        else:
            raise ValueError(f"Неизвестное условие: {condition}")
        
        return result
    
    def get_statistics(self, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить статистику по числовым колонкам
        
        Args:
            sheet_name: Имя листа
            
        Returns:
            Словарь со статистикой
        """
        df = self.read_sheet(sheet_name)
        numeric_df = df.select_dtypes(include=['number'])
        
        if numeric_df.empty:
            return {'message': 'Нет числовых колонок'}
        
        stats = {}
        for col in numeric_df.columns:
            stats[col] = {
                'count': int(numeric_df[col].count()),
                'mean': float(numeric_df[col].mean()) if not pd.isna(numeric_df[col].mean()) else None,
                'min': float(numeric_df[col].min()) if not pd.isna(numeric_df[col].min()) else None,
                'max': float(numeric_df[col].max()) if not pd.isna(numeric_df[col].max()) else None,
                'sum': float(numeric_df[col].sum()) if not pd.isna(numeric_df[col].sum()) else None,
                'std': float(numeric_df[col].std()) if not pd.isna(numeric_df[col].std()) else None
            }
        
        return stats
    
    def close(self):
        """Закрыть файл"""
        self.xlsx_file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def print_table(df: pd.DataFrame, max_rows: int = 20, max_col_width: int = 30):
    """Красиво вывести DataFrame в виде таблицы"""
    if len(df) > max_rows:
        df_display = pd.concat([df.head(max_rows // 2), df.tail(max_rows // 2)])
        print(f"\n... показаны первые и последние {max_rows // 2} строк из {len(df)} ...\n")
    else:
        df_display = df
    
    # Ограничиваем ширину колонок
    with pd.option_context('display.max_colwidth', max_col_width):
        print(df_display.to_string())


def main():
    parser = argparse.ArgumentParser(
        description='XLSX Interpreter - Утилита для работы с Excel файлами',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s file.xlsx --info                    # Показать информацию о файле
  %(prog)s file.xlsx --view                    # Просмотреть данные первого листа
  %(prog)s file.xlsx --view --sheet "Sheet1"   # Просмотреть конкретный лист
  %(prog)s file.xlsx --to-json output.json     # Конвертировать в JSON
  %(prog)s file.xlsx --to-csv output.csv       # Конвертировать в CSV
  %(prog)s file.xlsx --stats                   # Показать статистику
  %(prog)s file.xlsx --filter --column "Name" --value "John"  # Фильтрация
        """
    )
    
    parser.add_argument('file', help='Путь к XLSX файлу')
    parser.add_argument('--info', action='store_true', help='Показать информацию о файле')
    parser.add_argument('--view', action='store_true', help='Просмотреть данные')
    parser.add_argument('--sheet', type=str, help='Имя листа для работы')
    parser.add_argument('--head', type=int, default=None, help='Показать только N первых строк')
    parser.add_argument('--to-json', type=str, metavar='FILE', help='Конвертировать в JSON файл')
    parser.add_argument('--to-csv', type=str, metavar='FILE', help='Конвертировать в CSV файл')
    parser.add_argument('--stats', action='store_true', help='Показать статистику по числовым колонкам')
    parser.add_argument('--filter', action='store_true', help='Режим фильтрации')
    parser.add_argument('--column', type=str, help='Колонка для фильтрации')
    parser.add_argument('--value', type=str, help='Значение для фильтрации')
    parser.add_argument('--condition', type=str, default='eq',
                        choices=['eq', 'ne', 'gt', 'lt', 'ge', 'le', 'contains'],
                        help='Условие фильтрации (по умолчанию: eq)')
    
    args = parser.parse_args()
    
    try:
        with XLSXInterpreter(args.file) as interpreter:
            # Информация о файле
            if args.info or not any([args.view, args.to_json, args.to_csv, args.stats]):
                info = interpreter.get_info()
                print(f"\n📊 Файл: {info['filename']}")
                print(f"📁 Путь: {info['path']}")
                print(f"📑 Листов: {info['sheet_count']}")
                print("\nЛисты:")
                for i, sheet in enumerate(info['sheets'], 1):
                    print(f"\n  {i}. {sheet['name']}")
                    print(f"     Строк: {sheet['rows']}, Колонок: {sheet['columns']}")
                    print(f"     Колонки: {', '.join(sheet['column_names'][:10])}" + 
                          ("..." if len(sheet['column_names']) > 10 else ""))
            
            # Просмотр данных
            if args.view:
                df = interpreter.read_sheet(args.sheet, nrows=args.head)
                print(f"\n📄 Лист: {args.sheet or interpreter.sheet_names[0]}")
                print(f"Строк: {len(df)}, Колонок: {len(df.columns)}\n")
                print_table(df, max_rows=args.head or 20)
            
            # Конвертация в JSON
            if args.to_json:
                interpreter.to_json(args.sheet, output_file=args.to_json)
                print(f"✅ Данные успешно конвертированы в {args.to_json}")
            
            # Конвертация в CSV
            if args.to_csv:
                interpreter.to_csv(args.sheet, output_file=args.to_csv)
                print(f"✅ Данные успешно конвертированы в {args.to_csv}")
            
            # Статистика
            if args.stats:
                stats = interpreter.get_statistics(args.sheet)
                print(f"\n📈 Статистика по числовым колонкам:")
                if 'message' in stats:
                    print(f"  {stats['message']}")
                else:
                    for col, data in stats.items():
                        print(f"\n  {col}:")
                        for key, val in data.items():
                            if val is not None:
                                print(f"    {key}: {val:.2f}" if isinstance(val, float) else f"    {key}: {val}")
            
            # Фильтрация
            if args.filter and args.column and args.value:
                df_filtered = interpreter.filter_data(
                    args.sheet, 
                    args.column, 
                    args.value, 
                    args.condition
                )
                print(f"\n🔍 Результат фильтрации ({len(df_filtered)} строк):")
                print_table(df_filtered)
            
    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
