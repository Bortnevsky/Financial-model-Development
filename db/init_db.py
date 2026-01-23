#!/usr/bin/env python3
"""
FM Pro Demo - Database Initialization
Creates SQLite database with all tables and views
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from db.schema import (
    Base, get_engine, get_session, create_all_tables,
    CELLS_FINAL_VIEW_SQL, Project, Sheet, FMVersion
)


def init_database(db_path: str = 'fm_demo.db', force: bool = False):
    """
    Initialize the FM Demo database.

    Args:
        db_path: Path to SQLite database file
        force: If True, delete existing database and recreate
    """
    # Handle existing database
    if os.path.exists(db_path):
        if force:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        else:
            print(f"Database already exists: {db_path}")
            print("Use --force to recreate")
            return False

    # Create engine and tables
    print(f"Creating database: {db_path}")
    engine = create_all_tables(db_path=db_path)

    # Create view
    with engine.connect() as conn:
        conn.execute(text(CELLS_FINAL_VIEW_SQL))
        conn.commit()
    print("Created cells_final view")

    # Create default project and version
    session = get_session(engine)
    try:
        # Default project
        project = Project(
            code='KASATKINA2',
            name='ФМ Касаткина 2',
            excel_file='FM_Касаткина2.xlsx'
        )
        session.add(project)
        session.flush()  # Get project.id

        # Base version
        version = FMVersion(
            project_id=project.id,
            version_number=1,
            name='Базовая',
            description='Исходная версия из Excel',
            is_scenario=False,
            is_active=True
        )
        session.add(version)

        session.commit()
        print(f"Created project: {project.name}")
        print(f"Created base version: {version.name}")

    except Exception as e:
        session.rollback()
        print(f"Error creating default data: {e}")
        raise
    finally:
        session.close()

    print(f"\n✅ Database initialized successfully: {db_path}")
    return True


def list_tables(db_path: str = 'fm_demo.db'):
    """List all tables in database"""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
    views = cursor.fetchall()

    conn.close()

    print("\nTables:")
    for t in tables:
        print(f"  - {t[0]}")

    print("\nViews:")
    for v in views:
        print(f"  - {v[0]}")

    return tables, views


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Initialize FM Demo database')
    parser.add_argument('--db', default='fm_demo.db', help='Database path')
    parser.add_argument('--force', action='store_true', help='Force recreate database')
    parser.add_argument('--list', action='store_true', help='List tables only')

    args = parser.parse_args()

    if args.list:
        if os.path.exists(args.db):
            list_tables(args.db)
        else:
            print(f"Database not found: {args.db}")
        return

    init_database(args.db, force=args.force)

    # Show tables
    if os.path.exists(args.db):
        list_tables(args.db)


if __name__ == '__main__':
    main()
