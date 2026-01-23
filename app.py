#!/usr/bin/env python3
"""
FM Pro Demo - Streamlit Application
Main entry point for the web interface
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from db.schema import get_session, CellValue, Sheet, FMVersion, Project
from db.queries import get_sheet_data, num_to_col
from engine.wave_engine import apply_wave, preview_wave, WaveMethod

# Page config
st.set_page_config(
    page_title="FM Pro Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with amber accents
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --bg-dark: #0a1628;
        --bg-card: #0f1f3d;
        --bg-input: #132340;
        --border: #1e3a5f;
        --text: #f5f5f5;
        --text-muted: #8b9cb5;
        --accent: #f59e0b;
        --accent-hover: #d97706;
        --success: #22c55e;
        --warning: #eab308;
        --error: #ef4444;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dark background */
    .stApp {
        background: linear-gradient(180deg, #0a1628 0%, #0d1e38 100%);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #0f1f3d;
        border-right: 1px solid #1e3a5f;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #f5f5f5;
    }

    /* Cards */
    .fm-card {
        background: #0f1f3d;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .fm-card:hover {
        border-color: #f59e0b40;
    }

    /* KPI Card */
    .kpi-card {
        background: #0f1f3d;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #f59e0b;
        margin: 8px 0;
    }

    .kpi-label {
        font-size: 12px;
        color: #8b9cb5;
        text-transform: uppercase;
    }

    .kpi-sub {
        font-size: 14px;
        color: #8b9cb5;
    }

    /* Data table styling */
    .dataframe {
        background: #0f1f3d !important;
        color: #f5f5f5 !important;
    }

    .dataframe th {
        background: #132340 !important;
        color: #8b9cb5 !important;
        font-weight: 500 !important;
        border-bottom: 1px solid #1e3a5f !important;
    }

    .dataframe td {
        border-bottom: 1px solid #1e3a5f !important;
        color: #f5f5f5 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #000;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 20px;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: #000;
    }

    /* Secondary button */
    .secondary-btn > button {
        background: transparent;
        color: #f59e0b;
        border: 1px solid #f59e0b;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: #132340;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        color: #8b9cb5;
        padding: 8px 16px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        border-color: #f59e0b;
        color: #f5f5f5;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(245, 158, 11, 0.1);
        border-color: #f59e0b;
        color: #f59e0b;
    }

    /* Text inputs */
    .stTextInput > div > div > input {
        background: #132340;
        border: 1px solid #1e3a5f;
        color: #f5f5f5;
        border-radius: 8px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #f59e0b;
        box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background: #132340;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
    }

    /* Headers */
    h1, h2, h3 {
        color: #f5f5f5 !important;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #f59e0b !important;
        font-size: 28px !important;
    }

    [data-testid="stMetricLabel"] {
        color: #8b9cb5 !important;
    }

    [data-testid="stMetricDelta"] {
        color: #22c55e !important;
    }

    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 0;
        margin-bottom: 20px;
    }

    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }

    .logo-text {
        font-size: 22px;
        font-weight: 700;
        color: #f5f5f5;
    }

    /* Navigation items */
    .nav-section-title {
        font-size: 11px;
        text-transform: uppercase;
        color: #5a7090;
        padding: 16px 0 8px 0;
        letter-spacing: 0.5px;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        color: #8b9cb5;
        cursor: pointer;
        transition: all 0.15s;
        margin-bottom: 4px;
    }

    .nav-item:hover {
        background: #132340;
        color: #f5f5f5;
    }

    .nav-item.active {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
    }

    /* AI Hint box */
    .ai-hint {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
    }

    .ai-hint-title {
        color: #f59e0b;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .ai-hint-text {
        color: #8b9cb5;
        font-size: 14px;
        line-height: 1.6;
    }

    /* Excel-like grid */
    .excel-grid {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
    }

    .excel-grid th {
        background: #132340;
        position: sticky;
        top: 0;
        z-index: 1;
    }

    .excel-grid td {
        padding: 4px 8px;
        border: 1px solid #1e3a5f;
    }

    .excel-grid td.numeric {
        text-align: right;
        color: #f59e0b;
    }

    .excel-grid td.label {
        font-weight: 500;
        color: #f5f5f5;
    }

    .excel-grid td.override {
        background: rgba(245, 158, 11, 0.1);
    }

    /* Chat interface */
    .chat-message {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }

    .chat-message.user {
        background: #132340;
        border: 1px solid #1e3a5f;
    }

    .chat-message.assistant {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Scenario buttons */
    .scenario-btn {
        background: #132340;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
    }

    .scenario-btn:hover {
        border-color: #f59e0b;
        background: rgba(245, 158, 11, 0.05);
    }

    .scenario-btn-icon {
        font-size: 28px;
        margin-bottom: 8px;
    }

    .scenario-btn-title {
        color: #f5f5f5;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .scenario-btn-desc {
        color: #8b9cb5;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


def get_sheets_list():
    """Get list of available sheets from database"""
    session = get_session()
    try:
        sheets = session.query(Sheet).all()
        return [(s.name, s.description or s.name) for s in sheets]
    finally:
        session.close()


def get_sheet_as_dataframe(sheet_name: str, version_id: int = 1):
    """Load sheet data into a pandas DataFrame"""
    session = get_session()
    try:
        cells = session.query(CellValue).filter_by(
            version_id=version_id,
            sheet=sheet_name
        ).all()

        if not cells:
            return pd.DataFrame()

        # Build 2D grid
        max_row = max(c.row_num for c in cells if c.row_num)
        max_col = max(c.col_num for c in cells if c.col_num)

        # Create dataframe with column letters as headers
        columns = [num_to_col(i) for i in range(1, min(max_col + 1, 70))]
        data = {}

        for col_idx, col_letter in enumerate(columns, 1):
            col_data = []
            for row in range(1, min(max_row + 1, 500)):
                cell = next((c for c in cells if c.row_num == row and c.col_num == col_idx), None)
                if cell:
                    val = cell.final_value
                    if val is not None:
                        if isinstance(val, float) and val == int(val):
                            col_data.append(int(val))
                        else:
                            col_data.append(val)
                    else:
                        col_data.append('')
                else:
                    col_data.append('')
            data[col_letter] = col_data

        df = pd.DataFrame(data)
        df.index = range(1, len(df) + 1)
        return df
    finally:
        session.close()


def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">📊</div>
            <div class="logo-text">FM Pro</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown('<div class="nav-section-title">Навигация</div>', unsafe_allow_html=True)

        pages = {
            "dashboard": ("📊", "Dashboard"),
            "forms": ("📝", "Формы ввода"),
            "ai_chat": ("💬", "AI Ассистент"),
            "test_examples": ("🧪", "Тестовые примеры"),
            "new_model": ("➕", "Создание модели"),
            "scenarios": ("📈", "Сценарии")
        }

        # Initialize page state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"

        for page_id, (icon, label) in pages.items():
            if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()

        st.divider()

        # Project info
        st.markdown('<div class="nav-section-title">Текущий проект</div>', unsafe_allow_html=True)
        st.caption("Касаткина 7")
        st.caption("Версия: Базовая")

        # Version selector
        st.selectbox(
            "Версия",
            ["Базовая", "Сценарий КС+5%", "Факт Q3"],
            key="version_select",
            label_visibility="collapsed"
        )


def render_dashboard():
    """Render the main dashboard page"""
    st.markdown("## 📊 Dashboard — Касаткина 7")

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Выручка", "73.5 млрд", "+12%")
    with col2:
        st.metric("Расходы", "35.0 млрд", "-3%")
    with col3:
        st.metric("Маржа", "38.5 млрд", "+52%")
    with col4:
        st.metric("Площадь", "97.5 тыс м²", "")
    with col5:
        st.metric("Цена ср.", "754 т.р./м²", "+8%")

    st.divider()

    # Sheet tabs
    sheets = get_sheets_list()
    if sheets:
        sheet_names = [s[0] for s in sheets]

        # Use tabs for sheet selection
        tabs = st.tabs(sheet_names[:8])  # Limit to 8 tabs for UI

        for tab, sheet_name in zip(tabs, sheet_names[:8]):
            with tab:
                render_sheet_view(sheet_name)
    else:
        st.info("Нет данных в базе. Загрузите модель.")


def render_sheet_view(sheet_name: str):
    """Render a single sheet as Excel-like grid"""
    # Controls row
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search = st.text_input("🔍 Поиск", key=f"search_{sheet_name}", placeholder="Найти строку...")
    with col2:
        row_start = st.number_input("Строка с", min_value=1, value=1, key=f"row_start_{sheet_name}")
    with col3:
        row_end = st.number_input("по", min_value=1, value=100, key=f"row_end_{sheet_name}")
    with col4:
        if st.button("🔄 Обновить", key=f"refresh_{sheet_name}"):
            st.rerun()

    # Load and display data
    with st.spinner("Загрузка данных..."):
        df = get_sheet_as_dataframe(sheet_name)

    if df.empty:
        st.warning(f"Нет данных для листа {sheet_name}")
        return

    # Filter rows
    df_view = df.iloc[int(row_start)-1:int(row_end)]

    # Search filter
    if search:
        mask = df_view.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
        df_view = df_view[mask]

    # Display with formatting
    st.dataframe(
        df_view,
        use_container_width=True,
        height=500
    )

    # Row count info
    st.caption(f"Показано строк: {len(df_view)} из {len(df)}")


def render_forms():
    """Render forms input page"""
    st.markdown("## 📝 Формы ввода")

    form_tabs = st.tabs(["ТЭП", "Продажи", "Инвестиции", "Финансирование", "Прочее"])

    with form_tabs[0]:  # ТЭП
        st.markdown("### Технико-экономические показатели")

        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Общая площадь, м²", value=150000, key="tep_area")
            st.number_input("Продаваемая площадь, м²", value=97500, key="tep_sell_area")
            st.number_input("Количество квартир", value=1200, key="tep_units")
        with col2:
            st.number_input("Этажность", value=25, key="tep_floors")
            st.number_input("Машиномест", value=696, key="tep_parking")
            st.date_input("Дата ввода", key="tep_date")

        if st.button("💾 Сохранить ТЭП", key="save_tep"):
            st.success("ТЭП сохранены")

    with form_tabs[1]:  # Продажи
        st.markdown("### Параметры продаж")
        st.info("Здесь будет форма параметров продаж по категориям")

    with form_tabs[2]:  # Инвестиции
        st.markdown("### Инвестиционные затраты")
        st.info("Здесь будет форма инвестиционных затрат")

    with form_tabs[3]:  # Финансирование
        st.markdown("### Параметры финансирования")
        st.info("Здесь будет форма финансирования")

    with form_tabs[4]:  # Прочее
        st.markdown("### Прочие параметры")
        st.info("Здесь будут прочие параметры модели")


def render_ai_chat():
    """Render AI assistant chat interface"""
    st.markdown("## 💬 AI Ассистент")

    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Привет! Я AI-ассистент FM Pro. Могу помочь с анализом финансовой модели, расчетом сценариев и ответами на вопросы по проекту. Что вас интересует?"}
        ]

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <strong>Вы:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <strong>🤖 AI:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

    # Input
    st.divider()
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Ваш вопрос", key="chat_input", placeholder="Спросите что-нибудь о модели...")
    with col2:
        send_btn = st.button("📤 Отправить", key="send_msg")

    if send_btn and user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        # Placeholder response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Сейчас это демо-версия. Полная интеграция с Claude AI будет добавлена в следующих обновлениях."
        })
        st.rerun()

    # Quick actions
    st.divider()
    st.markdown("#### Быстрые действия")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Анализ модели", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Проанализируй текущую модель"})
            st.rerun()
    with col2:
        if st.button("💰 Проверь маржу", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Какая маржа по проекту?"})
            st.rerun()
    with col3:
        if st.button("⚠️ Риски проекта", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Какие есть риски?"})
            st.rerun()


def render_test_examples():
    """Render test examples page with ready dialogues"""
    st.markdown("## 🧪 Тестовые примеры")
    st.caption("Готовые диалоги для демонстрации возможностей системы")

    example_tabs = st.tabs(["📥 Загрузка факта", "📋 Проверка ковенантов", "🔄 Сравнение версий"])

    with example_tabs[0]:  # Факт
        st.markdown("### Загрузка фактических данных")

        st.markdown("""
        <div class="ai-hint">
            <div class="ai-hint-title">🤖 Пример диалога</div>
            <div class="ai-hint-text">
                <p><strong>Пользователь:</strong> Загрузи факт продаж за Q3 2025</p>
                <p><strong>AI:</strong> Загружаю фактические данные продаж за Q3 2025...</p>
                <p>Найдено расхождение с планом:</p>
                <ul>
                    <li>Квартиры: план 8,500 м², факт 9,200 м² (+8.2%)</li>
                    <li>Ритейл: план 1,200 м², факт 800 м² (-33%)</li>
                </ul>
                <p>Обновить прогноз с учетом факта?</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.file_uploader("Загрузить файл факта", type=['xlsx', 'csv'], key="fact_upload")

        if st.button("▶️ Запустить демо", key="demo_fact"):
            st.info("Демо загрузки факта будет здесь")

    with example_tabs[1]:  # Ковенанты
        st.markdown("### Проверка ковенантов")

        st.markdown("""
        <div class="ai-hint">
            <div class="ai-hint-title">🤖 Пример диалога</div>
            <div class="ai-hint-text">
                <p><strong>Пользователь:</strong> Проверь ковенанты по кредиту Сбера</p>
                <p><strong>AI:</strong> Проверяю ковенанты кредитного договора...</p>
                <p>Результаты:</p>
                <ul>
                    <li>✅ DSCR: 1.45 (мин. 1.2) — выполняется</li>
                    <li>✅ LTV: 58% (макс. 70%) — выполняется</li>
                    <li>⚠️ ICR: 1.18 (мин. 1.15) — близко к границе</li>
                </ul>
                <p>Рекомендую следить за ICR при повышении ставки.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("▶️ Запустить проверку", key="demo_covenants"):
            st.info("Демо проверки ковенантов будет здесь")

    with example_tabs[2]:  # Сравнение
        st.markdown("### Сравнение версий модели")

        st.markdown("""
        <div class="ai-hint">
            <div class="ai-hint-title">🤖 Пример диалога</div>
            <div class="ai-hint-text">
                <p><strong>Пользователь:</strong> Сравни базовый сценарий с КС+5%</p>
                <p><strong>AI:</strong> Сравниваю сценарии...</p>
                <p>Ключевые различия:</p>
                <ul>
                    <li>IRR проекта: 28% → 22% (-6 п.п.)</li>
                    <li>Срок окупаемости: 3.2 → 4.1 года</li>
                    <li>Процентные расходы: +2.4 млрд руб</li>
                </ul>
                <p>При ключевой ставке +5% проект остается рентабельным, но маржа снижается на 15%.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Версия 1", ["Базовая", "Сценарий КС+5%"], key="compare_v1")
        with col2:
            st.selectbox("Версия 2", ["Сценарий КС+5%", "Базовая"], key="compare_v2")

        if st.button("▶️ Сравнить версии", key="demo_compare"):
            st.info("Демо сравнения версий будет здесь")


def render_new_model():
    """Render new model creation wizard"""
    st.markdown("## ➕ Создание новой модели")
    st.caption("Пошаговый мастер создания финансовой модели")

    # Wizard steps
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    steps = ["Проект", "ТЭП", "Продажи", "Затраты", "Финансирование", "Итоги"]

    # Step indicators
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps), 1):
        with col:
            if i < st.session_state.wizard_step:
                st.markdown(f"<div style='text-align:center;color:#22c55e;'>✅ {step}</div>", unsafe_allow_html=True)
            elif i == st.session_state.wizard_step:
                st.markdown(f"<div style='text-align:center;color:#f59e0b;font-weight:bold;'>● {step}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;color:#5a7090;'>○ {step}</div>", unsafe_allow_html=True)

    st.divider()

    # Step content
    if st.session_state.wizard_step == 1:
        st.markdown("### Шаг 1: Информация о проекте")
        st.text_input("Название проекта", placeholder="Например: ЖК Солнечный")
        st.text_input("Адрес", placeholder="г. Москва, ул. Примерная, д. 1")
        st.selectbox("Тип проекта", ["Жилой комплекс", "Апартаменты", "Коммерческая недвижимость"])
        st.text_area("Описание", placeholder="Краткое описание проекта...")

    elif st.session_state.wizard_step == 2:
        st.markdown("### Шаг 2: Технико-экономические показатели")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Общая площадь, м²", value=100000)
            st.number_input("Жилая площадь, м²", value=70000)
        with col2:
            st.number_input("Этажность", value=20)
            st.number_input("Количество корпусов", value=3)

    elif st.session_state.wizard_step == 3:
        st.markdown("### Шаг 3: Параметры продаж")
        st.info("Здесь будут вводиться параметры продаж по категориям")

    elif st.session_state.wizard_step == 4:
        st.markdown("### Шаг 4: Структура затрат")
        st.info("Здесь будут вводиться затраты по статьям")

    elif st.session_state.wizard_step == 5:
        st.markdown("### Шаг 5: Финансирование")
        st.info("Здесь будут параметры кредитования и собственного капитала")

    else:
        st.markdown("### Шаг 6: Итоги и создание")
        st.success("Все данные введены! Модель готова к созданию.")
        if st.button("🚀 Создать модель", key="create_model"):
            st.balloons()
            st.success("Модель создана!")

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.session_state.wizard_step > 1:
            if st.button("← Назад"):
                st.session_state.wizard_step -= 1
                st.rerun()
    with col3:
        if st.session_state.wizard_step < len(steps):
            if st.button("Далее →"):
                st.session_state.wizard_step += 1
                st.rerun()


def render_scenarios():
    """Render scenario modeling placeholder with AI chat and buttons"""
    st.markdown("## 📈 Сценарное моделирование")
    st.caption("Анализ чувствительности и стресс-тестирование модели")

    # Scenario buttons grid
    st.markdown("### Выберите тип анализа")

    col1, col2, col3, col4 = st.columns(4)

    scenarios = [
        ("🎲", "Монте-Карло", "Вероятностный анализ с 1000+ итераций", col1),
        ("📉", "Стресс-тесты", "Анализ экстремальных сценариев", col2),
        ("🎯", "Чувствительность", "Влияние ключевых параметров", col3),
        ("🏠", "Продажи", "Моделирование темпов продаж", col4),
    ]

    for icon, title, desc, col in scenarios:
        with col:
            st.markdown(f"""
            <div class="scenario-btn">
                <div class="scenario-btn-icon">{icon}</div>
                <div class="scenario-btn-title">{title}</div>
                <div class="scenario-btn-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Выбрать", key=f"scenario_{title}", use_container_width=True):
                st.session_state.selected_scenario = title

    col1, col2, col3, col4 = st.columns(4)

    scenarios2 = [
        ("💰", "Затраты", "Вариации себестоимости", col1),
        ("📊", "Ключевая ставка", "Влияние ставки ЦБ", col2),
        ("⏱️", "Сроки", "Анализ задержек проекта", col3),
        ("🔧", "Кастомный", "Настроить свой сценарий", col4),
    ]

    for icon, title, desc, col in scenarios2:
        with col:
            st.markdown(f"""
            <div class="scenario-btn">
                <div class="scenario-btn-icon">{icon}</div>
                <div class="scenario-btn-title">{title}</div>
                <div class="scenario-btn-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Выбрать", key=f"scenario2_{title}", use_container_width=True):
                st.session_state.selected_scenario = title

    st.divider()

    # AI Chat for scenarios
    st.markdown("### 💬 AI-помощник по сценариям")

    st.markdown("""
    <div class="ai-hint">
        <div class="ai-hint-title">🤖 Как я могу помочь</div>
        <div class="ai-hint-text">
            Выберите тип анализа выше или опишите своими словами, какой сценарий вы хотите промоделировать.
            <br><br>
            Примеры запросов:
            <ul>
                <li>"Что будет с IRR при росте ключевой ставки на 3%?"</li>
                <li>"Посчитай сценарий падения цен на 15%"</li>
                <li>"Сделай стресс-тест с задержкой ввода на 6 месяцев"</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scenario chat input
    scenario_input = st.text_input(
        "Опишите сценарий",
        key="scenario_input",
        placeholder="Например: что будет если продажи упадут на 20%?"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🚀 Рассчитать", key="calc_scenario"):
            if scenario_input:
                st.info(f"Расчет сценария: {scenario_input}")
                st.warning("Полная интеграция с AI будет добавлена в следующих обновлениях")


def main():
    """Main application entry point"""
    render_sidebar()

    # Route to current page
    page = st.session_state.get('current_page', 'dashboard')

    if page == 'dashboard':
        render_dashboard()
    elif page == 'forms':
        render_forms()
    elif page == 'ai_chat':
        render_ai_chat()
    elif page == 'test_examples':
        render_test_examples()
    elif page == 'new_model':
        render_new_model()
    elif page == 'scenarios':
        render_scenarios()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
