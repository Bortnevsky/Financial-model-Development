"""
FM Pro Demo - Database Schema
SQLAlchemy models for financial model storage
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Text, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Project(Base):
    """Projects table - каждый проект = один файл модели"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    excel_file = Column(String(255))  # путь к исходному Excel
    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("FMVersion", back_populates="project")


class Sheet(Base):
    """Sheets table - листы модели"""
    __tablename__ = 'sheets'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    rows_count = Column(Integer)
    cols_count = Column(Integer)
    description = Column(Text)


class Indicator(Base):
    """Indicators table - справочник показателей"""
    __tablename__ = 'indicators'

    id = Column(Integer, primary_key=True)
    code = Column(String(20))  # "B87", "B97"
    name = Column(String(255), nullable=False)  # "ПОСТУПЛЕНИЕ", "% КРЕДИТ"
    sheet = Column(String(50), nullable=False, index=True)
    row_num = Column(Integer)
    section = Column(String(255))  # "ФИНАНСИРОВАНИЕ"
    indicator_type = Column(String(20))  # "input", "formula", "sum"
    allow_override = Column(Boolean, default=True)
    allow_distribution = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_indicators_sheet_row', 'sheet', 'row_num'),
    )


class FMVersion(Base):
    """FM Versions table - версии модели"""
    __tablename__ = 'fm_versions'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    version_number = Column(Integer, nullable=False)
    name = Column(String(255))  # "Базовая", "Сценарий КС+5%"
    description = Column(Text)
    is_scenario = Column(Boolean, default=False)
    parent_version_id = Column(Integer, ForeignKey('fm_versions.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="versions")
    parent_version = relationship("FMVersion", remote_side=[id])
    cells = relationship("CellValue", back_populates="version")


class CellValue(Base):
    """Cell Values table - главная таблица с данными ячеек"""
    __tablename__ = 'cell_values'

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('fm_versions.id'), index=True)
    sheet = Column(String(50), nullable=False, index=True)
    address = Column(String(20), nullable=False)  # "P87"
    row_num = Column(Integer)
    col_num = Column(Integer)

    # Три слоя значений
    formula = Column(Text)  # "=IF(P5<'DB2'!$U$25,...)"
    calc_value = Column(Float)  # расчётное значение
    override_value = Column(Float)  # ручное значение

    # Метаданные
    value_type = Column(String(20))  # "plan", "fact", "forecast"
    number_format = Column(String(50))  # "#,##0"
    is_locked = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    version = relationship("FMVersion", back_populates="cells")
    events = relationship("CellEvent", back_populates="cell")

    __table_args__ = (
        UniqueConstraint('version_id', 'sheet', 'address', name='uq_cell_version_sheet_address'),
        Index('idx_cells_sheet_address', 'sheet', 'address'),
    )

    @property
    def final_value(self):
        """Итоговое значение: override если есть, иначе calc"""
        if self.override_value is not None:
            return self.override_value
        return self.calc_value

    @property
    def value_status(self):
        """Статус значения: override/calc/empty"""
        if self.override_value is not None:
            return 'override'
        if self.calc_value is not None:
            return 'calc'
        return 'empty'


class CellEvent(Base):
    """Cell Events table - аудит изменений"""
    __tablename__ = 'cell_events'

    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cell_values.id'), index=True)
    event_type = Column(String(20), nullable=False)  # "override", "calc", "fact", "wave"
    old_value = Column(Float)
    new_value = Column(Float)
    reason = Column(Text)
    user_id = Column(String(100))  # для будущей авторизации
    created_at = Column(DateTime, default=datetime.utcnow)

    cell = relationship("CellValue", back_populates="events")


# Database connection helpers

def get_engine(db_path: str = 'fm_demo.db'):
    """Create SQLAlchemy engine"""
    return create_engine(f'sqlite:///{db_path}', echo=False)


def get_session(engine=None, db_path: str = 'fm_demo.db'):
    """Create database session"""
    if engine is None:
        engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables(engine=None, db_path: str = 'fm_demo.db'):
    """Create all tables in database"""
    if engine is None:
        engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


# SQL View as a query helper (SQLite doesn't support ORM views well)
CELLS_FINAL_VIEW_SQL = """
CREATE VIEW IF NOT EXISTS cells_final AS
SELECT
    *,
    COALESCE(override_value, calc_value) AS final_value,
    CASE
        WHEN override_value IS NOT NULL THEN 'override'
        WHEN calc_value IS NOT NULL THEN 'calc'
        ELSE 'empty'
    END AS value_status
FROM cell_values;
"""
