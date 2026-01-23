#!/usr/bin/env python3
"""
FM Pro Demo - Seed Data
Extracts indicators and sheets from JSON model and populates database
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.schema import get_engine, get_session, Sheet, Indicator


def load_json_model(json_path: str) -> dict:
    """Load JSON model from file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed_sheets(session, model_data: dict) -> Dict[str, Sheet]:
    """
    Populate sheets table from JSON model.

    Returns dict of sheet_name -> Sheet object
    """
    print("Seeding sheets...")
    sheets = {}

    # Sheet descriptions
    descriptions = {
        'МАСТЕР ПЛАН': 'Мастер-план проекта, варианты распределения площадей',
        'RESUME': 'Резюме изменений проекта',
        'DB': 'Dashboard - основные показатели проекта',
        'DB1': 'Dashboard детализация (часть 1)',
        'DB2': 'Dashboard детализация (часть 2) - ТЭПы',
        'CF': 'Cash Flow общий',
        'CF1': 'Cash Flow детализация (часть 1)',
        'CF2': 'Cash Flow детализация (часть 2)',
        'TS1': 'Timeline Schedule (часть 1) - графики и ставки',
        'TS2': 'Timeline Schedule (часть 2)',
        'DETAILS': 'Детализация расходов по статьям',
        'FACT': 'Загрузка фактических данных',
        'БИТ': 'БИТ-финанс интеграция',
        'CONTRACT': 'Контракты',
        'ПРОДАЖИ': 'План продаж по периодам',
        'СОЦИАЛКА': 'Социальные объекты'
    }

    for sheet_name, sheet_data in model_data.items():
        sheet = Sheet(
            name=sheet_name,
            rows_count=sheet_data.get('rows', 0),
            cols_count=sheet_data.get('cols', 0),
            description=descriptions.get(sheet_name, '')
        )
        session.add(sheet)
        sheets[sheet_name] = sheet
        print(f"  Added sheet: {sheet_name} ({sheet_data.get('rows', 0)} rows)")

    session.commit()
    return sheets


def extract_indicators_from_sheet(
    sheet_name: str,
    cells: dict,
    section_markers: Optional[List[str]] = None
) -> List[dict]:
    """
    Extract indicators from column B of a sheet.

    Indicators are text values in column B that serve as row labels.
    Section markers help categorize indicators into groups.
    """
    indicators = []
    current_section = None

    # Default section markers (uppercase words that define sections)
    if section_markers is None:
        section_markers = [
            'КОНТРАКТАЦИЯ', 'ЦЕНЫ', 'ПОСТУПЛЕНИЯ', 'РАСХОДЫ', 'ФИНАНСИРОВАНИЕ',
            'ИТОГО', 'НАЛОГИ', 'ПРИБЫЛЬ', 'ИНВЕСТИЦИИ', 'ПРОДАЖИ', 'ПЛОЩАДИ',
            'ТЭПы', 'НАЗЕМНАЯ', 'ПОДЗЕМНАЯ', 'ВХОД', 'ВЫХОД'
        ]

    # Get all B column cells
    b_cells = {}
    for addr, cell in cells.items():
        if addr.startswith('B') and addr[1:].isdigit():
            row_num = int(addr[1:])
            value = cell.get('v', '')

            # Skip formulas (they reference other cells)
            if isinstance(value, str) and value.startswith('='):
                continue

            # Skip empty or numeric values
            if not value or isinstance(value, (int, float)):
                continue

            b_cells[row_num] = str(value).strip()

    # Process cells in row order
    for row_num in sorted(b_cells.keys()):
        name = b_cells[row_num]

        # Skip very short names
        if len(name) < 2:
            continue

        # Check if this is a section marker
        name_upper = name.upper()
        is_section = any(marker in name_upper for marker in section_markers)

        if is_section and len(name) > 3:
            current_section = name
            # Section headers can also be indicators (like "ИТОГО")
            if any(total in name_upper for total in ['ИТОГО', 'ВСЕГО', 'TOTAL']):
                indicators.append({
                    'name': name,
                    'sheet': sheet_name,
                    'row_num': row_num,
                    'code': f'B{row_num}',
                    'section': current_section,
                    'indicator_type': 'sum'
                })
        else:
            # Determine indicator type
            indicator_type = 'formula'  # default
            if '%' in name:
                indicator_type = 'rate'
            elif any(input_word in name_upper for input_word in ['ВВОД', 'ВХОД', 'ПАРАМЕТР']):
                indicator_type = 'input'

            indicators.append({
                'name': name,
                'sheet': sheet_name,
                'row_num': row_num,
                'code': f'B{row_num}',
                'section': current_section,
                'indicator_type': indicator_type
            })

    return indicators


def seed_indicators(session, model_data: dict) -> int:
    """
    Populate indicators table from JSON model.

    Extracts indicator names from column B of key sheets.
    Returns number of indicators created.
    """
    print("\nSeeding indicators...")

    # Sheets to extract indicators from (order matters for deduplication)
    key_sheets = ['DB2', 'DB', 'CF2', 'CF', 'TS1', 'ПРОДАЖИ', 'DETAILS']

    all_indicators = []
    seen_names = set()  # Track unique names per sheet

    for sheet_name in key_sheets:
        if sheet_name not in model_data:
            continue

        cells = model_data[sheet_name].get('cells', {})
        indicators = extract_indicators_from_sheet(sheet_name, cells)

        for ind in indicators:
            # Create unique key per sheet+name
            key = (sheet_name, ind['name'])
            if key not in seen_names:
                seen_names.add(key)
                all_indicators.append(ind)

    # Insert indicators
    count = 0
    for ind_data in all_indicators:
        indicator = Indicator(
            code=ind_data['code'],
            name=ind_data['name'],
            sheet=ind_data['sheet'],
            row_num=ind_data['row_num'],
            section=ind_data.get('section'),
            indicator_type=ind_data.get('indicator_type', 'formula'),
            allow_override=True,
            allow_distribution=ind_data.get('indicator_type') != 'sum'
        )
        session.add(indicator)
        count += 1

    session.commit()
    print(f"  Added {count} indicators from {len(key_sheets)} sheets")

    # Print summary by sheet
    print("\n  Summary by sheet:")
    from sqlalchemy import func
    for sheet_name, cnt in session.query(
        Indicator.sheet, func.count(Indicator.id)
    ).group_by(Indicator.sheet).all():
        print(f"    {sheet_name}: {cnt} indicators")

    return count


def seed_all(db_path: str = 'fm_demo.db', json_path: str = 'fm_model.json'):
    """
    Seed all reference data into database.
    """
    if not os.path.exists(json_path):
        print(f"Error: JSON model not found: {json_path}")
        return False

    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        print("Run 'python db/init_db.py' first")
        return False

    print(f"Loading model from: {json_path}")
    model_data = load_json_model(json_path)
    print(f"Found {len(model_data)} sheets")

    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        # Seed sheets
        sheets = seed_sheets(session, model_data)

        # Seed indicators
        indicator_count = seed_indicators(session, model_data)

        print(f"\n✅ Seeding complete!")
        print(f"   Sheets: {len(sheets)}")
        print(f"   Indicators: {indicator_count}")

        return True

    except Exception as e:
        session.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        session.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Seed FM Demo database with reference data')
    parser.add_argument('--db', default='fm_demo.db', help='Database path')
    parser.add_argument('--json', default='fm_model.json', help='JSON model path')

    args = parser.parse_args()

    seed_all(args.db, args.json)


if __name__ == '__main__':
    main()
