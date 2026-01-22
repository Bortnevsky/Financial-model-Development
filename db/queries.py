#!/usr/bin/env python3
"""
FM Pro Demo - Database Queries
Functions for querying cell data with smart context detection
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db.schema import get_engine, get_session, CellValue, FMVersion, Sheet

# Units to skip when searching for labels
SKIP_UNITS = [
    'млн. руб.', 'млн.руб.', 'руб.', 'тыс. руб.', 'тыс.руб.',
    'м2', 'м²', 'м2 Sобщ.', 'кв.м', 'кв. м',
    'шт.', 'ед.', 'кв.', '%',
    'тыс.', 'млн.', 'млрд.',
    'дней', 'мес.', 'лет', 'г.', 'кварт.',
]


def col_to_num(col_letters: str) -> int:
    """Convert column letters to number (A=1, B=2, ..., AA=27)"""
    result = 0
    for char in col_letters.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def num_to_col(n: int) -> str:
    """Convert column number to letters (1=A, 2=B, ..., 27=AA)"""
    result = ''
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def parse_address(address: str) -> tuple:
    """Parse cell address like 'P87' into (col_letters, row_num, col_num)"""
    match = re.match(r'^([A-Z]+)(\d+)$', address.upper())
    if not match:
        return (None, None, None)
    col_letters = match.group(1)
    row_num = int(match.group(2))
    col_num = col_to_num(col_letters)
    return (col_letters, row_num, col_num)


def get_cell_label(
    session,
    version_id: int,
    sheet: str,
    row_num: int,
    col_num: int,
    max_search: int = 20
) -> Optional[str]:
    """
    Find the nearest meaningful text label to the left of a cell.

    Searches leftward in the same row, skipping:
    - Empty cells
    - Cells with formulas
    - Unit labels (млн. руб., м2, %, etc.)

    Args:
        session: Database session
        version_id: Version ID
        sheet: Sheet name
        row_num: Row number
        col_num: Column number (1-based)
        max_search: Maximum columns to search left

    Returns:
        Label text or None if not found
    """
    # Search leftward
    for c in range(col_num - 1, max(0, col_num - max_search - 1), -1):
        col_letter = num_to_col(c)
        address = f"{col_letter}{row_num}"

        cell = session.query(CellValue).filter_by(
            version_id=version_id,
            sheet=sheet,
            address=address
        ).first()

        if not cell:
            continue

        # Skip cells with formulas
        if cell.formula:
            continue

        # Check if cell has a text value (stored as calc_value would be None for text)
        # We need to check the original JSON for text values
        # For now, skip if no meaningful data
        if cell.calc_value is not None:
            # It's a number, skip
            continue

    # If not found in DB, return None
    # The label finding will work better with JSON source
    return None


def get_cell_label_from_json(
    json_data: dict,
    sheet: str,
    row_num: int,
    col_num: int,
    max_search: int = 20
) -> Optional[str]:
    """
    Find the nearest meaningful text label from JSON model.

    This is more reliable than DB because JSON has text values.
    """
    sheet_data = json_data.get(sheet, {})
    cells = sheet_data.get('cells', {})

    for c in range(col_num - 1, max(0, col_num - max_search - 1), -1):
        col_letter = num_to_col(c)
        address = f"{col_letter}{row_num}"

        cell = cells.get(address, {})
        val = cell.get('v', '')

        # Skip if empty, formula, or number
        if not val:
            continue
        if isinstance(val, (int, float, bool)):
            continue
        if isinstance(val, str) and val.startswith('='):
            continue

        # Skip unit labels
        val_stripped = val.strip()
        if val_stripped in SKIP_UNITS:
            continue

        return val_stripped

    return None


def get_cell(
    sheet: str,
    address: str,
    version_id: int = 1,
    db_path: str = 'fm_demo.db',
    json_path: str = 'fm_model.json',
    include_label: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get a cell with all its data and context.

    Args:
        sheet: Sheet name (e.g., 'CF2')
        address: Cell address (e.g., 'P87')
        version_id: Version ID (default 1 = base version)
        db_path: Path to database
        json_path: Path to JSON model (for label detection)
        include_label: Whether to include nearest label

    Returns:
        Dict with cell data:
        {
            'sheet': 'CF2',
            'address': 'P87',
            'formula': '=IF(...)',
            'calc_value': 570.21,
            'override_value': None,
            'final_value': 570.21,
            'value_status': 'calc',
            'label': 'ПОСТУПЛЕНИЕ',  # nearest text label
            'number_format': '#,##0'
        }
    """
    col_letters, row_num, col_num = parse_address(address)
    if row_num is None:
        return None

    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        cell = session.query(CellValue).filter_by(
            version_id=version_id,
            sheet=sheet,
            address=address.upper()
        ).first()

        if not cell:
            return None

        result = {
            'sheet': cell.sheet,
            'address': cell.address,
            'row_num': cell.row_num,
            'col_num': cell.col_num,
            'formula': cell.formula,
            'calc_value': cell.calc_value,
            'override_value': cell.override_value,
            'final_value': cell.final_value,
            'value_status': cell.value_status,
            'number_format': cell.number_format,
            'value_type': cell.value_type,
            'is_locked': cell.is_locked,
        }

        # Find label from JSON
        if include_label:
            try:
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                label = get_cell_label_from_json(json_data, sheet, row_num, col_num)
                result['label'] = label
            except Exception:
                result['label'] = None

        return result

    finally:
        session.close()


def get_sheet_data(
    sheet: str,
    version_id: int = 1,
    db_path: str = 'fm_demo.db',
    row_start: int = None,
    row_end: int = None,
    col_start: int = None,
    col_end: int = None
) -> List[Dict[str, Any]]:
    """
    Get all cells from a sheet (optionally filtered by range).

    Args:
        sheet: Sheet name
        version_id: Version ID
        db_path: Path to database
        row_start, row_end: Row range filter
        col_start, col_end: Column range filter (1-based)

    Returns:
        List of cell dicts
    """
    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        query = session.query(CellValue).filter_by(
            version_id=version_id,
            sheet=sheet
        )

        if row_start is not None:
            query = query.filter(CellValue.row_num >= row_start)
        if row_end is not None:
            query = query.filter(CellValue.row_num <= row_end)
        if col_start is not None:
            query = query.filter(CellValue.col_num >= col_start)
        if col_end is not None:
            query = query.filter(CellValue.col_num <= col_end)

        cells = query.order_by(CellValue.row_num, CellValue.col_num).all()

        return [
            {
                'sheet': c.sheet,
                'address': c.address,
                'row_num': c.row_num,
                'col_num': c.col_num,
                'formula': c.formula,
                'calc_value': c.calc_value,
                'override_value': c.override_value,
                'final_value': c.final_value,
                'value_status': c.value_status,
                'number_format': c.number_format,
            }
            for c in cells
        ]

    finally:
        session.close()


def get_sheet_info(sheet: str, db_path: str = 'fm_demo.db') -> Optional[Dict]:
    """Get sheet metadata"""
    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        sheet_obj = session.query(Sheet).filter_by(name=sheet).first()
        if not sheet_obj:
            return None
        return {
            'name': sheet_obj.name,
            'rows_count': sheet_obj.rows_count,
            'cols_count': sheet_obj.cols_count,
            'description': sheet_obj.description,
        }
    finally:
        session.close()


def list_sheets(db_path: str = 'fm_demo.db') -> List[Dict]:
    """List all sheets"""
    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        sheets = session.query(Sheet).order_by(Sheet.name).all()
        return [
            {
                'name': s.name,
                'rows_count': s.rows_count,
                'cols_count': s.cols_count,
                'description': s.description,
            }
            for s in sheets
        ]
    finally:
        session.close()


def search_cells(
    pattern: str,
    version_id: int = 1,
    db_path: str = 'fm_demo.db',
    search_formulas: bool = True,
    limit: int = 100
) -> List[Dict]:
    """
    Search cells by formula pattern.

    Args:
        pattern: SQL LIKE pattern (e.g., '%IRR%')
        version_id: Version ID
        db_path: Database path
        search_formulas: Search in formulas
        limit: Max results

    Returns:
        List of matching cells
    """
    engine = get_engine(db_path)
    session = get_session(engine)

    try:
        query = session.query(CellValue).filter_by(version_id=version_id)

        if search_formulas:
            query = query.filter(CellValue.formula.like(pattern))

        cells = query.limit(limit).all()

        return [
            {
                'sheet': c.sheet,
                'address': c.address,
                'formula': c.formula,
                'calc_value': c.calc_value,
            }
            for c in cells
        ]

    finally:
        session.close()


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python queries.py <sheet> <address>")
        print("Example: python queries.py DB2 U36")
        sys.exit(1)

    sheet = sys.argv[1]
    address = sys.argv[2]

    cell = get_cell(sheet, address)
    if cell:
        print(f"\n=== {sheet}!{address} ===")
        print(f"Label: {cell.get('label', 'N/A')}")
        print(f"Formula: {cell.get('formula', 'N/A')}")
        print(f"Calc value: {cell.get('calc_value', 'N/A')}")
        print(f"Final value: {cell.get('final_value', 'N/A')}")
        print(f"Status: {cell.get('value_status', 'N/A')}")
        print(f"Format: {cell.get('number_format', 'N/A')}")
    else:
        print(f"Cell not found: {sheet}!{address}")
