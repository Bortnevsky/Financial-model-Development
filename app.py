#!/usr/bin/env python3
"""
FM Pro Demo - Streamlit Application
Premium financial modeling interface
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from db.schema import get_session, CellValue, Sheet, FMVersion, Project
from db.queries import get_sheet_data, num_to_col

# Page config
st.set_page_config(
    page_title="FM Pro Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS - white on blue, minimal gold accents
st.markdown("""
<style>
    /* Root variables */
    :root {
        --bg-primary: #0a1929;
        --bg-secondary: #0d2137;
        --bg-card: #132f4c;
        --text-primary: #ffffff;
        --text-secondary: #b2bac2;
        --text-muted: #5f6a7a;
        --accent: #66b2ff;
        --accent-gold: #ffc107;
        --border: #1e4976;
        --success: #66bb6a;
        --error: #f44336;
    }

    /* Main app */
    .stApp {
        background: var(--bg-primary);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }

    /* Hide default hamburger */
    [data-testid="collapsedControl"] {
        display: none;
    }

    /* All text white */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: var(--text-primary) !important;
    }

    .stMarkdown {
        color: var(--text-primary);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    /* Cards/containers */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .card-header {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted) !important;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
    }

    /* Section headers - single consistent style */
    .section-header {
        background: var(--bg-card);
        border-left: 3px solid var(--accent);
        color: var(--text-primary) !important;
        padding: 10px 16px;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 16px;
        margin-bottom: 0;
    }

    /* Data tables */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        background: var(--bg-card);
    }

    .data-table th {
        background: var(--bg-secondary);
        color: var(--text-secondary) !important;
        padding: 10px 12px;
        text-align: left;
        font-weight: 500;
        border-bottom: 1px solid var(--border);
    }

    .data-table td {
        padding: 8px 12px;
        border-bottom: 1px solid var(--border);
        color: var(--text-primary);
    }

    .data-table tr:hover {
        background: rgba(102, 178, 255, 0.05);
    }

    .data-table .value {
        text-align: right;
        font-family: 'SF Mono', Monaco, monospace;
    }

    .data-table .total-row {
        background: var(--bg-secondary);
        font-weight: 600;
    }

    .data-table .total-row td {
        border-top: 2px solid var(--accent);
    }

    /* Buttons */
    .stButton > button {
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border);
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: var(--accent);
        color: var(--bg-primary);
        border-color: var(--accent);
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: var(--accent);
        color: var(--bg-primary);
        border: none;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: var(--bg-card);
        border-color: var(--border);
        color: var(--text-primary);
    }

    /* Radio as menu */
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }

    [data-testid="stSidebar"] .stRadio > div {
        flex-direction: column;
        gap: 2px;
    }

    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        padding: 12px 16px;
        border-radius: 8px;
        color: var(--text-secondary) !important;
        cursor: pointer;
        margin: 0;
        transition: all 0.2s;
    }

    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: var(--bg-card);
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(102, 178, 255, 0.1);
        color: var(--accent) !important;
        border-left: 3px solid var(--accent);
    }

    /* Logo */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 16px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 20px;
    }

    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent) 0%, #1976d2 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .logo-text {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary) !important;
    }

    /* Menu section title */
    .menu-section {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-muted) !important;
        padding: 16px 16px 8px 16px;
    }

    /* Project badge */
    .project-badge {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 0 16px 16px 16px;
    }

    .project-name {
        font-weight: 600;
        color: var(--text-primary) !important;
        margin-bottom: 4px;
    }

    .project-version {
        font-size: 12px;
        color: var(--text-muted) !important;
    }

    /* KPI row */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px;
    }

    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'SF Mono', Monaco, monospace;
    }

    .kpi-label {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 4px;
    }

    .kpi-delta {
        font-size: 12px;
        margin-top: 8px;
    }

    .kpi-delta.positive {
        color: var(--success);
    }

    .kpi-delta.negative {
        color: var(--error);
    }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }

    /* Info/warning boxes */
    .stAlert {
        background: var(--bg-card);
        border: 1px solid var(--border);
        color: var(--text-primary);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        color: var(--text-primary) !important;
    }

    /* Chat messages */
    .chat-ai {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    .chat-user {
        background: rgba(102, 178, 255, 0.1);
        border: 1px solid var(--accent);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# DATABASE FUNCTIONS
# ============================================

def check_database():
    """Check if database exists and has data"""
    db_path = Path(__file__).parent / "fm_demo.db"
    if not db_path.exists():
        return False, "База данных не найдена"
    if db_path.stat().st_size < 1000:
        return False, "База данных пустая"
    try:
        session = get_session()
        count = session.query(CellValue).count()
        session.close()
        return (True, f"{count:,} ячеек") if count > 0 else (False, "Нет данных")
    except Exception as e:
        return False, str(e)


def get_cell_value(sheet: str, address: str, version_id: int = 1):
    """Get single cell value"""
    session = get_session()
    try:
        cell = session.query(CellValue).filter_by(
            version_id=version_id, sheet=sheet, address=address
        ).first()
        return cell.final_value if cell else None
    except:
        return None
    finally:
        session.close()


def get_indicator_value(indicator_name: str, col: str = "J", version_id: int = 1):
    """Get value for an indicator by name from DB2 sheet"""
    from sqlalchemy import text
    session = get_session()
    try:
        # Find indicator row
        result = session.execute(text(
            "SELECT row_num FROM indicators WHERE name = :name AND sheet = 'DB2'"
        ), {"name": indicator_name})
        row = result.fetchone()
        if row:
            address = f"{col}{row[0]}"
            cell = session.query(CellValue).filter_by(
                version_id=version_id, sheet="DB2", address=address
            ).first()
            return cell.final_value if cell else None
        return None
    except:
        return None
    finally:
        session.close()


def load_section_data(sheet: str, row_start: int, row_end: int, cols: list, version_id: int = 1):
    """Load section of data from sheet"""
    from sqlalchemy import text
    session = get_session()
    try:
        # Get indicators for labels
        result = session.execute(text(
            "SELECT row_num, name FROM indicators WHERE sheet = :sheet AND row_num >= :start AND row_num <= :end"
        ), {"sheet": sheet, "start": row_start, "end": row_end})
        indicators = {r[0]: r[1] for r in result.fetchall()}

        # Get cell values
        cells = session.query(CellValue).filter(
            CellValue.version_id == version_id,
            CellValue.sheet == sheet,
            CellValue.row_num >= row_start,
            CellValue.row_num <= row_end
        ).all()

        # Build data
        data = []
        for row_num in range(row_start, row_end + 1):
            row_data = {"Показатель": indicators.get(row_num, "")}
            for col in cols:
                col_num = ord(col.upper()) - ord('A') + 1
                cell = next((c for c in cells if c.row_num == row_num and c.col_num == col_num), None)
                if cell and cell.final_value is not None:
                    val = cell.final_value
                    if isinstance(val, float):
                        row_data[col] = int(val) if val == int(val) else round(val, 2)
                    else:
                        row_data[col] = val
                else:
                    row_data[col] = ""
            if row_data["Показатель"] or any(row_data[c] != "" for c in cols):
                data.append(row_data)

        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()
    finally:
        session.close()


def format_number(val, suffix=""):
    """Format number with thousands separator"""
    if val is None or val == "":
        return ""
    try:
        num = float(val)
        if abs(num) >= 1000000:
            return f"{num/1000000:.1f} млрд{suffix}"
        elif abs(num) >= 1000:
            return f"{num/1000:.0f} тыс{suffix}"
        else:
            return f"{num:.0f}{suffix}"
    except:
        return str(val)


# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    # Logo
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">📊</div>
        <div class="logo-text">FM Pro</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown('<div class="menu-section">Навигация</div>', unsafe_allow_html=True)

    page = st.radio(
        "Menu",
        ["📊 Dashboard", "📋 Данные модели", "💬 AI Ассистент", "🧪 Примеры", "📈 Сценарии"],
        label_visibility="collapsed"
    )

    # Project info
    st.markdown('<div class="menu-section">Проект</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="project-badge">
        <div class="project-name">Касаткина 7</div>
        <div class="project-version">Версия: Базовая v1.0</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# DATABASE CHECK
# ============================================

db_ok, db_status = check_database()

if not db_ok:
    st.error(f"⚠️ {db_status}")
    st.code("""
# Windows:
git pull origin main
python -m streamlit run app.py
    """)
    st.stop()


# ============================================
# DASHBOARD PAGE
# ============================================

if page == "📊 Dashboard":
    st.markdown("## Финансовая модель — Касаткина 7")

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Выручка", "78.7 млрд", "")
    with col2:
        st.metric("Инвестиции", "47.8 млрд", "")
    with col3:
        st.metric("Прибыль", "9.3 млрд", "")
    with col4:
        st.metric("Маржа", "12%", "")
    with col5:
        st.metric("IRR", "18%", "")

    # Section tabs - horizontal like Excel
    section_tabs = st.tabs(["ТЭПы", "ИНВЕСТИЦИИ", "РАСХОДЫ", "ДОХОДЫ", "ФИНАНСИРОВАНИЕ", "СРОКИ", "РЕЗУЛЬТАТ", "ЗУ", "УПРАВЛЯЮЩИЙ"])

    # ТЭПы
    with section_tabs[0]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>Параметр</th><th>ГНС</th><th>ОБЩАЯ ПЛОЩАДЬ</th><th>ПОЛЕЗНАЯ ПЛОЩАДЬ</th><th>LF, %</th><th>КОЛ-ВО</th></tr>
            <tr><td><b>НАЗЕМНАЯ ЧАСТЬ</b></td><td>S лота</td><td>178 143</td><td>165 673</td><td>116 376</td><td>29,8%</td><td></td></tr>
            <tr><td>КВАРТИРЫ</td><td style="background: #3d3d3d;">95%</td><td style="background: #3d3d3d;">53 м2</td><td>169 436</td><td>157 575</td><td>110 303</td><td>30,0%</td><td>2 081</td></tr>
            <tr><td>РИТЕЙЛ</td><td style="background: #3d3d3d;">5%</td><td style="background: #3d3d3d;">100 м2</td><td>8 707</td><td>8 098</td><td>6 073</td><td>25,0%</td><td>61</td></tr>
            <tr><td>ШКОЛА</td><td>мест</td><td style="background: #ffc107; color: #000;">1 000</td><td></td><td></td><td></td><td></td></tr>
            <tr><td>ДОУ</td><td>мест</td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td><b>ПОДЗЕМНАЯ ЧАСТЬ</b></td><td>S общ.</td><td>S пол.</td><td>44 480</td><td>16 680</td><td></td><td></td></tr>
            <tr><td>ПАРКИНГ ЖИЛ.</td><td style="background: #3d3d3d;">обесп. 53%</td><td style="background: #ffc107; color: #000;">40 м2</td><td style="background: #3d3d3d;">15 м2</td><td>44 480</td><td>16 680</td><td></td><td>1 112</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>ПЛОЩАДИ</td><td></td><td>178 143</td><td>210 153</td><td>133 056</td><td>29,8%</td><td></td></tr>
        </table>
        """, unsafe_allow_html=True)

    # ИНВЕСТИЦИИ
    with section_tabs[1]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>Ставка</th><th>Ед.</th><th>руб./S общ.</th><th>руб./S пол.</th><th>млн.руб.</th></tr>
            <tr><td><b>ВХОД</b></td><td style="background: #ffc107; color: #000;">807</td><td>за Га</td><td>18 279</td><td>28 870</td><td style="background: #7c4dff; color: #fff;">3 841</td></tr>
            <tr><td>FINDERS FEE</td><td></td><td>% от входа</td><td></td><td></td><td></td></tr>
            <tr><td><b>ЗЕМЕЛЬНО-ПРАВОВЫЕ ВОПРОСЫ</b></td><td></td><td></td><td>23 436</td><td>37 016</td><td style="background: #7c4dff; color: #fff;">4 925</td></tr>
            <tr><td>ВРИ</td><td></td><td></td><td>40 248</td><td>63 570</td><td>8 458</td></tr>
            <tr><td>ЛЬГОТА</td><td></td><td></td><td>-40 248</td><td>-63 570</td><td style="color: #f44336;">-8 458</td></tr>
            <tr><td>ПОКУПКА ЛЬГОТЫ</td><td></td><td></td><td>22 314</td><td>35 243</td><td>4 689</td></tr>
            <tr><td>РАССРОЧКА ВРИ</td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td>АРЕНДА ЗУ/НАЛОГ ЗУ</td><td></td><td>АРЕНДА</td><td>1 123</td><td>1 773</td><td>236</td></tr>
            <tr><td><b>ВЛОЖЕНИЯ В СТРОИТЕЛЬСТВО</b></td><td></td><td></td><td>185 503</td><td>292 990</td><td>38 984</td></tr>
            <tr><td>ПРОЕКТИРОВАНИЕ (К+П+РД)</td><td style="background: #ffc107; color: #000;">7 310</td><td>м2 S общ.</td><td>7 310</td><td>11 546</td><td>1 536</td></tr>
            <tr><td>СОГЛАСОВАНИЯ</td><td style="background: #ffc107; color: #000;">1 000</td><td>м2 S общ.</td><td>1 000</td><td>1 579</td><td>210</td></tr>
            <tr><td>СМР жилье</td><td style="background: #ffc107; color: #000;">137 000</td><td>м2 S общ.</td><td>137 000</td><td>216 382</td><td>28 791</td></tr>
            <tr><td>СМР соц. объектов</td><td style="background: #ffc107; color: #000;">20 791</td><td>м2 Sобщ.</td><td>20 791</td><td>32 838</td><td>4 369</td></tr>
            <tr><td>СОДЕРЖАНИЕ ПЛОЩАДКИ</td><td style="background: #ffc107; color: #000;">770</td><td>м2 S общ.</td><td>770</td><td>1 216</td><td>162</td></tr>
            <tr><td>СЕТИ</td><td style="background: #ffc107; color: #000;">5 500</td><td>м2 Sобщ.</td><td>5 500</td><td>8 687</td><td style="background: #ffc107; color: #000;">1 156</td></tr>
            <tr><td>МОНИТОРИНГИ</td><td style="background: #ffc107; color: #000;">2 500</td><td>м2 Sобщ.</td><td>2 500</td><td>3 949</td><td>525</td></tr>
            <tr><td>УПРАВЛЕНИЕ ПРОЕКТОМ</td><td>20,8 млн. в мес.</td><td style="background: #ffc107; color: #000;">4,00%</td><td>% от расходов</td><td>7 135</td><td>11 269</td><td>1 499</td></tr>
            <tr><td>НЕПРЕДВИДЕННЫЕ РАСХОДЫ</td><td></td><td style="background: #ffc107; color: #000;">2,00%</td><td>% от расходов</td><td>3 497</td><td>5 524</td><td>735</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>ИНВЕСТИЦИИ</td><td></td><td></td><td>227 219</td><td>358 876</td><td style="color: #f44336;">47 751</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # РАСХОДЫ НА ПРОДАЖУ
    with section_tabs[2]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>Ставка</th><th>Ед.</th><th>руб./S общ.</th><th>руб./S пол.</th><th>млн.руб.</th></tr>
            <tr><td>АХР</td><td style="background: #ffc107; color: #000;">2,0</td><td>млн. р. в кв.</td><td>757</td><td>1 195</td><td>159</td></tr>
            <tr><td>РЕКЛАМА И МАРКЕТИНГ</td><td style="background: #ffc107; color: #000;">3,0%</td><td>% от выручки</td><td>11 241</td><td>17 755</td><td>2 362</td></tr>
            <tr><td>БРОКЕРИДЖ</td><td style="background: #ffc107; color: #000;">3,0%</td><td>% от выручки</td><td>11 241</td><td>17 755</td><td>2 362</td></tr>
            <tr><td>УПРАВЛЕНИЕ ПРОДАЖАМИ</td><td style="background: #ffc107; color: #000;">1,2%</td><td>% от выручки</td><td>4 496</td><td>7 102</td><td>945</td></tr>
            <tr><td>РЕГИСТРАЦИЯ ДОГОВОРОВ</td><td style="background: #ffc107; color: #000;">30 000</td><td>руб./лот</td><td>657</td><td>1 038</td><td>138</td></tr>
            <tr><td>АРЕНДА / НАЛОГ ЗУ</td><td></td><td></td><td>155</td><td>245</td><td>33</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>РАСХОДЫ</td><td></td><td></td><td>28 548</td><td>45 089</td><td style="color: #4caf50;">5 999</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # ДОХОДЫ
    with section_tabs[3]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>старт</th><th>% пост.</th><th>c/c</th><th>ЦЕНА →</th><th>ЦЕНА ←</th><th>СРЕДНЯЯ ЦЕНА</th><th>ДОХОД, млн.руб.</th><th>%</th><th>ОБЪЕМ ПРОДАЖ, в кв.</th></tr>
            <tr><td><b>НАЗЕМНАЯ ЧАСТЬ</b></td><td></td><td></td><td></td><td>511</td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td>КВАРТИРЫ</td><td style="background: #ffc107; color: #000;">01.10.2026</td><td style="background: #3d3d3d;">36%</td><td></td><td>523</td><td>711</td><td style="background: #ffc107; color: #000;">630</td><td style="font-weight: bold;">69 491</td><td>88%</td><td>4 596</td></tr>
            <tr><td>РИТЕЙЛ</td><td>1 кв после РнВ</td><td></td><td></td><td>700</td><td>700</td><td style="background: #ffc107; color: #000;">700</td><td>4 251</td><td>5%</td><td></td></tr>
            <tr><td>ШКОЛА</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td>ДОУ</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td><b>ПОДЗЕМНАЯ ЧАСТЬ</b></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
            <tr><td>ПАРКИНГ ЖИЛЬЕ</td><td></td><td style="background: #ffc107; color: #000;">70%</td><td></td><td>4 500</td><td>4 500</td><td style="background: #ffc107; color: #000;">4 500</td><td style="font-weight: bold;">5 004</td><td>6%</td><td></td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>ДОХОДЫ</td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color: #4caf50;">78 746</td><td></td><td></td></tr>
        </table>
        """, unsafe_allow_html=True)

    # ФИНАНСИРОВАНИЕ
    with section_tabs[4]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>Параметр</th><th>Значение</th></tr>
            <tr><td colspan="3" style="background: #2d2d2d;"><b>КРЕДИТ</b></td></tr>
            <tr><td>СТАВКИ</td><td></td><td>КС = 20,0%</td></tr>
            <tr><td>СТАВКА бридж</td><td style="background: #ffc107; color: #000;">+ 5,0%</td><td>25,0%</td></tr>
            <tr><td>СТАВКА проектное фин-ие</td><td style="background: #ffc107; color: #000;">+ 3,8%</td><td>23,8%</td></tr>
            <tr><td>СТАВКА под эскроу</td><td></td><td>3,8%</td></tr>
            <tr><td colspan="3" style="background: #2d2d2d;"><b>КОМИССИИ</b></td></tr>
            <tr><td>РЕЗЕРВИРОВАНИЕ в банке</td><td>303 млн. руб.</td><td style="background: #ffc107; color: #000;">0,50%</td></tr>
            <tr><td>БРОКЕРИДЖ МРГ бридж</td><td></td><td></td></tr>
            <tr><td>БРОКЕРИДЖ МРГ проектное</td><td></td><td></td></tr>
            <tr><td colspan="3" style="background: #2d2d2d;"><b>ОБЪЕМ ФИНАНСИРОВАНИЯ</b></td></tr>
            <tr><td>ВХОД</td><td>млн. руб.</td><td></td></tr>
            <tr><td>ДО РНС</td><td>млн. руб.</td><td>9 723</td></tr>
            <tr><td>ПРОЕКТНОЕ ФИН-ИЕ</td><td>млн. руб.</td><td>50 956</td></tr>
            <tr><td>% и КОМИСИИ банка</td><td>млн. руб.</td><td>10 380</td></tr>
            <tr><td colspan="3" style="background: #2d2d2d;"><b>АКЦИОНЕРНЫЕ ЗАЙМЫ</b></td></tr>
            <tr><td>СТАВКА ЗАЙМА</td><td style="background: #ffc107; color: #000;">+ 1,0%</td><td>21,0%</td></tr>
            <tr><td>ТЕЛО ЗАЙМА</td><td>млн. руб.</td><td>596</td></tr>
            <tr><td>%</td><td>млн. руб.</td><td>392</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>ПРОЦЕНТЫ</td><td></td><td style="color: #f44336;">10 772</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # СРОКИ
    with section_tabs[5]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #7c4dff;"><th>Показатель</th><th>кв.</th></tr>
            <tr><td>НАЧАЛО РАСЧЕТОВ</td><td style="font-weight: bold;">01.04.2023</td></tr>
            <tr><td>НАЧАЛО ПРОЕКТА</td><td style="font-weight: bold;">01.04.2025</td></tr>
            <tr><td>СРОК ИРД</td><td>5 кв.</td></tr>
            <tr><td>РНС 1</td><td style="font-weight: bold;">01.10.2026</td></tr>
            <tr><td>СРОК СМР</td><td>16 кв.</td></tr>
            <tr><td>РНВ 2</td><td style="font-weight: bold;">30.09.2030</td></tr>
            <tr><td>ОКОНЧАНИЕ ПРОДАЖ</td><td style="font-weight: bold;">31.12.2031</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>СРОК</td><td>6,8 л</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # РЕЗУЛЬТАТ
    with section_tabs[6]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>млн. руб.</th></tr>
            <tr><td>ДОХОДЫ</td><td>78 746</td></tr>
            <tr><td>РАСХОДЫ НА ПРОДАЖУ</td><td style="color: #f44336;">-5 999</td></tr>
            <tr><td>ИНВЕСТИЦИИ</td><td style="color: #f44336;">-47 751</td></tr>
            <tr><td>ПРОЦЕНТЫ</td><td style="color: #f44336;">-10 772</td></tr>
            <tr><td>НАЛОГИ</td><td style="color: #f44336;">-4 878</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td>ПРИБЫЛЬ (в т ч SF МРГ)</td><td style="color: #4caf50;">9 346</td></tr>
            <tr><td>МАРЖИНАЛЬНОСТЬ до Н/О</td><td>18%</td></tr>
            <tr><td>МАРЖ-СТЬ после Н/О</td><td>12%</td></tr>
            <tr><td>IRR ПРОЕКТА (pre-tax)</td><td style="font-weight: bold;">18%</td></tr>
            <tr><td>IRR ИНВЕСТОРА</td><td style="font-weight: bold;">63%</td></tr>
            <tr><td>LLSR</td><td>1,20</td></tr>
            <tr><td>PV</td><td style="background: #3d3d3d;">20%</td><td>1866</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # ЗУ
    with section_tabs[7]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #7c4dff;"><th colspan="3">ЗУ</th></tr>
            <tr><td>КАДАСТРОВЫЙ НОМЕР</td><td></td><td style="font-weight: bold;">77:02:0019010:102</td></tr>
            <tr><td>ВИД ПРАВА</td><td></td><td>АРЕНДА</td></tr>
            <tr><td>АРЕНДА / НАЛОГ ЗУ после ввода</td><td>кв.</td><td>2</td></tr>
            <tr><td>ПЛОЩАДЬ ЗУ</td><td>м2</td><td style="font-weight: bold;">47 620</td></tr>
            <tr><td>УДЕЛЬНАЯ ТЕКУЩАЯ КС</td><td>тыс. руб.</td><td>21 593</td></tr>
        </table>
        """, unsafe_allow_html=True)

    # ДОХОДЫ УПРАВЛЯЮЩЕГО
    with section_tabs[8]:
        st.markdown("""
        <table class="data-table">
            <tr style="background: #1e4976;"><th>Показатель</th><th>Ставка</th><th>млн. руб.</th></tr>
            <tr><td>УПРАВЛЕНИЕ ПРОЕКТОМ</td><td></td><td>1 499</td></tr>
            <tr><td>УПРАВЛЕНИЕ ПРОДАЖАМИ</td><td></td><td>945</td></tr>
            <tr><td>ПРИВЛЕЧЕНИЕ КРЕДИТА</td><td></td><td></td></tr>
            <tr><td>FINDERS FEE</td><td></td><td></td></tr>
            <tr><td>SF</td><td style="background: #ffc107; color: #000;">5,0%</td><td>467</td></tr>
            <tr style="background: #1a1a1a; font-weight: bold;"><td></td><td></td><td style="color: #4caf50;">2 912</td></tr>
        </table>
        """, unsafe_allow_html=True)


# ============================================
# DATA PAGE
# ============================================

elif page == "📋 Данные модели":
    st.markdown("## Данные модели")
    st.caption("Просмотр данных по листам как в Excel")

    # All sheets as horizontal tabs (like Excel)
    all_sheets = ["МАСТЕР ПЛАН", "RESUME", "DB", "DB1", "DB2", "CF", "CF1", "CF2", "TS1", "TS2", "DETAILS", "FACT", "БИТ", "ПРОДАЖИ", "СОЦИАЛКА"]

    sheet_tabs = st.tabs(all_sheets)

    for i, sheet_name in enumerate(all_sheets):
        with sheet_tabs[i]:
            # Load sheet data as grid
            session = get_session()
            try:
                cells = session.query(CellValue).filter_by(
                    version_id=1, sheet=sheet_name
                ).all()

                if cells:
                    max_row = max((c.row_num for c in cells if c.row_num), default=0)
                    max_col = max((c.col_num for c in cells if c.col_num), default=0)

                    max_row = min(max_row, 100)
                    max_col = min(max_col, 20)

                    # Build grid
                    columns = [num_to_col(j) for j in range(1, max_col + 1)]
                    data = {col: [''] * max_row for col in columns}

                    for cell in cells:
                        if cell.row_num and cell.col_num and cell.row_num <= max_row and cell.col_num <= max_col:
                            col_letter = num_to_col(cell.col_num)
                            val = cell.final_value
                            if val is not None:
                                if isinstance(val, float):
                                    data[col_letter][cell.row_num - 1] = int(val) if val == int(val) else round(val, 2)
                                else:
                                    data[col_letter][cell.row_num - 1] = val

                    df = pd.DataFrame(data)
                    df.index = range(1, len(df) + 1)
                    st.dataframe(df, use_container_width=True, height=550)
                    st.caption(f"Ячеек: {len(cells)}")
                else:
                    st.info(f"Нет данных для листа {sheet_name}")
            except Exception as e:
                st.error(f"Ошибка: {e}")
            finally:
                session.close()


# ============================================
# AI ASSISTANT PAGE
# ============================================

elif page == "💬 AI Ассистент":
    st.markdown("## AI Ассистент")
    st.caption("Анализ модели с помощью Claude AI")

    # Settings
    with st.expander("⚙️ Настройки API", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            api_key = st.text_input("Claude API Key", type="password", placeholder="sk-ant-...", key="claude_api_key")
        with col2:
            model = st.selectbox("Модель", [
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-5-20251101",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022"
            ], key="claude_model")

        col3, col4 = st.columns(2)
        with col3:
            eleven_key = st.text_input("11Labs API Key", type="password", placeholder="...", key="eleven_key")
        with col4:
            voice = st.selectbox("Голос", ["Rachel", "Adam", "Antoni"], key="eleven_voice")

    st.markdown("---")

    # Model context for AI
    model_context = """
    Финансовая модель проекта "Касаткина 7":
    - Выручка: 78 746 млн руб (КВАРТИРЫ 69 491, РИТЕЙЛ 4 251, ПАРКИНГ 5 004)
    - Инвестиции: 47 751 млн руб
    - Расходы на продажу: 5 999 млн руб
    - Проценты: 10 772 млн руб
    - Налоги: 4 878 млн руб
    - Прибыль: 9 346 млн руб
    - Маржа до Н/О: 18%, после Н/О: 12%
    - IRR проекта: 18%, IRR инвестора: 63%
    - Площади: ГНС 178 143 м², общая 210 153 м², полезная 133 056 м²
    - Сроки: начало 01.04.2025, РНС 01.10.2026, РНВ 30.09.2030, окончание продаж 31.12.2031 (6.8 лет)
    - Ключевая ставка: 20%, ставка бридж: 25%, проектное: 23.8%
    """

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Привет! Я AI-ассистент для анализа финансовых моделей. Спросите меня о показателях, формулах или сценариях."}
        ]

    for msg in st.session_state.messages:
        css_class = "chat-ai" if msg["role"] == "assistant" else "chat-user"
        icon = "🤖" if msg["role"] == "assistant" else "👤"
        st.markdown(f'<div class="{css_class}"><strong>{icon}</strong> {msg["content"]}</div>', unsafe_allow_html=True)

    # Quick buttons
    st.markdown("**Быстрые вопросы:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 Показатели", use_container_width=True):
            st.session_state.pending_question = "Покажи основные показатели проекта"
    with col2:
        if st.button("💰 Прибыль", use_container_width=True):
            st.session_state.pending_question = "Какая прибыль проекта и из чего она складывается?"
    with col3:
        if st.button("⚠️ Риски", use_container_width=True):
            st.session_state.pending_question = "Какие риски у проекта?"
    with col4:
        if st.button("📈 IRR", use_container_width=True):
            st.session_state.pending_question = "Объясни IRR проекта и инвестора"

    # Input
    user_input = st.chat_input("Ваш вопрос...")

    # Handle pending question from buttons
    if "pending_question" in st.session_state:
        user_input = st.session_state.pending_question
        del st.session_state.pending_question

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        if api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                # Build messages for API
                api_messages = []
                for msg in st.session_state.messages:
                    if msg["role"] in ["user", "assistant"]:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})

                with st.spinner("Думаю..."):
                    response = client.messages.create(
                        model=model,
                        max_tokens=1024,
                        system=f"Ты финансовый аналитик. Отвечай на русском языке. Вот данные модели:\n{model_context}",
                        messages=api_messages
                    )
                    answer = response.content[0].text
                    st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Ошибка API: {str(e)}"})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Введите API ключ Claude в настройках выше."})

        st.rerun()


# ============================================
# EXAMPLES PAGE
# ============================================

elif page == "🧪 Примеры":
    st.markdown("## Демонстрационные примеры")
    st.caption("Интерактивные демо возможностей системы")

    tab1, tab2, tab3, tab4 = st.tabs(["🌊 Wave распределение", "📥 Загрузка факта", "📋 Ковенанты", "💬 AI Chat"])

    with tab1:
        st.markdown("### Волна перераспределения")
        st.markdown("Демонстрация алгоритмов распределения значений по периодам.")

        st.markdown("""
        **Как работает:**
        1. Выберите показатель для редактирования
        2. Введите новое значение
        3. Система автоматически перераспределит по периодам

        **Методы распределения:**
        - **Пропорциональный** - сохраняет исходные пропорции
        - **Равномерный** - делит поровну
        - **Хвостовой** - всё в последний период
        - **S-кривая** - плавное нарастание
        """)

        # Demo table
        wave_data = {
            "Показатель": ["Выручка квартиры", "План", "Расчет", "Дельта"],
            "Q1 2026": ["🔒", "15 000", "15 000", "0"],
            "Q2 2026": ["✏️", "18 000", "17 500", "+500"],
            "Q3 2026": ["↻", "20 000", "19 800", "+200"],
            "Q4 2026": ["↻", "22 000", "21 700", "+300"],
        }
        st.dataframe(pd.DataFrame(wave_data), use_container_width=True, hide_index=True)

        if st.button("▶️ Открыть полную демо", key="wave_demo"):
            st.markdown("[Открыть wave.html](mockup/wave.html)")

    with tab2:
        st.markdown("### Загрузка фактических данных")
        st.markdown("Демонстрация загрузки факта и сравнения с планом.")

        st.markdown("""
        **Пример диалога:**

        👤 *Загрузи факт продаж за Q3 2025*

        🤖 Загружаю данные... Найдено расхождение:
        - Квартиры: план 8,500 м², факт 9,200 м² (+8.2%)
        - Ритейл: план 1,200 м², факт 800 м² (-33%)

        Обновить прогноз?
        """)

        st.file_uploader("Загрузить файл факта", type=["xlsx", "csv"])

        if st.button("▶️ Запустить демо", key="fact_demo"):
            st.info("Демо загрузки факта в разработке")

    with tab3:
        st.markdown("### Проверка ковенантов")
        st.markdown("Автоматическая проверка банковских ковенантов.")

        st.markdown("""
        **Результаты проверки:**

        ✅ **DSCR**: 1.45 (мин. 1.2) — OK
        ✅ **LTV**: 58% (макс. 70%) — OK
        ⚠️ **ICR**: 1.18 (мин. 1.15) — близко к границе
        """)

        cov_data = {
            "Ковенант": ["DSCR", "LTV", "ICR", "Debt/Equity"],
            "Факт": ["1.45", "58%", "1.18", "2.1"],
            "Мин/Макс": ["≥1.2", "≤70%", "≥1.15", "≤3.0"],
            "Статус": ["✅ OK", "✅ OK", "⚠️ Внимание", "✅ OK"]
        }
        st.dataframe(pd.DataFrame(cov_data), use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### AI Chat с голосом")
        st.markdown("Демонстрация голосового ассистента с Claude API и 11Labs.")

        st.markdown("""
        **Возможности:**
        - Ввод голосом (микрофон)
        - Ответ голосом (11Labs TTS)
        - Анализ формул и ячеек
        - Объяснение расчетов

        **Настройки:**
        - Claude API для анализа
        - 11Labs API для озвучки
        """)

        if st.button("▶️ Открыть AI Chat демо", key="ai_demo"):
            st.markdown("[Открыть ai-chat.html](mockup/ai-chat.html)")


# ============================================
# SCENARIOS PAGE
# ============================================

elif page == "📈 Сценарии":
    st.markdown("## Сценарное моделирование")
    st.caption("Анализ чувствительности и стресс-тесты")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🎲</div>
            <div style="font-weight: 600;">Монте-Карло</div>
            <div style="font-size: 12px; color: var(--text-muted);">1000+ итераций</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Запустить", key="mc"):
            st.info("В разработке")

    with col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📉</div>
            <div style="font-weight: 600;">Стресс-тесты</div>
            <div style="font-size: 12px; color: var(--text-muted);">Экстремальные сценарии</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Запустить", key="stress"):
            st.info("В разработке")

    with col3:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🎯</div>
            <div style="font-weight: 600;">Чувствительность</div>
            <div style="font-size: 12px; color: var(--text-muted);">Ключевые параметры</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Запустить", key="sens"):
            st.info("В разработке")

    with col4:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
            <div style="font-weight: 600;">Ключевая ставка</div>
            <div style="font-size: 12px; color: var(--text-muted);">Влияние ставки ЦБ</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Запустить", key="rate"):
            st.info("В разработке")

    st.markdown("---")

    st.markdown("### 💬 Опишите сценарий")
    scenario = st.text_input("", placeholder="Например: что будет если продажи упадут на 20%?")

    if st.button("🚀 Рассчитать"):
        if scenario:
            st.info("Расчет сценария в разработке. Нужен API ключ Claude.")
