#!/usr/bin/env python3
"""
FM Pro Demo - Model Import
Imports cell data from JSON model into database
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.schema import get_engine, get_session, CellValue, FMVersion


def parse_cell_address(address: str) -> tuple:
    """
    Parse cell address like 'P87' into (column_name, row_num, col_num).

    Returns:
        (col_letters, row_num, col_num) where col_num is 1-based index
    """
    match = re.match(r'^([A-Z]+)(\d+)$', address)
    if not match:
        return (None, None, None)

    col_letters = match.group(1)
    row_num = int(match.group(2))

    # Convert column letters to number (A=1, B=2, ..., Z=26, AA=27, etc.)
    col_num = 0
    for char in col_letters:
        col_num = col_num * 26 + (ord(char) - ord('A') + 1)

    return (col_letters, row_num, col_num)


def load_json_model(json_path: str) -> dict:
    """Load JSON model from file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_base_version(session) -> Optional[FMVersion]:
    """Get the base version (version_number=1)"""
    return session.query(FMVersion).filter_by(version_number=1).first()


def import_cells(
    session,
    model_data: dict,
    version_id: int,
    batch_size: int = 5000
) -> int:
    """
    Import all cells from JSON model into database.

    Args:
        session: Database session
        model_data: Loaded JSON model
        version_id: Version ID to associate cells with
        batch_size: Number of cells to insert per batch

    Returns:
        Total number of cells imported
    """
    total_cells = 0
    batch = []

    for sheet_name, sheet_data in model_data.items():
        cells = sheet_data.get('cells', {})
        sheet_cell_count = 0

        for address, cell_data in cells.items():
            col_letters, row_num, col_num = parse_cell_address(address)
            if row_num is None:
                continue

            # Extract cell properties
            formula = cell_data.get('f')  # Formula
            value = cell_data.get('v')    # Value
            fmt = cell_data.get('fmt')    # Number format

            # Determine calc_value (numeric value if available)
            calc_value = None
            if isinstance(value, (int, float)):
                calc_value = float(value)
            elif value is not None and not isinstance(value, bool):
                # Try to parse string as number
                try:
                    calc_value = float(value)
                except (ValueError, TypeError):
                    pass

            # Create cell record
            cell = CellValue(
                version_id=version_id,
                sheet=sheet_name,
                address=address,
                row_num=row_num,
                col_num=col_num,
                formula=formula,
                calc_value=calc_value,
                number_format=fmt,
                value_type='plan'
            )
            batch.append(cell)
            sheet_cell_count += 1

            # Batch insert
            if len(batch) >= batch_size:
                session.bulk_save_objects(batch)
                session.commit()
                batch = []

        total_cells += sheet_cell_count
        print(f"  {sheet_name}: {sheet_cell_count} cells")

    # Insert remaining batch
    if batch:
        session.bulk_save_objects(batch)
        session.commit()

    return total_cells


def import_model(
    db_path: str = 'fm_demo.db',
    json_path: str = 'fm_model.json',
    clear_existing: bool = True
) -> bool:
    """
    Import JSON model into database.

    Args:
        db_path: Path to SQLite database
        json_path: Path to JSON model file
        clear_existing: If True, delete existing cells before import
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
        # Get base version
        version = get_base_version(session)
        if not version:
            print("Error: Base version not found. Run init_db.py first.")
            return False

        print(f"Importing to version: {version.name} (id={version.id})")

        # Clear existing cells if requested
        if clear_existing:
            deleted = session.query(CellValue).filter_by(
                version_id=version.id
            ).delete()
            session.commit()
            if deleted > 0:
                print(f"Cleared {deleted} existing cells")

        # Import cells
        print("\nImporting cells by sheet:")
        total = import_cells(session, model_data, version.id)

        print(f"\n✅ Import complete!")
        print(f"   Total cells: {total}")

        # Verify key cells
        print("\nVerifying key cells:")

        # Check CF2!P87
        cell = session.query(CellValue).filter_by(
            version_id=version.id,
            sheet='CF2',
            address='P87'
        ).first()
        if cell:
            print(f"  CF2!P87: formula={cell.formula[:50] if cell.formula else 'None'}...")
            print(f"           calc_value={cell.calc_value}")
        else:
            print("  CF2!P87: NOT FOUND (warning)")

        # Check TS1!J85 (key rate)
        cell = session.query(CellValue).filter_by(
            version_id=version.id,
            sheet='TS1',
            address='J85'
        ).first()
        if cell:
            print(f"  TS1!J85 (key rate): {cell.calc_value}")
        else:
            print("  TS1!J85: NOT FOUND (warning)")

        return True

    except Exception as e:
        session.rollback()
        print(f"Error importing: {e}")
        raise
    finally:
        session.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Import JSON model into FM Demo database')
    parser.add_argument('json_path', nargs='?', default='fm_model.json',
                        help='Path to JSON model file')
    parser.add_argument('--db', default='fm_demo.db', help='Database path')
    parser.add_argument('--no-clear', action='store_true',
                        help='Do not clear existing cells before import')

    args = parser.parse_args()

    import_model(args.db, args.json_path, clear_existing=not args.no_clear)


if __name__ == '__main__':
    main()
