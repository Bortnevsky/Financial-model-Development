# FM Pro Demo — План разработки

> **Статус:** Готов к разработке
> **Дата:** 22.01.2026
> **Модель для демо:** FM_Касаткина2.xlsx (62 194 ячейки, 49 121 формула)

---

## Приветствие для нового чата

```
Привет! Продолжаем разработку FM Pro Demo.

Контекст:
- Репозиторий: https://github.com/Bortnevsky/Financial-model-Development
- План и статус: см. DEMO_PLAN.md в репозитории
- Модель для демо: FM_Касаткина2.xlsx (уже в репо)
- JSON модель: fm_model.json (62K ячеек)
- pycel работает — пересчёт формул проверен

Что уже сделано:
- [x] Excel → JSON конвертер
- [x] Базовый AI chat (mockup/ai-chat.html)
- [x] pycel интеграция проверена
- [x] Найдены ячейки ставок (TS1!J85 — ключевая ставка)

Следующий шаг: ШАГ 1 — создание SQLite базы и справочников.

Начинаем?
```

---

## 1. Функционал демо (подробно)

### 1.1. Загрузка и хранение модели

| Функция | Описание | Как работает |
|---------|----------|--------------|
| **Импорт Excel** | Загрузка FM_Касаткина2.xlsx в систему | Excel → JSON → SQLite |
| **Структура БД** | Хранение ячеек с тремя слоями | calc_value, override_value, final_value |
| **Справочники** | Показатели, листы, секции | Извлекаются из колонки B листов |

### 1.2. Просмотр данных

| Функция | Описание | UI |
|---------|----------|-----|
| **Выбор листа** | Переключение между CF, CF2, ПРОДАЖИ и др. | Dropdown |
| **Таблица данных** | Строки = показатели, колонки = периоды | AG Grid стиль |
| **Информация о ячейке** | Клик → формула, значение, статус | Sidebar/popup |
| **Цветовая индикация** | Жёлтый = override, зелёный = факт | Подсветка ячеек |

### 1.3. Анализ через Claude AI

| Функция | Пример запроса | Ответ |
|---------|----------------|-------|
| **Объяснение формулы** | "Что в CF2!P87?" | Формула + разбор + бизнес-смысл |
| **ТЭП проекта** | "Покажи основные показатели" | Таблица с реальными данными из БД |
| **Структура затрат** | "Покажи расходы по статьям" | Группировка по справочнику |
| **Действия** | "Измени продажи июль на 500" | Запись в БД + подтверждение |

### 1.4. Override (ручная правка)

| Функция | Описание | Логика |
|---------|----------|--------|
| **Установка override** | Ввод значения поверх расчёта | override_value = X, final = override ?? calc |
| **Снятие override** | Возврат к расчётному | override_value = NULL, final = calc |
| **Визуализация** | Жёлтый фон + иконка ✎ | CSS класс |
| **Аудит** | Запись в cell_events | who, when, old, new, reason |

### 1.5. Волна распределения (ключевая фича!)

**Сценарий:** Пользователь меняет продажи в июле с 8208 на 500 м². Дельта +7708 м² должна распределиться по остальным периодам.

| Алгоритм | Описание | Формула |
|----------|----------|---------|
| **Пропорционально** | По весу каждого периода | new[i] = old[i] × (1 + delta/sum_others) |
| **Равномерно** | Поровну на все | new[i] = old[i] + delta/count |
| **В хвост** | Всё на последний период | new[last] = old[last] + delta |
| **S-кривая** | Больше в середину | Сигмоида с пиком в центре |

**UI модалки:**
```
┌─────────────────────────────────────────────────────────┐
│  Перераспределение дельты                          [×]  │
├─────────────────────────────────────────────────────────┤
│  +7 708 м² к распределению                              │
│  Изменение в июль: 8 208 → 500 м²                       │
├─────────────────────────────────────────────────────────┤
│  Как распределить?                                      │
│                                                         │
│  [■ Пропорционально]  [Равномерно]                     │
│  [В хвост]            [S-кривая]                       │
├─────────────────────────────────────────────────────────┤
│  Превью распределения:                                  │
│  [график с барами по месяцам]                          │
├─────────────────────────────────────────────────────────┤
│  [Только эту ячейку]     [Применить волну]             │
└─────────────────────────────────────────────────────────┘
```

**Режимы ИТОГО:**
- **Сохранить ИТОГО** — волна балансирует, сумма не меняется
- **Изменить ИТОГО** — пересчёт зависимых показателей

### 1.6. Пересчёт модели (pycel)

| Функция | Описание | Пример |
|---------|----------|--------|
| **Evaluate** | Вычислить значение ячейки | `calc.evaluate('CF2!P87')` → 570.21 |
| **Set value** | Изменить входной параметр | `calc.set_value('TS1!J85', 0.25)` |
| **Recalculate** | Пересчитать зависимые | Автоматически при evaluate |

### 1.7. Сценарии

| Сценарий | Параметр | Ячейка | Эффект |
|----------|----------|--------|--------|
| **Ключевая ставка** | % | TS1!J85 | Ставка ПФ, проценты по кредитам |
| **Цены продаж** | % изменения | ПРОДАЖИ | Выручка, маржа |
| **СМР** | % изменения | DB/DETAILS | Себестоимость |
| **Темп продаж** | м²/мес | ПРОДАЖИ | Сроки, кредитная нагрузка |

**Процесс:**
1. Выбрать тип сценария
2. Ввести параметры (%, абсолютное значение)
3. Система создаёт копию версии
4. pycel пересчитывает модель
5. Показать сравнение "было/стало"
6. Сохранить или отменить

### 1.8. Загрузка факта

| Шаг | Описание |
|-----|----------|
| 1 | Загрузить Excel с первичкой (формат листа FACT) |
| 2 | Парсинг: дата, сумма, контрагент, назначение |
| 3 | AI матчинг: сопоставление с показателями в БД |
| 4 | Проверка лимитов: план vs факт |
| 5 | Запись в cell_values с типом 'fact' |
| 6 | Алерт при превышении |

### 1.9. Версионирование

| Функция | Описание |
|---------|----------|
| **Создать версию** | Snapshot текущего состояния |
| **Список версий** | "Базовая", "После торгов", "Сценарий КС+5%" |
| **Переключение** | Загрузить данные выбранной версии |
| **Сравнение** | Diff двух версий — что изменилось |

---

## 2. Архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                       │
│                      Streamlit (демо)                                    │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Таблицы    │  │   Волна     │  │    Чат      │  │   Факт      │    │
│  │  (данные)   │  │  (модалка)  │  │  (Claude)   │  │  (загрузка) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                        │
│                      Python modules                                      │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  db/            │  │  engine/        │  │  ai/            │         │
│  │  - schema.py    │  │  - calc.py      │  │  - claude.py    │         │
│  │  - queries.py   │  │  - wave.py      │  │  - prompts.py   │         │
│  │  - import.py    │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          STORAGE                                         │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  SQLite: fm_demo.db                                               │  │
│  │                                                                   │  │
│  │  projects    indicators    sheets    cell_values    fm_versions  │  │
│  │  cell_events                                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Files:                                                           │  │
│  │  - FM_Касаткина2.xlsx (исходный Excel для pycel)                 │  │
│  │  - fm_model.json (для быстрого доступа)                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Структура БД

### Таблицы

```sql
-- Проекты
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник показателей (извлекается из модели)
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY,
    code TEXT,                    -- "B87", "B97"
    name TEXT NOT NULL,           -- "ПОСТУПЛЕНИЕ", "% КРЕДИТ проектное фин-ие"
    sheet TEXT NOT NULL,          -- "CF2"
    row_num INTEGER,              -- 87
    section TEXT,                 -- "ФИНАНСИРОВАНИЕ"
    indicator_type TEXT,          -- "input", "formula", "sum"
    allow_override BOOLEAN DEFAULT 1,
    allow_distribution BOOLEAN DEFAULT 1
);

-- Листы модели
CREATE TABLE sheets (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,    -- "CF2", "ПРОДАЖИ"
    rows_count INTEGER,
    cols_count INTEGER,
    description TEXT
);

-- Версии модели
CREATE TABLE fm_versions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    version_number INTEGER NOT NULL,
    name TEXT,                    -- "Базовая", "Сценарий КС+5%"
    is_scenario BOOLEAN DEFAULT 0,
    parent_version_id INTEGER REFERENCES fm_versions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ячейки данных (главная таблица)
CREATE TABLE cell_values (
    id INTEGER PRIMARY KEY,
    version_id INTEGER REFERENCES fm_versions(id),
    sheet TEXT NOT NULL,
    address TEXT NOT NULL,        -- "P87"
    row_num INTEGER,
    col_num INTEGER,

    -- Три слоя значений
    formula TEXT,                 -- "=IF(P5<'DB2'!$U$25,...)"
    calc_value REAL,              -- расчётное значение
    override_value REAL,          -- ручное значение

    -- Метаданные
    value_type TEXT,              -- "plan", "fact", "forecast"
    format TEXT,                  -- "#,##0"
    is_locked BOOLEAN DEFAULT 0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(version_id, sheet, address)
);

-- View для final_value
CREATE VIEW cells_final AS
SELECT
    *,
    COALESCE(override_value, calc_value) AS final_value,
    CASE
        WHEN override_value IS NOT NULL THEN 'override'
        WHEN calc_value IS NOT NULL THEN 'calc'
        ELSE 'empty'
    END AS value_status
FROM cell_values;

-- Аудит изменений
CREATE TABLE cell_events (
    id INTEGER PRIMARY KEY,
    cell_id INTEGER REFERENCES cell_values(id),
    event_type TEXT NOT NULL,     -- "override", "calc", "fact", "wave"
    old_value REAL,
    new_value REAL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_cells_version ON cell_values(version_id);
CREATE INDEX idx_cells_sheet ON cell_values(sheet);
CREATE INDEX idx_cells_address ON cell_values(sheet, address);
CREATE INDEX idx_indicators_sheet ON indicators(sheet);
```

---

## 4. Шаги реализации

### ШАГ 1: База данных + Справочники
**Файлы:** `db/schema.py`, `db/init_db.py`, `db/seed_data.py`

**Проверки:**
```bash
python db/init_db.py
# ✅ fm_demo.db создан

sqlite3 fm_demo.db ".tables"
# ✅ projects indicators sheets cell_values fm_versions cell_events

sqlite3 fm_demo.db "SELECT COUNT(*) FROM indicators"
# ✅ > 100 записей
```

---

### ШАГ 2: Импорт данных
**Файлы:** `db/import_model.py`

**Проверки:**
```bash
python db/import_model.py fm_model.json
# ✅ Импортировано 62194 ячеек

sqlite3 fm_demo.db "SELECT COUNT(*) FROM cell_values"
# ✅ 62194

sqlite3 fm_demo.db "SELECT formula FROM cell_values WHERE sheet='CF2' AND address='P87'"
# ✅ =IF(P5<'DB2'!$U$25,IF(-(P178)>0,-P178,0),0)
```

---

### ШАГ 3: Базовые запросы
**Файлы:** `db/queries.py`

**Проверки:**
```python
from db.queries import get_cell, get_sheet_data
cell = get_cell('CF2', 'P87')
# ✅ {'formula': '=IF(...)', 'calc_value': 570.21, ...}
```

---

### ШАГ 4: Расчётный движок
**Файлы:** `engine/calc_engine.py`

**Проверки:**
```python
from engine.calc_engine import CalcEngine
calc = CalcEngine('FM_Касаткина2.xlsx')
calc.evaluate('TS1!J85')  # ✅ 0.2
calc.set_value('TS1!J85', 0.25)
calc.evaluate('DB!P24')   # ✅ 0.288
```

---

### ШАГ 5: Override логика
**Файлы:** обновление `db/queries.py`

**Проверки:**
```python
from db.queries import set_override, get_cell
set_override('CF2', 'P87', 999.99, 'тест')
get_cell('CF2', 'P87')['final_value']  # ✅ 999.99
```

---

### ШАГ 6: Волна распределения
**Файлы:** `engine/wave_engine.py`

**Проверки:**
```python
from engine.wave_engine import apply_wave
old = {'янв': 100, 'фев': 200, 'мар': 300}
new = apply_wave(old, 'фев', 100, 'proportional')
# ✅ {'янв': 125, 'фев': 100, 'мар': 375}, sum=600
```

---

### ШАГ 7: Streamlit — таблицы
**Файлы:** `app/main.py`, `app/pages/tables.py`

**Проверки:**
```bash
streamlit run app/main.py
# ✅ Открывается localhost:8501
# ✅ Видны данные листа CF2
```

---

### ШАГ 8: Streamlit — волна
**Файлы:** `app/pages/wave.py`

**Проверки:**
- ✅ Клик на ячейку → модалка
- ✅ Выбор алгоритма → превью
- ✅ "Применить" → данные обновляются

---

### ШАГ 9: Claude интеграция
**Файлы:** `ai/claude_service.py`, `ai/prompts.py`

**Проверки:**
```
Ввод: "Что в CF2!P87?"
# ✅ Ответ с формулой и объяснением

Ввод: "Покажи ТЭП"
# ✅ Таблица с данными из БД
```

---

### ШАГ 10: Загрузка факта
**Файлы:** `app/pages/fact.py`, `db/fact_loader.py`

**Проверки:**
- ✅ Upload Excel
- ✅ Парсинг данных
- ✅ Запись в БД

---

### ШАГ 11: Версионирование
**Файлы:** `db/versions.py`

**Проверки:**
```python
from db.versions import create_version, list_versions
create_version('После корректировки')
list_versions()  # ✅ [{'id': 1, 'name': 'Базовая'}, {'id': 2, 'name': 'После корректировки'}]
```

---

### ШАГ 12: Сценарии
**Файлы:** `engine/scenarios.py`

**Проверки:**
```python
from engine.scenarios import create_scenario
create_scenario('КС +5%', {'TS1!J85': 0.25})
# ✅ Создана версия-сценарий с пересчитанными данными
```

---

## 5. Что уже сделано

- [x] Репозиторий на GitHub
- [x] Excel файл модели (FM_Касаткина2.xlsx)
- [x] JSON конвертер (excel_to_json.py)
- [x] JSON модель (fm_model.json, 4 MB)
- [x] Базовый AI chat (mockup/ai-chat.html)
- [x] Проверка pycel — пересчёт работает
- [x] Найдены ключевые ячейки ставок
- [x] ТЗ и методика в репозитории

---

## 6. Ссылки

- **Репозиторий:** https://github.com/Bortnevsky/Financial-model-Development
- **ТЗ:** [tz_fm_final.md](tz_fm_final.md)
- **Методика:** Методика ФМ_19-01-2026_сценарий (1).docx

---

## 7. Контакты

При вопросах по архитектуре или функционалу — см. ТЗ или спрашивай в чате.
