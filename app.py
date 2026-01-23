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
import os

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="FM Pro Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(180deg, #0a1628 0%, #0d1e38 100%);
    }

    /* Sidebar always visible */
    [data-testid="stSidebar"] {
        background: #0f1f3d;
        min-width: 280px;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }

    /* Hide hamburger menu */
    [data-testid="collapsedControl"] {
        display: none;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #f5f5f5 !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #f59e0b !important;
        font-size: 2rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: #8b9cb5 !important;
    }

    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    /* Dataframe */
    .stDataFrame {
        background: #0f1f3d;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #0f1f3d;
        padding: 8px;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #132340;
        border-radius: 6px;
        color: #8b9cb5;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: #f59e0b !important;
        color: #000 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #000;
        border: none;
        font-weight: 600;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
    }

    /* Radio buttons in sidebar as menu */
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }

    [data-testid="stSidebar"] .stRadio > div {
        flex-direction: column;
        gap: 4px;
    }

    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        padding: 12px 16px;
        border-radius: 8px;
        color: #8b9cb5;
        cursor: pointer;
        margin: 0;
    }

    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: #132340;
        color: #f5f5f5;
    }

    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border-left: 3px solid #f59e0b;
    }

    /* Info boxes */
    .stAlert {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #f5f5f5;
    }

    /* Text */
    p, span, div {
        color: #e0e0e0;
    }

    /* Logo */
    .logo-box {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-right: 12px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }

    .logo-text {
        font-size: 24px;
        font-weight: 700;
        color: #f5f5f5;
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
    }

    .kpi-label {
        font-size: 14px;
        color: #8b9cb5;
        margin-top: 8px;
    }

    /* Section title */
    .section-title {
        font-size: 11px;
        text-transform: uppercase;
        color: #5a7090;
        letter-spacing: 1px;
        margin: 20px 0 10px 0;
        padding-left: 16px;
    }

    /* Chat message */
    .chat-ai {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    .chat-user {
        background: #132340;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


def check_database():
    """Check if database exists and has data"""
    db_path = Path(__file__).parent / "fm_demo.db"

    if not db_path.exists():
        return False, "База данных не найдена"

    if db_path.stat().st_size < 1000:  # Less than 1KB = empty
        return False, "База данных пустая (0 байт)"

    try:
        session = get_session()
        count = session.query(CellValue).count()
        session.close()
        if count == 0:
            return False, "В базе нет данных"
        return True, f"База OK: {count:,} ячеек"
    except Exception as e:
        return False, f"Ошибка базы: {str(e)}"


def get_sheets_list():
    """Get list of available sheets"""
    try:
        session = get_session()
        sheets = session.query(Sheet).all()
        result = [s.name for s in sheets]
        session.close()
        return result
    except Exception as e:
        return []


def load_sheet_data(sheet_name: str, version_id: int = 1):
    """Load sheet as DataFrame"""
    session = get_session()
    try:
        cells = session.query(CellValue).filter_by(
            version_id=version_id,
            sheet=sheet_name
        ).all()

        if not cells:
            return pd.DataFrame()

        max_row = max((c.row_num for c in cells if c.row_num), default=0)
        max_col = max((c.col_num for c in cells if c.col_num), default=0)

        # Limit for performance
        max_row = min(max_row, 200)
        max_col = min(max_col, 50)

        # Build grid
        columns = [num_to_col(i) for i in range(1, max_col + 1)]
        data = {col: [''] * max_row for col in columns}

        for cell in cells:
            if cell.row_num and cell.col_num and cell.row_num <= max_row and cell.col_num <= max_col:
                col_letter = num_to_col(cell.col_num)
                val = cell.final_value
                if val is not None:
                    if isinstance(val, float):
                        if val == int(val):
                            data[col_letter][cell.row_num - 1] = int(val)
                        else:
                            data[col_letter][cell.row_num - 1] = round(val, 2)
                    else:
                        data[col_letter][cell.row_num - 1] = val

        df = pd.DataFrame(data)
        df.index = range(1, len(df) + 1)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
    finally:
        session.close()


# ============================================
# SIDEBAR - Always visible menu
# ============================================
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display: flex; align-items: center; padding: 16px 0; margin-bottom: 20px;">
        <div class="logo-box">📊</div>
        <span class="logo-text">FM Pro</span>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown('<div class="section-title">НАВИГАЦИЯ</div>', unsafe_allow_html=True)

    page = st.radio(
        "Меню",
        [
            "📊 Dashboard",
            "📋 Таблицы модели",
            "💬 AI Ассистент",
            "🧪 Тестовые примеры",
            "➕ Новая модель",
            "📈 Сценарии"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Project info
    st.markdown('<div class="section-title">ПРОЕКТ</div>', unsafe_allow_html=True)
    st.markdown("**Касаткина 7**")
    st.caption("Версия: Базовая")

    version = st.selectbox(
        "Выбор версии",
        ["Базовая", "Сценарий КС+5%", "Факт Q3 2025"],
        label_visibility="collapsed"
    )


# ============================================
# DATABASE CHECK
# ============================================
db_ok, db_status = check_database()

if not db_ok:
    st.error(f"⚠️ Проблема с базой данных: {db_status}")
    st.markdown("""
    ### Как исправить (Windows):

    Откройте командную строку в папке проекта и выполните:

    ```bash
    del fm_demo.db
    git fetch origin claude/add-model-selection-0dfbH
    git checkout origin/claude/add-model-selection-0dfbH -- fm_demo.db
    ```

    Затем перезапустите Streamlit: `streamlit run app.py`
    """)
    st.stop()

# ============================================
# MAIN CONTENT
# ============================================

if page == "📊 Dashboard":
    st.markdown("## 📊 Финансовая модель — Касаткина 7")

    # Load DB sheet data (main dashboard view like Excel)
    df = load_sheet_data("DB")

    if not df.empty:
        # Section tabs for Excel-like navigation
        tabs = st.tabs(["ТЭП", "ДОХОДЫ", "ИНВЕСТИЦИИ", "ФИНАНСИРОВАНИЕ", "СРОКИ", "РЕЗУЛЬТАТ", "Вся модель"])

        # Section row ranges (approximate, based on typical FM structure)
        sections = {
            "ТЭП": (1, 35),
            "ДОХОДЫ": (36, 90),
            "ИНВЕСТИЦИИ": (91, 150),
            "ФИНАНСИРОВАНИЕ": (151, 200),
            "СРОКИ": (201, 230),
            "РЕЗУЛЬТАТ": (231, 280)
        }

        for i, (section_name, (row_start, row_end)) in enumerate(sections.items()):
            with tabs[i]:
                st.markdown(f"### {section_name}")
                df_section = df.iloc[max(0, row_start-1):min(len(df), row_end)]
                if not df_section.empty:
                    st.dataframe(df_section, use_container_width=True, height=500)
                else:
                    st.info("Нет данных для этого раздела")

        # Full model view
        with tabs[-1]:
            st.markdown("### Вся модель")
            col1, col2 = st.columns([1, 1])
            with col1:
                row_from = st.number_input("Строки с", min_value=1, value=1, key="dash_row_from")
            with col2:
                row_to = st.number_input("по", min_value=1, value=100, key="dash_row_to")

            df_view = df.iloc[int(row_from)-1:int(row_to)]
            st.dataframe(df_view, use_container_width=True, height=600)
            st.caption(f"Показано строк: {len(df_view)} из {len(df)}")

    else:
        st.warning("Нет данных для листа DB. Проверьте базу данных.")


elif page == "📋 Таблицы модели":
    st.markdown("## 📋 Таблицы модели")
    st.caption("Данные финансовой модели как в Excel")

    sheets = get_sheets_list()

    if sheets:
        # Sheet tabs
        selected_sheet = st.selectbox("Выберите лист", sheets)

        # Controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Поиск по таблице", placeholder="Введите текст...")
        with col2:
            row_from = st.number_input("Строки с", min_value=1, value=1)
        with col3:
            row_to = st.number_input("по", min_value=1, value=100)

        # Load and show data
        with st.spinner("Загрузка данных..."):
            df = load_sheet_data(selected_sheet)

        if not df.empty:
            # Filter rows
            df_view = df.iloc[int(row_from)-1:int(row_to)]

            # Search filter
            if search:
                mask = df_view.astype(str).apply(
                    lambda x: x.str.contains(search, case=False, na=False)
                ).any(axis=1)
                df_view = df_view[mask]

            st.dataframe(df_view, use_container_width=True, height=600)
            st.caption(f"Показано строк: {len(df_view)} из {len(df)}")
        else:
            st.warning(f"Нет данных для листа {selected_sheet}")
    else:
        st.info("Нет данных в базе. Загрузите финансовую модель.")


elif page == "💬 AI Ассистент":
    st.markdown("## 💬 AI Ассистент")
    st.caption("Задайте вопрос по финансовой модели")

    # Chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Привет! Я AI-ассистент FM Pro. Могу помочь с анализом модели, расчетом сценариев, проверкой ковенантов. Что вас интересует?"}
        ]

    # Display messages
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Ваш вопрос...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Placeholder response
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Сейчас это демо-версия. Полная интеграция с Claude AI будет в следующем обновлении."
        })
        st.rerun()

    # Quick actions
    st.markdown("---")
    st.markdown("**Быстрые вопросы:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Анализ модели", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Проанализируй текущую модель"})
            st.rerun()
    with col2:
        if st.button("💰 Проверь маржу", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Какая маржа по проекту?"})
            st.rerun()
    with col3:
        if st.button("⚠️ Риски", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Какие есть риски?"})
            st.rerun()


elif page == "🧪 Тестовые примеры":
    st.markdown("## 🧪 Тестовые примеры")
    st.caption("Готовые сценарии для демонстрации")

    tab1, tab2, tab3 = st.tabs(["📥 Загрузка факта", "📋 Ковенанты", "🔄 Сравнение"])

    with tab1:
        st.markdown("### Загрузка фактических данных")
        st.markdown("""
        <div class="chat-ai">
            <strong>Пример диалога:</strong><br><br>
            👤 <em>Загрузи факт продаж за Q3 2025</em><br><br>
            🤖 Загружаю данные... Найдено расхождение:<br>
            • Квартиры: план 8,500 м², факт 9,200 м² (+8.2%)<br>
            • Ритейл: план 1,200 м², факт 800 м² (-33%)<br><br>
            Обновить прогноз?
        </div>
        """, unsafe_allow_html=True)

        st.file_uploader("Загрузить файл факта", type=['xlsx', 'csv'])
        st.button("▶️ Запустить демо")

    with tab2:
        st.markdown("### Проверка ковенантов")
        st.markdown("""
        <div class="chat-ai">
            <strong>Пример диалога:</strong><br><br>
            👤 <em>Проверь ковенанты по кредиту Сбера</em><br><br>
            🤖 Проверяю...<br>
            ✅ DSCR: 1.45 (мин. 1.2) — ОК<br>
            ✅ LTV: 58% (макс. 70%) — ОК<br>
            ⚠️ ICR: 1.18 (мин. 1.15) — близко к границе
        </div>
        """, unsafe_allow_html=True)

        st.button("▶️ Проверить ковенанты")

    with tab3:
        st.markdown("### Сравнение версий")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Версия 1", ["Базовая", "КС+5%", "Факт Q3"])
        with col2:
            st.selectbox("Версия 2", ["КС+5%", "Базовая", "Факт Q3"])

        st.button("▶️ Сравнить")


elif page == "➕ Новая модель":
    st.markdown("## ➕ Создание новой модели")
    st.caption("Пошаговый мастер")

    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    steps = ["1. Проект", "2. ТЭП", "3. Продажи", "4. Затраты", "5. Финансирование", "6. Итоги"]

    # Progress
    st.progress(st.session_state.wizard_step / len(steps))
    st.caption(f"Шаг {st.session_state.wizard_step} из {len(steps)}: {steps[st.session_state.wizard_step-1]}")

    st.markdown("---")

    # Step content
    if st.session_state.wizard_step == 1:
        st.text_input("Название проекта", placeholder="ЖК Солнечный")
        st.text_input("Адрес", placeholder="г. Москва, ул. Примерная")
        st.selectbox("Тип", ["Жилой комплекс", "Апартаменты", "Коммерция"])
    elif st.session_state.wizard_step == 2:
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Общая площадь, м²", value=100000)
            st.number_input("Жилая площадь, м²", value=70000)
        with col2:
            st.number_input("Этажность", value=20)
            st.number_input("Корпусов", value=3)
    else:
        st.info(f"Шаг {st.session_state.wizard_step} в разработке")

    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
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


elif page == "📈 Сценарии":
    st.markdown("## 📈 Сценарное моделирование")
    st.caption("Анализ чувствительности и стресс-тесты")

    # Scenario buttons
    st.markdown("### Выберите тип анализа")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: #0f1f3d; border: 1px solid #1e3a5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🎲</div>
            <div style="color: #f5f5f5; font-weight: 600;">Монте-Карло</div>
            <div style="color: #8b9cb5; font-size: 12px;">1000+ итераций</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Выбрать", key="mc", use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background: #0f1f3d; border: 1px solid #1e3a5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📉</div>
            <div style="color: #f5f5f5; font-weight: 600;">Стресс-тесты</div>
            <div style="color: #8b9cb5; font-size: 12px;">Экстремальные сценарии</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Выбрать", key="stress", use_container_width=True)

    with col3:
        st.markdown("""
        <div style="background: #0f1f3d; border: 1px solid #1e3a5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🎯</div>
            <div style="color: #f5f5f5; font-weight: 600;">Чувствительность</div>
            <div style="color: #8b9cb5; font-size: 12px;">Ключевые параметры</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Выбрать", key="sens", use_container_width=True)

    with col4:
        st.markdown("""
        <div style="background: #0f1f3d; border: 1px solid #1e3a5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
            <div style="color: #f5f5f5; font-weight: 600;">Ключевая ставка</div>
            <div style="color: #8b9cb5; font-size: 12px;">Влияние ставки ЦБ</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Выбрать", key="rate", use_container_width=True)

    st.markdown("---")

    # AI Chat
    st.markdown("### 💬 Опишите сценарий")
    scenario_input = st.text_input("", placeholder="Например: что будет если продажи упадут на 20%?")

    if st.button("🚀 Рассчитать", use_container_width=False):
        if scenario_input:
            st.info("Расчет сценария в разработке")
