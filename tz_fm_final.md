# ТЗ: AI-First операционная финмодель девелопера

## Версия документа
- Дата: 21.01.2026
- Статус: Готово к разработке

---

## 1. Концепция продукта

### Суть
Финансовая модель девелоперского проекта с двумя режимами работы:
- **Чат-визард** — создание и корректировка модели через диалог с AI
- **Таблицы** — классический Excel-подобный интерфейс для хардкорных финансистов

Оба режима работают с одними данными. Ввёл в чате — видно в таблицах. Поправил в таблице — чат знает.

### Ключевая идея
AI не считает — AI только понимает запрос и формирует ответ. Все расчёты в Python.

### Pitch
> "Создай финмодель девелоперского проекта голосом за 10 минут. Или работай как привык — в таблицах. Одни данные, два интерфейса."

---

## 2. Основные сценарии

### 2.1. Создание модели (чат-визард)

```
Шаг 1. Структура    → Название, регион, ПК, ЗУ
Шаг 2. ТЭП          → Площади, виды ОН, LF%
Шаг 3. Сроки        → Старт, длительность, этапы
Шаг 4. Доходы       → Цены, рост, темп продаж
Шаг 5. Расходы      → Земля, СМР, коммерция, АХР
Шаг 6. Финансирование → ПФ, ставка, эскроу
Шаг 7. Итоги        → Сводка, графики, сохранение
```

Время: 5-10 минут. Каждый шаг — подтверждение и сохранение.

### 2.2. Внесение факта

```
Шаг 1. Уведомление  → Новая транзакция из 1С
Шаг 2. Идентификация → Найти договор, статью, проект
Шаг 3. Проверка лимита → В бюджете или превышение
Шаг 4. Разнесение   → Записать в накопительную ведомость
```

При превышении: запрос на пересмотр / покрыть из другой статьи / провести с превышением.

### 2.3. Корректировка плана

```
Шаг 1. Инициация    → "СМР март уменьшить с 100 до 80"
Шаг 2. Уточнение    → Экономия vs перенос vs ручное
Шаг 3. Предпросмотр → Таблица было/стало
Шаг 4. Применение   → Сохранить, создать версию
```

### 2.4. Сценарное моделирование

```
Шаг 1. Запрос       → "Что если цены +15%?"
Шаг 2. Эластичность → Выбор коэффициента [0.3] [0.5] [0.7] [1.0] [____]
Шаг 3. Расчёт       → Таблица сравнения, влияние на маржу
Шаг 4. Варианты     → Компенсация, оптимум, сохранение сценария
Шаг 5. Решение      → Отправить CFO, сделать основным
```

---

## 3. Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                         React + TypeScript                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         APP SHELL                                    │   │
│  │  • Header: проект, версия, переключатель [Чат]/[Таблицы]            │   │
│  │  • Sidebar: навигация, проекты, контекст                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐   │
│  │       CHAT INTERFACE         │  │     SPREADSHEET INTERFACE        │   │
│  │                              │  │                                  │   │
│  │  • Сообщения (markdown)      │  │  • AG Grid таблицы               │   │
│  │  • Кнопки-действия           │  │  • Табы разделов                 │   │
│  │  • Inline-таблицы            │  │  • Toolbar                       │   │
│  │  • Inline-графики            │  │  • Мини-чат (🤖 кнопка)          │   │
│  │  • Голосовой ввод            │  │                                  │   │
│  │  • Модалки распределений     │  │  • Модалки распределений         │   │
│  └──────────────────────────────┘  └──────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DISTRIBUTION MODAL                                │   │
│  │  • Ползунки (интерактивные, двусторонняя связь)                     │   │
│  │  • Таблица значений (editable)                                      │   │
│  │  • Алгоритмы волны (выбор, кастомные)                               │   │
│  │  • Анимация перераспределения                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Графики: Recharts (простые) + ECharts (сложные: waterfall, sankey)        │
│  Таблицы: AG Grid Enterprise                                               │
│  UI Kit: shadcn/ui + Tailwind                                              │
│  Голос: Web Speech API                                                     │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ REST API + WebSocket
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                         │
│                         FastAPI + Python 3.11                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API LAYER                                    │   │
│  │                                                                      │   │
│  │  CHAT                           DATA                                 │   │
│  │  POST /chat/message             GET  /projects                       │   │
│  │  POST /chat/action              GET  /projects/{id}/hierarchy        │   │
│  │  GET  /chat/history             GET  /cells                          │   │
│  │  WS   /chat/stream              POST /cells/batch-update             │   │
│  │                                                                      │   │
│  │  CALC                           REPORTS                              │   │
│  │  POST /calc/recalculate         GET  /reports/{type}                 │   │
│  │  POST /calc/distribute          GET  /export/pdf                     │   │
│  │  POST /calc/scenario            GET  /export/excel                   │   │
│  │                                                                      │   │
│  │  VERSIONS                       REALTIME                             │   │
│  │  GET  /versions                 WS   /events (факт из 1С)            │   │
│  │  POST /versions/create                                               │   │
│  │  GET  /versions/diff                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      AI ORCHESTRATOR                                 │   │
│  │                                                                      │   │
│  │  • Контекст сессии (проект, раздел, состояние визарда)              │   │
│  │  • State machine сценариев                                          │   │
│  │  • Парсинг намерений (NLU) через Claude API                         │   │
│  │  • Формирование ответа + кнопок                                     │   │
│  │  • Валидация данных                                                 │   │
│  │  • НЕ считает — только понимает и отвечает                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CALCULATION ENGINE                              │   │
│  │                                                                      │   │
│  │  • Граф зависимостей показателей                                    │   │
│  │  • Расчёт по формулам                                               │   │
│  │  • Расчёт по драйверам (% от другого показателя)                    │   │
│  │  • Распределение по периодам (алгоритмы)                            │   │
│  │  • Override логика (calc + override → final)                        │   │
│  │  • Агрегация (ЗУ → ПК → Проект)                                     │   │
│  │  • Сценарное моделирование (эластичность)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EXPORT ENGINE                                   │   │
│  │                                                                      │   │
│  │  • PDF: WeasyPrint (HTML → PDF)                                     │   │
│  │  • Excel: openpyxl                                                  │   │
│  │  • Шаблоны отчётов                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│     POSTGRESQL       │ │    CLAUDE API    │ │     1С ШЛЮЗ      │
│     (Supabase)       │ │                  │ │                  │
│                      │ │  • Sonnet (быстро)│ │  • Polling/webhook│
│  • Структура         │ │  • Opus (сложно) │ │  • Транзакции    │
│  • Данные            │ │  • Haiku (дёшево)│ │  • Договоры      │
│  • История           │ │                  │ │                  │
│  • Версии            │ │                  │ │                  │
│  • Алгоритмы         │ │                  │ │                  │
└──────────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 4. База данных

### 4.1. Справочники

```sql
-- Показатели
CREATE TABLE indicators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,       -- "00-01", "05-08"
    name            TEXT NOT NULL,              -- "Общая площадь"
    unit            TEXT,                       -- "м²", "руб", "%"
    section_code    TEXT NOT NULL,              -- "00", "01", "05"
    indicator_type  TEXT NOT NULL,              -- "input", "formula", "driver", "sum"
    formula         TEXT,                       -- "= {00-01} * {01-02}"
    driver_code     TEXT,                       -- код показателя-драйвера
    driver_pct      DECIMAL,                    -- процент от драйвера
    allow_override  BOOLEAN DEFAULT true,
    allow_distribution BOOLEAN DEFAULT true,
    sort_order      INT,
    created_at      TIMESTAMP DEFAULT now()
);

-- Граф зависимостей
CREATE TABLE indicator_deps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID REFERENCES indicators(id),
    target_id       UUID REFERENCES indicators(id),
    dep_type        TEXT NOT NULL               -- "formula", "driver"
);

-- Виды объектов недвижимости
CREATE TABLE von_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,       -- "КВАР", "АПАРТ", "РИТЕЙЛ"
    name            TEXT NOT NULL,
    category        TEXT                        -- "Жилая", "Коммерция", "Паркинг"
);

-- Разделы модели
CREATE TABLE form_sections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,       -- "00", "01", "05"
    name            TEXT NOT NULL,              -- "ТЭП", "Продажи", "СМР"
    sort_order      INT
);
```

### 4.2. Структура проекта

```sql
-- Проекты
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    region          TEXT,
    address         TEXT,
    status          TEXT DEFAULT 'active',      -- "active", "archived"
    created_by      UUID,
    created_at      TIMESTAMP DEFAULT now()
);

-- Продуктовые комплексы
CREATE TABLE pks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    code            TEXT NOT NULL,              -- "ПК-1"
    name            TEXT NOT NULL,              -- "Жилой"
    sort_order      INT
);

-- Земельные участки / Урбан-блоки
CREATE TABLE urban_blocks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pk_id           UUID REFERENCES pks(id) ON DELETE CASCADE,
    code            TEXT NOT NULL,              -- "ЗУ-1.1"
    name            TEXT,
    area            DECIMAL,                    -- площадь участка
    sort_order      INT
);

-- Индексы
CREATE INDEX idx_pks_project ON pks(project_id);
CREATE INDEX idx_ub_pk ON urban_blocks(pk_id);
```

### 4.3. Версии и данные

```sql
-- Версии модели
CREATE TABLE fm_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    version_number  INT NOT NULL,
    name            TEXT,                       -- "После торгов", "Антикризис"
    status          TEXT DEFAULT 'draft',       -- "draft", "review", "approved"
    parent_id       UUID REFERENCES fm_versions(id),
    is_scenario     BOOLEAN DEFAULT false,      -- true = сценарий, не основная
    scenario_params JSONB,                      -- параметры сценария
    created_by      UUID,
    created_at      TIMESTAMP DEFAULT now(),
    approved_by     UUID,
    approved_at     TIMESTAMP,
    
    UNIQUE(project_id, version_number)
);

-- Ячейки данных (главная таблица)
CREATE TABLE cell_values (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID REFERENCES fm_versions(id) ON DELETE CASCADE,
    indicator_id    UUID REFERENCES indicators(id),
    zu_id           UUID REFERENCES urban_blocks(id),    -- NULL = уровень проекта
    pk_id           UUID REFERENCES pks(id),             -- NULL = уровень проекта
    von_id          UUID REFERENCES von_types(id),       -- NULL = без разреза
    period          DATE,                                -- NULL = итого
    
    -- Трёхслойная ячейка
    calc_value      DECIMAL,                    -- расчётное значение
    override_value  DECIMAL,                    -- ручное (NULL = нет override)
    override_reason TEXT,
    override_by     UUID,
    override_at     TIMESTAMP,
    
    -- Служебные
    is_locked       BOOLEAN DEFAULT false,      -- защищена от перераспределения
    is_dirty        BOOLEAN DEFAULT false,      -- требует пересчёта
    updated_at      TIMESTAMP DEFAULT now()
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

-- Индексы
CREATE INDEX idx_cells_version ON cell_values(version_id);
CREATE INDEX idx_cells_indicator ON cell_values(indicator_id);
CREATE INDEX idx_cells_zu ON cell_values(zu_id);
CREATE INDEX idx_cells_period ON cell_values(period);
CREATE INDEX idx_cells_lookup ON cell_values(version_id, indicator_id, zu_id, period);

-- Журнал изменений (аудит)
CREATE TABLE cell_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id         UUID REFERENCES cell_values(id) ON DELETE CASCADE,
    version_id      UUID REFERENCES fm_versions(id),
    event_type      TEXT NOT NULL,              -- "create", "update", "override", "calc", "distribute"
    field_changed   TEXT,                       -- "calc_value", "override_value"
    old_value       DECIMAL,
    new_value       DECIMAL,
    user_id         UUID,
    comment         TEXT,
    created_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_events_cell ON cell_events(cell_id);
CREATE INDEX idx_events_version ON cell_events(version_id);
```

### 4.4. Алгоритмы распределения

```sql
-- Алгоритмы распределения
CREATE TABLE distribution_algorithms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,       -- "proportional", "uniform", "tail"
    name            TEXT NOT NULL,              -- "Пропорционально"
    description     TEXT,
    is_system       BOOLEAN DEFAULT false,      -- системный = нельзя удалить
    created_by      UUID,                       -- NULL для системных
    base_algorithm  TEXT,                       -- для кастомных: на основе какого
    modifiers       JSONB,                      -- правила модификации
    created_at      TIMESTAMP DEFAULT now()
);

-- Системные алгоритмы (seed)
INSERT INTO distribution_algorithms (code, name, description, is_system, modifiers) VALUES
('proportional', 'Пропорционально', 'Дельта распределяется пропорционально долям периодов', true, '{}'),
('uniform', 'Равномерно', 'Дельта делится поровну на все периоды', true, '{}'),
('tail', 'Всё на хвост', 'Вся дельта уходит в последний период', true, '{}'),
('scurve', 'S-кривая', 'Распределение по S-кривой (медленный старт, пик, замедление)', true, 
 '{"curve_type": "sigmoid", "peak_position": 0.6}');

-- Пользовательские настройки
CREATE TABLE user_preferences (
    user_id                 UUID PRIMARY KEY,
    default_algorithm_id    UUID REFERENCES distribution_algorithms(id),
    default_wave_algorithm  TEXT DEFAULT 'proportional',
    ui_mode                 TEXT DEFAULT 'chat',    -- "chat" или "spreadsheet"
    updated_at              TIMESTAMP DEFAULT now()
);
```

### 4.5. Чат и сессии

```sql
-- Сессии чата
CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id),
    user_id         UUID,
    wizard_type     TEXT,                       -- "new_project", "fact", "adjustment", "scenario"
    wizard_state    JSONB,                      -- текущее состояние визарда
    collected_data  JSONB,                      -- накопленные данные
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- Сообщения чата
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,              -- "user", "assistant", "system"
    content         TEXT NOT NULL,
    
    -- Дополнительные элементы сообщения
    buttons         JSONB,                      -- кнопки для ответа
    inline_table    JSONB,                      -- таблица внутри сообщения
    inline_chart    JSONB,                      -- график внутри сообщения
    
    -- Результат действия
    actions_taken   JSONB,                      -- что было сделано (сохранено в БД)
    
    -- Метаданные
    tokens_input    INT,
    tokens_output   INT,
    model_used      TEXT,                       -- "sonnet", "opus", "haiku"
    created_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
```

### 4.6. Интеграция с 1С

```sql
-- Транзакции из 1С
CREATE TABLE fact_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT UNIQUE,                -- ID из 1С
    
    -- Данные транзакции
    amount          DECIMAL NOT NULL,
    transaction_date DATE NOT NULL,
    counterparty    TEXT,
    contract_number TEXT,
    payment_purpose TEXT,
    
    -- Сырые данные
    raw_data        JSONB,
    
    -- Разнесение
    status          TEXT DEFAULT 'pending',     -- "pending", "matched", "deferred"
    project_id      UUID REFERENCES projects(id),
    matched_cell_id UUID REFERENCES cell_values(id),
    matched_by      UUID,
    matched_at      TIMESTAMP,
    match_comment   TEXT,
    
    created_at      TIMESTAMP DEFAULT now()
);

-- Договоры
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT,
    project_id      UUID REFERENCES projects(id),
    contract_number TEXT,
    counterparty    TEXT,
    subject         TEXT,
    amount          DECIMAL,
    
    -- Связь со статьёй бюджета
    indicator_id    UUID REFERENCES indicators(id),
    pk_id           UUID REFERENCES pks(id),
    zu_id           UUID REFERENCES urban_blocks(id),
    
    -- PDF и AI-анализ
    pdf_url         TEXT,
    ai_summary      TEXT,
    
    created_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_contracts_project ON contracts(project_id);
CREATE INDEX idx_contracts_number ON contracts(contract_number);
```

---

## 5. Расчётный движок

### 5.1. Типы показателей

| Тип | Описание | Пример |
|-----|----------|--------|
| `input` | Ручной ввод | Площадь участка |
| `formula` | Расчёт по формуле | Выручка = Площадь × Цена |
| `driver` | % от другого показателя | Маркетинг = 3% от Выручки |
| `sum` | Сумма дочерних | СМР итого = Σ этапов |

### 5.2. Граф зависимостей

```python
# При изменении показателя A:
# 1. Найти все показатели, зависящие от A
# 2. Топологическая сортировка
# 3. Пересчитать в правильном порядке

def recalculate(changed_indicator_id, version_id):
    # Получить граф зависимостей
    deps = get_dependency_graph(version_id)
    
    # Найти все затронутые показатели
    affected = find_affected(changed_indicator_id, deps)
    
    # Топологическая сортировка
    ordered = topological_sort(affected, deps)
    
    # Пересчитать каждый
    for indicator_id in ordered:
        calculate_indicator(indicator_id, version_id)
```

### 5.3. Override логика

```python
def get_final_value(cell):
    """
    Приоритет: override > calc
    """
    if cell.override_value is not None:
        return cell.override_value
    return cell.calc_value

def set_override(cell_id, value, reason, user_id):
    """
    Установить ручное значение
    """
    cell = get_cell(cell_id)
    
    # Сохранить override
    cell.override_value = value
    cell.override_reason = reason
    cell.override_by = user_id
    cell.override_at = now()
    
    # calc_value продолжает считаться!
    # При снятии override сразу видно актуальное calc
    
    # Записать в аудит
    log_event(cell_id, "override", cell.calc_value, value, user_id)
    
    # Пересчитать зависимые (они видят final_value)
    recalculate_dependents(cell.indicator_id)
```

### 5.4. Алгоритмы распределения

```python
def distribute(total, periods, algorithm, locked_periods=None):
    """
    Распределить итого по периодам
    
    locked_periods: dict {period: value} — защищённые периоды (override)
    """
    locked = locked_periods or {}
    locked_sum = sum(locked.values())
    remaining = total - locked_sum
    
    # Периоды без override
    free_periods = [p for p in periods if p not in locked]
    
    if algorithm == 'proportional':
        # Пропорционально (по умолчанию)
        base_values = get_base_distribution(free_periods)  # из шаблона
        base_sum = sum(base_values.values())
        
        result = {}
        for period in periods:
            if period in locked:
                result[period] = locked[period]
            else:
                share = base_values[period] / base_sum
                result[period] = remaining * share
                
    elif algorithm == 'uniform':
        # Равномерно
        per_period = remaining / len(free_periods)
        result = {p: per_period for p in free_periods}
        result.update(locked)
        
    elif algorithm == 'tail':
        # Всё на хвост
        result = {p: 0 for p in free_periods[:-1]}
        result[free_periods[-1]] = remaining
        result.update(locked)
        
    elif algorithm == 'scurve':
        # S-кривая
        result = generate_scurve(free_periods, remaining)
        result.update(locked)
    
    return result


def apply_wave(old_distribution, changed_period, new_value, algorithm='proportional'):
    """
    Применить волну перераспределения после изменения одного периода
    """
    total = sum(old_distribution.values())
    delta = old_distribution[changed_period] - new_value
    
    # Новое распределение
    new_distribution = old_distribution.copy()
    new_distribution[changed_period] = new_value  # override
    
    # Остальные периоды
    other_periods = [p for p in old_distribution if p != changed_period]
    other_sum = sum(old_distribution[p] for p in other_periods)
    
    if algorithm == 'proportional':
        # Формула: новое = старое × (1 + дельта / остаток)
        multiplier = 1 + (delta / other_sum) if other_sum > 0 else 1
        for period in other_periods:
            new_distribution[period] = old_distribution[period] * multiplier
            
    elif algorithm == 'uniform':
        # Дельта поровну
        delta_per_period = delta / len(other_periods)
        for period in other_periods:
            new_distribution[period] = old_distribution[period] + delta_per_period
            
    elif algorithm == 'tail':
        # Вся дельта на последний
        last_period = max(other_periods)
        new_distribution[last_period] = old_distribution[last_period] + delta
    
    return new_distribution
```

### 5.5. Эластичность спроса

```python
def apply_price_elasticity(base_scenario, price_change_pct, elasticity):
    """
    Рассчитать влияние изменения цен на объём продаж
    
    elasticity: коэффициент эластичности (0.3 - 1.5)
    Пример: elasticity=0.7, price_change=+15% → volume_change=-10.5%
    """
    volume_change_pct = -price_change_pct * elasticity
    
    new_scenario = base_scenario.copy()
    
    # Цена
    new_scenario['price'] = base_scenario['price'] * (1 + price_change_pct / 100)
    
    # Объём
    new_scenario['volume'] = base_scenario['volume'] * (1 + volume_change_pct / 100)
    
    # Выручка
    new_scenario['revenue'] = new_scenario['price'] * new_scenario['volume']
    
    return new_scenario
```

### 5.6. Агрегация

```python
def aggregate_zu_to_pk(version_id, indicator_id):
    """
    Суммировать значения ЗУ на уровень ПК
    """
    for pk in get_pks(version_id):
        zu_values = get_cells(
            version_id=version_id,
            indicator_id=indicator_id,
            pk_id=pk.id
        )
        
        pk_total = sum(cell.final_value for cell in zu_values)
        
        set_calc_value(
            version_id=version_id,
            indicator_id=indicator_id,
            pk_id=pk.id,
            zu_id=None,  # уровень ПК
            value=pk_total
        )


def aggregate_pk_to_project(version_id, indicator_id):
    """
    Суммировать значения ПК на уровень проекта
    """
    pk_values = get_cells(
        version_id=version_id,
        indicator_id=indicator_id,
        zu_id=None,
        pk_id__isnull=False
    )
    
    project_total = sum(cell.final_value for cell in pk_values)
    
    set_calc_value(
        version_id=version_id,
        indicator_id=indicator_id,
        pk_id=None,
        zu_id=None,  # уровень проекта
        value=project_total
    )
```

---

## 6. AI Orchestrator

### 6.1. Сценарии (State Machine)

```python
WIZARD_SCENARIOS = {
    "new_project": {
        "states": [
            "ask_name",
            "ask_region", 
            "ask_pk_count",
            "ask_pk_names",
            "ask_zu_count",
            "confirm_structure",
            "ask_total_area",
            "ask_area_distribution",
            "ask_von_types",
            "ask_lf",
            "confirm_tep",
            "ask_timeline",
            "confirm_timeline",
            "ask_prices",
            "ask_price_growth",
            "ask_sales_curve",
            "confirm_sales",
            "ask_land_cost",
            "ask_construction_cost",
            "ask_commercial_costs",
            "confirm_costs",
            "ask_financing",
            "confirm_financing",
            "show_summary",
            "save_version"
        ]
    },
    
    "fact_processing": {
        "states": [
            "new_transaction",
            "identify_contract",
            "confirm_allocation",
            "check_budget",
            "handle_overrun",
            "commit_fact"
        ]
    },
    
    "plan_adjustment": {
        "states": [
            "identify_change",
            "ask_adjustment_type",  # экономия / перенос / ручное
            "configure_redistribution",
            "preview_changes",
            "confirm_changes"
        ]
    },
    
    "scenario_modeling": {
        "states": [
            "ask_scenario_type",
            "ask_parameters",
            "ask_elasticity",      # для ценовых сценариев
            "calculate_scenario",
            "show_comparison",
            "ask_compensation",    # варианты компенсации
            "save_scenario"
        ]
    }
}
```

### 6.2. Формат сообщений

```python
# Ответ AI Orchestrator
{
    "message": "Какой коэффициент эластичности применить?",
    
    "hint": "Эластичность показывает, на сколько % упадут продажи при росте цены на 1%",
    
    "buttons": [
        {"id": "e03", "label": "0.3 низкая", "value": 0.3},
        {"id": "e05", "label": "0.5 средняя", "value": 0.5},
        {"id": "e07", "label": "0.7 рыночная", "value": 0.7},
        {"id": "e10", "label": "1.0 высокая", "value": 1.0},
        {"id": "custom", "label": "Ввести", "type": "input"}
    ],
    
    "inline_table": null,
    "inline_chart": null,
    
    "next_state": "calculate_scenario",
    "save_data": null
}

# После расчёта сценария
{
    "message": "Сценарий \"Цены +15%, эластичность 0.7\":",
    
    "inline_table": {
        "title": "Сравнение",
        "columns": ["Показатель", "Текущий", "Сценарий", "Δ"],
        "rows": [
            ["Цена м²", "180 000", "207 000", "+15%"],
            ["Объём продаж", "32 800 м²", "29 356 м²", "−10.5%"],
            ["Выручка", "6.35 млрд", "6.08 млрд", "−4.3%"],
            ["Маржа", "2.2 млрд", "1.9 млрд", "−14%"]
        ]
    },
    
    "inline_chart": {
        "type": "bar",
        "library": "recharts",
        "data": [
            {"name": "Текущий", "revenue": 6.35, "margin": 2.2},
            {"name": "Сценарий", "revenue": 6.08, "margin": 1.9}
        ]
    },
    
    "buttons": [
        {"id": "optimize", "label": "Найти оптимум"},
        {"id": "compensate", "label": "Как компенсировать?"},
        {"id": "save", "label": "Сохранить сценарий"}
    ]
}
```

### 6.3. Паттерн кнопок

```python
# Везде где нужен ввод параметра:
# [Шаблон 1] [Шаблон 2] [Шаблон 3] [Шаблон 4] [____]

BUTTON_TEMPLATES = {
    "elasticity": [
        {"label": "0.3", "value": 0.3, "hint": "низкая"},
        {"label": "0.5", "value": 0.5, "hint": "средняя"},
        {"label": "0.7", "value": 0.7, "hint": "рыночная"},
        {"label": "1.0", "value": 1.0, "hint": "высокая"},
        {"type": "input", "label": "Ввести"}
    ],
    
    "price_change": [
        {"label": "+5%", "value": 5},
        {"label": "+10%", "value": 10},
        {"label": "+15%", "value": 15},
        {"label": "−10%", "value": -10},
        {"type": "input", "label": "Ввести"}
    ],
    
    "lf_percent": [
        {"label": "80%", "value": 80},
        {"label": "82%", "value": 82},
        {"label": "85%", "value": 85},
        {"type": "input", "label": "Ввести"}
    ],
    
    "distribution": [
        {"label": "Равномерно", "value": "uniform"},
        {"label": "S-кривая", "value": "scurve"},
        {"label": "По драйверу", "value": "by_driver"},
        {"label": "Вручную", "value": "manual"}
    ]
}
```

---

## 7. Модальное окно распределения

### 7.1. Структура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Распределение: [Название показателя]                                 [×]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ИТОГО: [значение]                    Период: [начало] — [конец]           │
│                                                                             │
├──────────────────────────────────────────────┬──────────────────────────────┤
│                                              │                              │
│  ПОЛЗУНКИ                                    │  АЛГОРИТМ ВОЛНЫ             │
│  (интерактивные, двусторонняя связь)         │                              │
│                                              │  ● Пропорционально          │
│  период 1  ████████░░░░░░░░░░  XX%          │  ○ Равномерно               │
│  период 2  ██████░░░░░░░░░░░░  XX%          │  ○ Всё на хвост             │
│  ...                                         │  ○ [Кастомный] ⭐            │
│                                              │                              │
│                              ─────           │  [+ Создать свой]           │
│                              100%            │  [⚙ Мой по умолчанию]       │
│                                              │                              │
├──────────────────────────────────────────────┴──────────────────────────────┤
│                                                                             │
│  ТАБЛИЦА (editable)                                                        │
│  ┌────────┬───────────┬───────────┬──────────┬────────┬──────────────────┐ │
│  │ Период │ Шаблон    │ Значение  │ %        │ Статус │ Δ от шаблона    │ │
│  ├────────┼───────────┼───────────┼──────────┼────────┼──────────────────┤ │
│  │ ...    │           │ [edit]    │          │ ✎/↻/═  │                 │ │
│  └────────┴───────────┴───────────┴──────────┴────────┴──────────────────┘ │
│                                                                             │
│  Легенда: ✎ override, ↻ пересчитано волной, ═ шаблон                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Сбросить к шаблону]                      [Отмена]  [✓ Применить]         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2. Поведение

| Действие | Реакция |
|----------|---------|
| Двинул ползунок | Таблица обновляется, волна по алгоритму, анимация |
| Изменил ячейку | Ползунок двигается, волна по алгоритму |
| Сменил алгоритм | Все не-override значения пересчитываются |
| Override ячейка | Защищена от волны, помечена ✎ |
| Итого | Всегда = исходному, система балансирует |

### 7.3. Кастомные алгоритмы

```python
# Структура кастомного алгоритма
{
    "name": "Бобик's алгоритм",
    "base": "proportional",
    "modifiers": {
        "protect_first": 3,       # не трогать первые N периодов
        "protect_last": 0,        # не трогать последние N периодов
        "peak_multiplier": 1.5,   # множитель для периода-пика
        "tail_multiplier": 0.7,   # множитель для хвоста
        "tail_periods": 2,        # сколько периодов считать хвостом
        "max_per_period": 0.25,   # лимит на период (доля от итого)
        "min_per_period": 0.01    # минимум на период
    }
}
```

---

## 8. Дорожная карта

### Фаза 1: MVP чат-визард (6 недель)

```
НЕДЕЛЯ 1-2: Фундамент
├── День 1-2: Инфраструктура
│   ├── Supabase: создать проект, схема БД
│   ├── FastAPI: scaffold, деплой на Railway
│   ├── React: create-react-app, деплой на Vercel
│   └── Связать всё, проверить
│
├── День 3-4: База данных
│   ├── Все таблицы из раздела 4
│   ├── Seed справочников (indicators, von_types)
│   ├── Тестовый проект с данными
│   └── View cells_final
│
├── День 5-7: API структуры
│   ├── CRUD projects, pks, urban_blocks
│   ├── GET /projects/{id}/hierarchy
│   ├── Версии: create, list
│   └── Тесты

НЕДЕЛЯ 3-4: Чат-интерфейс
├── День 8-10: Chat UI
│   ├── Компонент чата (сообщения, ввод)
│   ├── Кнопки внутри сообщений
│   ├── Inline-таблицы (простые)
│   └── POST /chat/message, /chat/action
│
├── День 11-12: AI Orchestrator (базовый)
│   ├── Claude API интеграция
│   ├── State machine для new_project
│   ├── Парсинг ответов, формирование кнопок
│   └── Контекст сессии
│
├── День 13-14: Визард создания модели
│   ├── Все шаги: структура → ТЭП → сроки → доходы → расходы
│   ├── Сохранение в БД при подтверждении
│   └── Итоговая сводка

НЕДЕЛЯ 5-6: Расчёты и графики
├── День 15-17: Расчётный движок
│   ├── Формулы и драйверы
│   ├── Граф зависимостей
│   ├── Распределение по периодам (базовое)
│   └── POST /calc/recalculate, /calc/distribute
│
├── День 18-19: Графики в чате
│   ├── Recharts интеграция
│   ├── Cash Flow график
│   ├── Структура расходов (pie)
│   └── Сравнение (bar)
│
├── День 20-21: Полировка MVP
│   ├── Версионность (создать, выбрать)
│   ├── Экспорт PDF (базовый)
│   ├── История чата
│   └── Тестирование на реальных данных
```

### Фаза 2: Таблицы + распределения (4 недели)

```
НЕДЕЛЯ 7-8: Табличный интерфейс
├── AG Grid интеграция
├── Формы по разделам (ТЭП, Продажи, Расходы)
├── Навигация (дерево ПК/ЗУ)
├── Переключатель Чат/Таблицы
└── Мини-чат из таблиц (🤖 кнопка)

НЕДЕЛЯ 9-10: Модалка распределений
├── Ползунки + таблица (двусторонняя связь)
├── Алгоритмы волны (3 системных)
├── Кастомные алгоритмы (создание, сохранение)
├── Анимация перераспределения
└── Override логика
```

### Фаза 3: Факт и сценарии (4 недели)

```
НЕДЕЛЯ 11-12: Интеграция 1С
├── Шлюз (polling / webhook)
├── WebSocket уведомления
├── Визард разнесения факта
├── Проверка лимитов
└── Накопительная ведомость

НЕДЕЛЯ 13-14: Сценарное моделирование
├── Визард сценариев
├── Эластичность спроса
├── Сравнение версий
├── Отправка отчётов (Telegram, email)
└── Расширенные отчёты
```

### Фаза 4: Продакшен (2 недели)

```
НЕДЕЛЯ 15-16: Production-ready
├── Авторизация (Supabase Auth)
├── Роли (admin, analyst, viewer)
├── Оптимизация (кэш, батчинг)
├── Мониторинг (Sentry, логи)
├── Мобильная адаптация
└── Документация
```

**Итого: 16 недель (4 месяца) до полного продукта**

**MVP (демо-готовый): 6 недель**

---

## 9. Стек технологий

| Слой | Технология | Почему |
|------|------------|--------|
| **Frontend** | React 18 + TypeScript | Стандарт, экосистема |
| UI Kit | shadcn/ui + Tailwind | Быстро, красиво, кастомизируемо |
| Таблицы | AG Grid Enterprise | Лучший для финансовых данных |
| Графики | Recharts + ECharts | Recharts — простые, ECharts — сложные |
| State | Zustand | Проще Redux, достаточно мощный |
| **Backend** | FastAPI + Python 3.11 | Async, типизация, быстрый |
| ORM | SQLAlchemy 2.0 | Async, миграции через Alembic |
| Валидация | Pydantic v2 | Встроена в FastAPI |
| **AI** | Claude API | Sonnet — быстро, Opus — сложно, Haiku — дёшево |
| **БД** | PostgreSQL 15 (Supabase) | Бесплатно до определённого объёма |
| **Realtime** | WebSocket (FastAPI) | Для факта из 1С |
| **Export** | WeasyPrint (PDF), openpyxl (Excel) | Проверенные библиотеки |
| **Деплой** | Vercel (front) + Railway (back) | Просто, дёшево, масштабируемо |

---

## 10. Стоимость инфраструктуры

### MVP (до 100 пользователей)

| Сервис | План | Цена/мес |
|--------|------|----------|
| Supabase | Free | $0 |
| Railway | Starter | $5-20 |
| Vercel | Pro | $20 |
| Claude API | Pay-as-you-go | $50-200 |
| AG Grid | Enterprise (1 dev) | $83 ($999/год) |
| **Итого** | | **$160-320/мес** |

### Рост (100-1000 пользователей)

| Сервис | План | Цена/мес |
|--------|------|----------|
| Supabase | Pro | $25 |
| Railway | Pro | $50-100 |
| Vercel | Pro | $20 |
| Claude API | | $500-2000 |
| AG Grid | Enterprise (team) | $200+ |
| **Итого** | | **$800-2500/мес** |

### Оптимизация Claude API

- **Haiku** для простых задач (парсинг чисел) — в 10 раз дешевле
- **Кэширование** повторяющихся запросов
- **Короткие промпты** — меньше токенов
- **Батчинг** — один вызов вместо нескольких

---

## 11. Критерии готовности

### MVP (6 недель)
- [ ] Создание модели через чат-визард (полный цикл)
- [ ] Сохранение в БД, версионность
- [ ] Базовые расчёты (формулы, драйверы)
- [ ] Графики в чате (Cash Flow, структура)
- [ ] Экспорт PDF
- [ ] Один реальный проект загружен и работает

### Полный продукт (16 недель)
- [ ] Табличный интерфейс с AG Grid
- [ ] Переключение Чат/Таблицы
- [ ] Модалка распределений (ползунки, волна, кастомные алгоритмы)
- [ ] Интеграция с 1С (факт)
- [ ] Сценарное моделирование с эластичностью
- [ ] Авторизация и роли
- [ ] Мобильная версия

---

## 12. Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Claude неправильно парсит ввод | Средняя | Валидация в Python, переспрос "я понял X — верно?" |
| Дорогой API | Высокая | Haiku для простого, кэш, лимиты |
| AG Grid сложный | Средняя | Документация хорошая, есть примеры |
| 1С интеграция нестандартная | Высокая | Начать с простого polling, унифицировать формат |
| Финансисты не примут чат | Средняя | Гибридный режим, можно работать только в таблицах |

---

## 13. Первые шаги

```bash
# 1. Создать репозиторий
git init fm-ai
cd fm-ai

# 2. Структура проекта
mkdir -p backend/app/{api,core,models,services}
mkdir -p backend/app/services/{chat,calc,export}
mkdir -p frontend/src/{components,pages,hooks,stores}

# 3. Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy asyncpg pydantic anthropic

# 4. Frontend setup
cd ../frontend
npx create-next-app@latest . --typescript --tailwind
npm install @tanstack/react-query zustand recharts

# 5. Supabase
# Создать проект на supabase.com
# Скопировать connection string

# 6. Запуск
# Backend: uvicorn app.main:app --reload
# Frontend: npm run dev
```

---

## 14. Дизайн-система

### 14.1. Референс стиля

Ориентируемся на стиль приложения MR Agent (agent.superapp.site) — тёмная тема с акцентами amber/orange.

```
Основные цвета:
├── Background: #1a1a1a / #0d0d0d (основной фон)
├── Surface: #2a2a2a / #1e1e1e (карточки, модалки)
├── Border: #3a3a3a / rgba(255,255,255,0.1)
├── Text primary: #ffffff / #f5f5f5
├── Text secondary: #a0a0a0 / #888888
├── Accent primary: #f59e0b (amber-500) — кнопки, ссылки, активные
├── Accent hover: #d97706 (amber-600)
├── Accent glow: rgba(245, 158, 11, 0.3) — подсветка
├── Success: #22c55e (green-500)
├── Warning: #eab308 (yellow-500)
├── Error: #ef4444 (red-500)
└── Info: #3b82f6 (blue-500)
```

### 14.2. Компоненты

```
Кнопки:
├── Primary: bg-amber-500, hover:bg-amber-600, rounded-lg
├── Secondary: border border-amber-500, text-amber-500, bg-transparent
├── Ghost: text-gray-400, hover:text-white, hover:bg-white/5
└── Icon: rounded-full, p-2, hover:bg-white/10

Карточки:
├── bg-[#1e1e1e], border border-[#3a3a3a], rounded-xl
├── Hover: border-amber-500/30, shadow-amber-500/10
└── Active: border-amber-500

Инпуты:
├── bg-[#2a2a2a], border border-[#3a3a3a], rounded-lg
├── Focus: border-amber-500, ring-1 ring-amber-500/50
└── Placeholder: text-gray-500

Чат:
├── User message: bg-amber-500/10, border-l-2 border-amber-500
├── Assistant message: bg-[#1e1e1e], border-l-2 border-gray-600
└── System message: bg-blue-500/10, text-blue-400
```

### 14.3. Типографика

```
Шрифты:
├── Sans: Inter / system-ui (основной)
├── Mono: JetBrains Mono / monospace (таблицы, числа)
└── Display: Inter (заголовки, жирнее)

Размеры:
├── xs: 0.75rem / 12px
├── sm: 0.875rem / 14px
├── base: 1rem / 16px
├── lg: 1.125rem / 18px
├── xl: 1.25rem / 20px
├── 2xl: 1.5rem / 24px
└── 3xl: 1.875rem / 30px
```

---

## 15. AI Ассистент — настройки

### 15.1. Хранение API ключей (десктоп)

```
Локальное хранение:
├── SQLite или encrypted JSON на диске пользователя
├── Путь: ~/.fm-assistant/config.enc
├── Шифрование: AES-256 с ключом из machine ID
└── Ввод один раз — хранится навсегда

Настройки в UI:
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ Настройки AI ассистента                            [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Claude API                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ sk-ant-api03-***************************           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ✓ Ключ сохранён                    [Проверить] [Удалить]  │
│                                                             │
│  Модель по умолчанию                                        │
│  ○ Claude Sonnet (быстро, дешевле)                         │
│  ● Claude Opus (умнее, для сложного)                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ElevenLabs API (голос)                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ **************************************              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ✓ Ключ сохранён                    [Проверить] [Удалить]  │
│                                                             │
│  Голос ассистента                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Савелий (мужской, деловой)                       ▼  │  │
│  └──────────────────────────────────────────────────────┘  │
│  [▶ Прослушать]                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 15.2. Контекст пользователя

Перед демонстрацией или работой — можно добавить контекст о собеседнике:

```
┌─────────────────────────────────────────────────────────────┐
│  👤 Контекст общения                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Имя пользователя: [Катя____________________________]      │
│                                                             │
│  Дополнительный контекст:                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Катя — финансовый директор. Любит краткие ответы   │   │
│  │ с таблицами. Предпочитает видеть ключевые цифры:   │   │
│  │ IRR, NPV, маржа, наполнение эскроу. Знает все      │   │
│  │ проекты, не нужно объяснять базовые вещи.          │   │
│  │                                                     │   │
│  │ Любимая табличка: ФЭП проекта (выручка, себест.,   │   │
│  │ маржа, IRR, NPV, срок окупаемости)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Этот контекст добавляется в system prompt и сохраняется   │
│  для последующих сессий.                                    │
│                                                             │
│                            [Очистить] [Сохранить]          │
└─────────────────────────────────────────────────────────────┘
```

System prompt с контекстом:
```python
SYSTEM_PROMPT = f"""
Ты — AI финансовый ассистент для девелоперской компании.
Текущий пользователь: {user_context.name}

Контекст о пользователе:
{user_context.additional_context}

Обращайся к пользователю по имени. Учитывай предпочтения.
Любимые форматы пользователя: {user_context.favorite_presets}
"""
```

### 15.3. Голосовые настройки

```
┌─────────────────────────────────────────────────────────────┐
│  🎙️ Голосовое управление                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Режим ввода                                                │
│  ┌───────────────────────┐ ┌───────────────────────┐       │
│  │  🎤 Микрофон ВКЛ      │ │  ⌨️ Только текст      │       │
│  │  (нажмите для откл.)  │ │                       │       │
│  └───────────────────────┘ └───────────────────────┘       │
│                                                             │
│  Режим ответа                                               │
│  ● Текст + голос (ассистент озвучивает ответы)             │
│  ○ Только текст (тихий режим)                              │
│                                                             │
│  Горячая клавиша для микрофона: [Space_________] [Изменить]│
│                                                             │
│  Wake word: "Савелий" / "Финансист" / [кастомный]          │
│  ┌────────────────────────────────────────────────────────┐│
│  │ ● Савелий (по умолчанию)                               ││
│  │ ○ Финансист                                            ││
│  │ ○ [Свой вариант: ____________________]                 ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 15.4. Архитектура голоса

```python
# Голосовой пайплайн
class VoiceAssistant:
    def __init__(self, config: AssistantConfig):
        self.stt = WebSpeechAPI()         # Speech-to-Text (браузер)
        self.llm = ClaudeAPI(config.api_key)
        self.tts = ElevenLabsAPI(config.elevenlabs_key, config.voice_id)

    async def process_voice(self, audio_stream):
        # 1. Распознать речь
        text = await self.stt.transcribe(audio_stream)

        # 2. Отправить в Claude
        response = await self.llm.chat(
            text,
            system=self.build_system_prompt()
        )

        # 3. Озвучить ответ (если включено)
        if self.config.voice_response_enabled:
            audio = await self.tts.synthesize(response.text)
            await self.play_audio(audio)

        return response
```

---

## 16. Демо-сценарии для презентации

### 16.1. Стартовое окно

При запуске приложения — приветственный попап:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    🏗️ FM AI Assistant                       │
│                                                             │
│           Умная операционная финансовая модель              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Привет! 👋                                                 │
│                                                             │
│  Я — твой AI финансовый ассистент.                         │
│  Могу помочь с:                                             │
│                                                             │
│  📊  Создать финмодель голосом за 10 минут                 │
│  📥  Разнести факт из 1С по проектам                       │
│  ✏️  Скорректировать план с перераспределением              │
│  📈  Рассчитать сценарии и сравнить варианты               │
│  📋  Проверить ковенанты и лимиты                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        [🎤 Начать голосом]  [⌨️ Написать]           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  или выбери действие:                                       │
│                                                             │
│  [+ Новый проект]  [📥 Ждёт разнесения: 3]  [📊 Дашборд]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 16.2. Сценарий 1: Разнесение факта из 1С/Tessa

```
┌─────────────────────────────────────────────────────────────┐
│  📥 Новые документы                                    [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔔 Катя, привет! Тут пришла первичка — факт.              │
│     Давай разнесём?                                         │
│                                                             │
│     [Давай]  [Позже]  [Показать все (3)]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

После "Давай":

┌─────────────────────────────────────────────────────────────┐
│  AI: Слушай, тут договор на услуги по дизайну офиса        │
│      продаж для проекта Касаткина.                         │
│                                                             │
│      📄 Платёжное поручение #1247                          │
│      💰 3 000 000 ₽                                         │
│      📅 21.01.2026                                          │
│      🏢 ООО "Дизайн Студио"                                │
│                                                             │
│      Предлагаю разнести так:                                │
│                                                             │
│      ┌────────────────────────────────────────────────┐    │
│      │ Проект:    Касаткина                           │    │
│      │ Очереди:   1 и 2 (пропорционально метрам)      │    │
│      │ Статья:    Коммерческие → Маркетинг →          │    │
│      │            Офис продаж                         │    │
│      └────────────────────────────────────────────────┘    │
│                                                             │
│      Норм?                                                  │
│                                                             │
│      [✓ Да, разноси]  [Изменить статью]  [Другой проект]   │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

Катя: "А сколько уже по этой статье потрачено?"

┌─────────────────────────────────────────────────────────────┐
│  AI: Смотри, вот раскладка по бюджету:                     │
│                                                             │
│  ┌─────────────────┬──────────┬──────────┬────────────────┐│
│  │ Статья          │ Бюджет   │ Факт     │ Остаток        ││
│  ├─────────────────┼──────────┼──────────┼────────────────┤│
│  │ Коммерческие    │ 100 млн  │ 15 млн   │ 85 млн (85%)   ││
│  │ └─ Маркетинг    │  50 млн  │  6 млн   │ 44 млн (88%)   ││
│  │    └─ Офис прод │  30 млн  │  4 млн   │ 26 млн → 23 млн││
│  └─────────────────┴──────────┴──────────┴────────────────┘│
│                                                             │
│  С этим платежом по офису продаж будет 7 млн факт.         │
│  Платёж в бюджете, превышения нет. ✅                       │
│                                                             │
│  Вносим в накопительную?                                    │
│                                                             │
│  [✓ Да, вноси]  [Подробнее по статье]                      │
└─────────────────────────────────────────────────────────────┘
```

### 16.3. Сценарий 2: Корректировка плана (волна)

```
Катя: "По Касаткина мы решили с генподрядчиком, что стартовый
       аванс по СМР будет не 15% — 750 млн, а 10% — 500 млн"

┌─────────────────────────────────────────────────────────────┐
│  AI: Ок, понял. Корректируем аванс СМР по Касаткина:       │
│                                                             │
│      Было:  750 млн (15% от 5 млрд)                        │
│      Стало: 500 млн (10% от 5 млрд)                        │
│      Дельта: −250 млн                                       │
│                                                             │
│      Как распределить дельту по оставшимся периодам?        │
│                                                             │
│      [Равномерно]  [Пропорционально]  [В конец]  [Вручную] │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

Катя: "Давай равномерно, а там видно будет"

┌─────────────────────────────────────────────────────────────┐
│  AI: Ок, смотри — строка СМР с генподрядчиком:             │
│                                                             │
│  ╔═══════════════════════════════════════════════════════╗ │
│  ║  [Анимированная таблица волны — как в wave.html]      ║ │
│  ║                                                        ║ │
│  ║  Период   │ Было     │ Стало    │ Δ                   ║ │
│  ║  ─────────┼──────────┼──────────┼─────────────────────║ │
│  ║  1 кв 26  │ 750 млн  │ 500 млн  │ −250 млн (ручное)  ║ │
│  ║  2 кв 26  │ 400 млн  │ 462 млн  │ +62 млн  ~~~>      ║ │
│  ║  3 кв 26  │ 600 млн  │ 662 млн  │ +62 млн  ~~~>      ║ │
│  ║  4 кв 26  │ 800 млн  │ 862 млн  │ +62 млн  ~~~>      ║ │
│  ║  1 кв 27  │ 700 млн  │ 764 млн  │ +64 млн  ~~~>      ║ │
│  ║  ─────────┼──────────┼──────────┼─────────────────────║ │
│  ║  ИТОГО    │ 5 000 млн│ 5 000 млн│ 0                   ║ │
│  ╚═══════════════════════════════════════════════════════╝ │
│                                                             │
│  Больше ничего не правим?                                   │
│  Отправляем на коммит эту версию в базу?                   │
│                                                             │
│  [✓ Да, сохраняй]  [Ещё корректировки]  [Отмена]           │
└─────────────────────────────────────────────────────────────┘
```

### 16.4. Сценарий 3: Аналитика с пресетом

```
Катя: "Покажи мне по Тушино только 2 и 3 очередь.
       Основные показатели, ну ты знаешь, как я люблю табличку"

┌─────────────────────────────────────────────────────────────┐
│  AI: Да, конечно! Твоя любимая табличка по ФЭП 😊          │
│                                                             │
│  📊 Тушино — очереди 2 и 3                                 │
│                                                             │
│  ┌─────────────────────┬─────────────┬─────────────┐       │
│  │ Показатель          │ Очередь 2   │ Очередь 3   │       │
│  ├─────────────────────┼─────────────┼─────────────┤       │
│  │ Продаваемая площадь │ 28 500 м²   │ 34 200 м²   │       │
│  │ Выручка             │ 5.7 млрд    │ 6.8 млрд    │       │
│  │ Себестоимость       │ 4.1 млрд    │ 4.9 млрд    │       │
│  │ Валовая маржа       │ 1.6 млрд    │ 1.9 млрд    │       │
│  │ Маржинальность      │ 28%         │ 28%         │       │
│  │ IRR                 │ 24%         │ 22%         │       │
│  │ NPV (15%)           │ 890 млн     │ 1.1 млрд    │       │
│  │ Срок окупаемости    │ 2.1 года    │ 2.4 года    │       │
│  └─────────────────────┴─────────────┴─────────────┘       │
│                                                             │
│  [📄 В PDF]  [📊 Подробнее]  [Сравнить со входом]          │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

Катя: "Можешь в потоки по земле поставить строчку —
       покупка проекта сторонним инвестором.
       Поставь 2 млрд и посмотрим какие станут показатели"

┌─────────────────────────────────────────────────────────────┐
│  AI: Добавил строку "Покупка инвестором" — 2 млрд ₽        │
│      Пересчитал модель. Смотри результат:                  │
│                                                             │
│  ┌─────────────────────┬─────────────┬─────────────┐       │
│  │ Показатель          │ Было        │ С инвестором│       │
│  ├─────────────────────┼─────────────┼─────────────┤       │
│  │ IRR проекта         │ 24%         │ 38%         │       │
│  │ NPV для продавца    │ 1.9 млрд    │ 3.4 млрд    │       │
│  │ IRR для покупателя  │ —           │ 24%         │       │
│  │ NPV для покупателя  │ —           │ 1.9 млрд    │       │
│  │ Чистая прибыль      │ 3.5 млрд    │ 3.7 млрд *  │       │
│  └─────────────────────┴─────────────┴─────────────┘       │
│  * с учётом выхода в 2 млрд                                 │
│                                                             │
│  При продаже за 2 млрд единоразово — для покупателя        │
│  IRR 24%, NPV 1.9 млрд. Сделка выгодна обеим сторонам.     │
│                                                             │
│  [📄 Сохранить в PDF]  [Кинуть в чат]  [Новый расчёт]      │
└─────────────────────────────────────────────────────────────┘
```

### 16.5. Сценарий 4: Проверка ковенантов

```
Катя: "Покажи по проспекту Мира какие сейчас ковенанты
       в красной или жёлтой зоне"

┌─────────────────────────────────────────────────────────────┐
│  AI: Катя, лови отчёт по ковенантам:                       │
│                                                             │
│  🏗️ Проспект Мира — статус ковенантов                      │
│                                                             │
│  ┌───────────────┬────────────┬────────────┬──────┬───────┐│
│  │ Ковенант      │ Банк.модель│ Факт/Прогн │ Δ    │Статус ││
│  ├───────────────┼────────────┼────────────┼──────┼───────┤│
│  │ Цена продажи  │ 550 т.р/м² │ 545 т.р/м² │ −5   │ 🟡    ││
│  │ Темп продаж   │ 2.2 млрд   │ 1.9 млрд * │ −0.3 │ 🟡    ││
│  │ СМР выполн.   │ 45%        │ 47%        │ +2%  │ 🟢    ││
│  │ Сроки ввода   │ 4 кв 2027  │ 4 кв 2027  │ 0    │ 🟢    ││
│  └───────────────┴────────────┴────────────┴──────┴───────┘│
│  * прогноз на следующий квартал                            │
│                                                             │
│  ⚠️ По ценам: банк ждёт 550 т.р., факт 545 т.р.            │
│     В пределах допуска (−2%), но на грани.                 │
│                                                             │
│  ⚠️ По темпам: план 2.2 млрд на эскроу, прогноз 1.9 млрд   │
│     Отставание 14%, требует внимания.                      │
│                                                             │
│  [Подробнее по ценам]  [План продаж]  [История ковенантов] │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

Катя: "А какое сейчас наполнение эскроу?"

┌─────────────────────────────────────────────────────────────┐
│  AI: Вот текущее состояние эскроу:                         │
│                                                             │
│  📊 Эскроу по проспекту Мира (на 01.01.2026)               │
│                                                             │
│  ┌─────────────────────────┬───────────────┐               │
│  │ Показатель              │ Значение      │               │
│  ├─────────────────────────┼───────────────┤               │
│  │ Остаток на эскроу       │ 1.5 млрд      │               │
│  │ Выборка ПФ              │ 2.1 млрд      │               │
│  │ Наполнение эскроу       │ 71%           │               │
│  │ Ковенант (мин.)         │ 70%           │               │
│  │ Запас                   │ +1%           │               │
│  └─────────────────────────┴───────────────┘               │
│                                                             │
│  ✅ Наполнение 71% — ковенант 70% соблюдается,             │
│     но запас минимальный. При падении продаж может         │
│     потребоваться корректировка графика выборки ПФ.        │
│                                                             │
│  [📈 График эскроу]  [Прогноз наполнения]  [Отчёт в банк]  │
└─────────────────────────────────────────────────────────────┘
```

### 16.6. Сценарий 5: Сравнение со входом

```
Катя: "Сравни вариант входа в проект и текущую модель
       по основным ФЭП"

┌─────────────────────────────────────────────────────────────┐
│  AI: Сравнение: вход в проект vs текущая модель            │
│                                                             │
│  ┌─────────────────────┬───────────┬───────────┬──────────┐│
│  │ Показатель          │ Вход      │ Текущая   │ Δ        ││
│  ├─────────────────────┼───────────┼───────────┼──────────┤│
│  │ Цена продажи, т.р/м²│ 550       │ 605       │ +55 +10% ││
│  │ СМР, т.р/м²         │ 230       │ 265       │ +35 +15% ││
│  │ Налоги + фин.расх.  │ 48        │ 60        │ +12 +25% ││
│  │ Маржа, т.р/м²       │ 85        │ 93        │ +8  +9%  ││
│  │ Маржа, млн ₽        │ 2 720     │ 3 280     │ +560     ││
│  │ Маржинальность      │ 15.5%     │ 15.4%     │ −0.1%    ││
│  │ IRR                 │ 22%       │ 21%       │ −1%      ││
│  └─────────────────────┴───────────┴───────────┴──────────┘│
│                                                             │
│  📝 Выводы:                                                 │
│  • Цены выросли на 10% (+55 т.р/м²)                        │
│  • СМР подорожал на 15% (+35 т.р/м²)                       │
│  • Налоги и финрасходы +12 т.р/м²                          │
│  • Но финрез лучше на 8 т.р/м² или 560 млн ₽               │
│  • Маржинальность почти не изменилась                      │
│                                                             │
│  [📄 Скачать сравнение]  [Детальный анализ]                │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

Катя: "А что с ликвидностью при раскрытии эскроу?"

┌─────────────────────────────────────────────────────────────┐
│  AI: Сравнение ликвидности при раскрытии:                  │
│                                                             │
│  ┌──────────────────────────┬───────────┬──────────┐       │
│  │ Показатель               │ Вход      │ Текущая  │       │
│  ├──────────────────────────┼───────────┼──────────┤       │
│  │ Накоплено на эскроу      │ 4.2 млрд  │ 4.6 млрд │       │
│  │ Долг ПФ на момент раскр. │ 4.0 млрд  │ 5.4 млрд │       │
│  │ Погашение при раскрытии  │ 95%       │ 85%      │       │
│  │ Остаток долга            │ 200 млн   │ 810 млн  │       │
│  │ Срок погашения остатка   │ 1 кв      │ 2 кв     │       │
│  └──────────────────────────┴───────────┴──────────┘       │
│                                                             │
│  📝 В базовом варианте при раскрытии эскроу погашалось     │
│     95% ПФ. В текущей модели — 85%, остаток 810 млн        │
│     гасится из продаж за 2 квартала.                       │
│                                                             │
│  ⚠️ Риск: увеличенная зависимость от темпов продаж         │
│     после ввода в эксплуатацию.                            │
│                                                             │
│  [График ликвидности]  [Стресс-тест]                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 17. Контакты и ресурсы
- **Supabase**: https://supabase.com/docs
- **AG Grid**: https://www.ag-grid.com/react-data-grid/
- **Recharts**: https://recharts.org
- **ECharts**: https://echarts.apache.org
- **FastAPI**: https://fastapi.tiangolo.com
- **shadcn/ui**: https://ui.shadcn.com
