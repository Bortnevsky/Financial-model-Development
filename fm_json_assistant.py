#!/usr/bin/env python3
"""
Financial Model JSON Assistant - анализ финансовых моделей в JSON через Claude API
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

try:
    import anthropic
except ImportError:
    print("Установите anthropic: pip install anthropic")
    exit(1)

# Файл для хранения настроек
CONFIG_FILE = Path(__file__).parent / ".fm_config.json"

# Доступные модели
MODELS = {
    "1": ("claude-sonnet-4-5-20250514", "Claude Sonnet 4.5"),
    "2": ("claude-opus-4-5-20251101", "Claude Opus 4.5"),
    "3": ("claude-3-5-haiku-20241022", "Claude Haiku 3.5"),
}


def load_config() -> Dict[str, Any]:
    """Загрузить конфигурацию из файла"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Сохранить конфигурацию в файл"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def get_api_key() -> str:
    """Получить API ключ (из конфига или запросить у пользователя)"""
    config = load_config()

    if "api_key" in config and config["api_key"]:
        print(f"Сохранённый API ключ: {config['api_key'][:10]}...{config['api_key'][-4:]}")
        use_saved = input("Использовать его? (Enter - да, n - ввести новый): ").strip().lower()
        if use_saved != "n":
            return config["api_key"]

    api_key = input("Введите ваш Anthropic API ключ: ").strip()

    if api_key:
        config["api_key"] = api_key
        save_config(config)
        print("API ключ сохранён!")

    return api_key


def select_model() -> Tuple[str, str]:
    """Выбрать модель Claude. Возвращает (model_id, model_name)"""
    config = load_config()

    print("\nДоступные модели:")
    for key, (model_id, name) in MODELS.items():
        marker = " ← текущая" if config.get("model") == model_id else ""
        print(f"  {key}. {name}{marker}")

    if "model" in config:
        print(f"\nEnter - оставить текущую")

    choice = input("Выберите модель (1-3): ").strip()

    if choice in MODELS:
        model_id, model_name = MODELS[choice]
        config["model"] = model_id
        config["model_name"] = model_name
        save_config(config)
        print(f"Выбрана: {model_name}")
        return model_id, model_name
    elif "model" in config:
        return config["model"], config.get("model_name", config["model"])
    else:
        # По умолчанию Sonnet
        model_id, model_name = MODELS["1"]
        config["model"] = model_id
        config["model_name"] = model_name
        save_config(config)
        return model_id, model_name


def extract_cell_references(formula: str) -> List[Tuple[Optional[str], str]]:
    """
    Извлечь все ссылки на ячейки из формулы.
    Возвращает список (sheet_name или None, cell_address)
    """
    if not formula:
        return []

    refs = []
    # Паттерн: 'Sheet'!A1 или Sheet!A1 или просто A1
    # Также $A$1, A$1, $A1
    pattern = r"(?:'([^']+)'!|\b([A-Za-z0-9_]+)!)?\$?([A-Z]+)\$?(\d+)"

    for match in re.finditer(pattern, formula, re.IGNORECASE):
        sheet_quoted = match.group(1)  # 'Sheet Name'
        sheet_plain = match.group(2)   # SheetName
        col = match.group(3).upper()
        row = match.group(4)

        sheet = sheet_quoted or sheet_plain
        cell_addr = f"{col}{row}"
        refs.append((sheet, cell_addr))

    return refs


def get_cell(model: Dict, sheet: str, addr: str) -> Optional[Dict]:
    """Получить ячейку из модели"""
    if sheet not in model:
        # Попробуем найти без учёта регистра
        for s in model.keys():
            if s.lower() == sheet.lower():
                sheet = s
                break
        else:
            return None

    return model[sheet]["cells"].get(addr.upper())


def get_row_label(model: Dict, sheet: str, row: int) -> str:
    """Получить название строки (из колонок A, B или C)"""
    for col in ['A', 'B', 'C', 'D']:
        cell = get_cell(model, sheet, f"{col}{row}")
        if cell and cell.get('v'):
            val = str(cell.get('v'))
            if val and not val.startswith('=') and len(val) > 1:
                return val
    return ""


def get_column_header(model: Dict, sheet: str, col: str) -> str:
    """Получить заголовок колонки (из строк 1-5)"""
    for row in range(1, 6):
        cell = get_cell(model, sheet, f"{col}{row}")
        if cell:
            val = cell.get('v') or cell.get('f')
            if val and not str(val).startswith('='):
                return str(val)
    return ""


def analyze_cell(model: Dict, sheet: str, addr: str) -> Dict[str, Any]:
    """Полный анализ ячейки"""
    cell = get_cell(model, sheet, addr)

    if not cell:
        return {"error": f"Ячейка {sheet}!{addr} не найдена"}

    # Парсим адрес
    match = re.match(r"([A-Z]+)(\d+)", addr.upper())
    if not match:
        return {"error": f"Некорректный адрес: {addr}"}

    col = match.group(1)
    row = int(match.group(2))

    result = {
        "sheet": sheet,
        "address": addr.upper(),
        "full_address": f"'{sheet}'!{addr.upper()}",
        "value": cell.get("v"),
        "formula": cell.get("f"),
        "format": cell.get("fmt"),
        "row_label": get_row_label(model, sheet, row),
        "col_header": get_column_header(model, sheet, col),
        "referenced_cells": {},
        "context": []
    }

    # Анализируем ссылки в формуле
    if result["formula"]:
        refs = extract_cell_references(result["formula"])
        for ref_sheet, ref_addr in refs:
            ref_sheet = ref_sheet or sheet
            ref_cell = get_cell(model, ref_sheet, ref_addr)
            key = f"'{ref_sheet}'!{ref_addr}"
            if ref_cell:
                if ref_cell.get("f"):
                    result["referenced_cells"][key] = {
                        "formula": ref_cell["f"],
                        "format": ref_cell.get("fmt")
                    }
                else:
                    result["referenced_cells"][key] = {
                        "value": ref_cell.get("v"),
                        "format": ref_cell.get("fmt")
                    }
                # Добавляем label для ссылки
                ref_match = re.match(r"([A-Z]+)(\d+)", ref_addr.upper())
                if ref_match:
                    ref_row = int(ref_match.group(2))
                    label = get_row_label(model, ref_sheet, ref_row)
                    if label:
                        result["referenced_cells"][key]["label"] = label
            else:
                result["referenced_cells"][key] = {"error": "не найдена"}

    # Контекст - соседние ячейки в той же колонке
    for r in range(max(1, row - 3), row + 4):
        ctx_cell = get_cell(model, sheet, f"{col}{r}")
        label = get_row_label(model, sheet, r)
        ctx_info = {
            "address": f"{col}{r}",
            "row": r,
            "label": label,
            "is_target": r == row
        }
        if ctx_cell:
            if ctx_cell.get("f"):
                ctx_info["formula"] = ctx_cell["f"]
            else:
                ctx_info["value"] = ctx_cell.get("v")
        result["context"].append(ctx_info)

    return result


def ask_claude(client: anthropic.Anthropic, model_id: str,
               analysis: Dict[str, Any], question: str) -> str:
    """Отправить анализ ячейки Claude для объяснения"""

    system_prompt = """Ты эксперт по финансовому моделированию и Excel/Google Sheets.
Твоя задача - анализировать формулы и данные в финансовых моделях.

Когда объясняешь формулу:
1. СНАЧАЛА покажи саму формулу как есть
2. Разбери каждую часть формулы в таблице
3. Объясни логику формулы (что она вычисляет)
4. Объясни бизнес-смысл простыми словами

Отвечай на русском языке. Будь конкретен. Используй markdown для форматирования."""

    # Формируем промпт
    prompt_parts = [
        f"## Анализ ячейки {analysis['full_address']}",
        f"**Название строки:** {analysis.get('row_label', 'не определено')}",
    ]

    if analysis.get("formula"):
        prompt_parts.append(f"\n**ФОРМУЛА:**\n```\n{analysis['formula']}\n```")
    else:
        prompt_parts.append(f"\n**Значение:** {analysis.get('value')}")

    if analysis.get("format"):
        prompt_parts.append(f"**Формат:** {analysis['format']}")

    if analysis.get("referenced_cells"):
        prompt_parts.append("\n**Ячейки, на которые ссылается формула:**")
        for ref, info in analysis["referenced_cells"].items():
            label = info.get("label", "")
            label_str = f" ({label})" if label else ""
            if "formula" in info:
                prompt_parts.append(f"- `{ref}`{label_str}: формула `{info['formula']}`")
            elif "value" in info:
                prompt_parts.append(f"- `{ref}`{label_str}: значение = {info['value']}")
            else:
                prompt_parts.append(f"- `{ref}`{label_str}: {info.get('error', '?')}")

    if analysis.get("context"):
        prompt_parts.append("\n**Контекст (соседние строки):**")
        for ctx in analysis["context"]:
            marker = " ← ЦЕЛЕВАЯ ЯЧЕЙКА" if ctx.get("is_target") else ""
            label = ctx.get("label", "")
            if "formula" in ctx:
                prompt_parts.append(f"- {ctx['address']} {label}: формула{marker}")
            elif "value" in ctx:
                prompt_parts.append(f"- {ctx['address']} {label}: {ctx['value']}{marker}")
            else:
                prompt_parts.append(f"- {ctx['address']} {label}: пусто{marker}")

    prompt_parts.append(f"\n**Вопрос пользователя:** {question}")

    full_prompt = "\n".join(prompt_parts)

    response = client.messages.create(
        model=model_id,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": full_prompt}]
    )

    return response.content[0].text


def parse_cell_reference_from_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Парсит ввод пользователя и извлекает лист и адрес ячейки.
    Примеры: "CF2!P87", "на листе cf2 в ячейке p87", "p87 на листе cf2"
    """
    text = text.strip()

    # Паттерн 1: Sheet!Cell
    match = re.search(r"['\"]?([A-Za-zА-Яа-я0-9_\s]+)['\"]?!([A-Za-z]+\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).upper()

    # Паттерн 2: "на листе X ячейка Y" или "лист X ячейка Y"
    match = re.search(r"(?:на\s+)?лист[еа]?\s+([A-Za-zА-Яа-я0-9_]+)\s+.*?([A-Za-z]+\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2).upper()

    # Паттерн 3: "ячейка Y на листе X"
    match = re.search(r"([A-Za-z]+\d+)\s+(?:на\s+)?лист[еа]?\s+([A-Za-zА-Яа-я0-9_]+)", text, re.IGNORECASE)
    if match:
        return match.group(2), match.group(1).upper()

    # Паттерн 4: просто адрес ячейки
    match = re.search(r"\b([A-Za-z]{1,3}\d{1,5})\b", text)
    if match:
        return None, match.group(1).upper()

    return None, None


def list_sheets(model: Dict) -> None:
    """Показать список листов"""
    print("\nЛисты в модели:")
    for name, data in model.items():
        cells_count = len(data.get("cells", {}))
        print(f"  - {name} ({data.get('rows', '?')}x{data.get('cols', '?')}, {cells_count} ячеек)")


def select_json_file() -> Optional[str]:
    """Выбрать JSON файл"""
    json_files = list(Path(".").glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith(".")]

    if not json_files:
        print("JSON файлы не найдены!")
        return None

    print("\nДоступные JSON файлы:")
    for i, f in enumerate(json_files, 1):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {i}. {f.name} ({size_mb:.2f} MB)")

    choice = input("\nВыберите файл (номер): ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(json_files):
            return str(json_files[idx])
    except ValueError:
        if Path(choice).exists():
            return choice

    return None


def main():
    print("=" * 60)
    print("  Financial Model JSON Assistant")
    print("  Анализ финансовых моделей через Claude AI")
    print("=" * 60)

    # Получаем API ключ
    api_key = get_api_key()
    if not api_key:
        print("API ключ не указан. Выход.")
        return

    # Выбираем модель
    model_id, model_name = select_model()

    # Создаём клиент
    try:
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Ошибка создания клиента: {e}")
        return

    # Выбираем файл
    os.chdir(Path(__file__).parent)
    json_path = select_json_file()
    if not json_path:
        print("Файл не выбран. Выход.")
        return

    print(f"\nЗагрузка {json_path}...")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            fm_model = json.load(f)
        print("Загружено!")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    list_sheets(fm_model)

    # Текущий лист по умолчанию
    current_sheet = list(fm_model.keys())[0]

    print("\n" + "-" * 60)
    print("Как спрашивать:")
    print("  - CF2!P87 или 'на листе cf2 ячейка p87'")
    print("  - P87 (использует текущий лист)")
    print("Команды:")
    print("  - 'лист X' - сменить текущий лист")
    print("  - 'листы' - показать все листы")
    print("  - 'модель' - сменить модель Claude")
    print("  - 'q' - выход")
    print("-" * 60)

    while True:
        try:
            prompt = f"\n[{current_sheet}] [{model_name}] > "
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("q", "quit", "выход", "exit"):
            print("До свидания!")
            break

        if lower in ("листы", "sheets", "list"):
            list_sheets(fm_model)
            continue

        if lower in ("модель", "model"):
            model_id, model_name = select_model()
            continue

        # Смена текущего листа
        match = re.match(r"лист\s+(.+)", lower)
        if match:
            new_sheet = match.group(1).strip()
            # Ищем лист
            for s in fm_model.keys():
                if s.lower() == new_sheet.lower():
                    current_sheet = s
                    print(f"Текущий лист: {current_sheet}")
                    break
            else:
                print(f"Лист '{new_sheet}' не найден")
            continue

        # Ищем ссылку на ячейку
        sheet, addr = parse_cell_reference_from_input(user_input)

        if not addr:
            print("Не нашёл ячейку в вопросе. Укажите например: CF2!P87 или 'p87'")
            continue

        sheet = sheet or current_sheet

        print(f"\nАнализирую {sheet}!{addr}...")

        # Анализируем ячейку
        analysis = analyze_cell(fm_model, sheet, addr)

        if "error" in analysis:
            print(f"Ошибка: {analysis['error']}")
            continue

        # Выводим базовую информацию
        print(f"\n{'='*60}")
        print(f"Ячейка: {analysis['full_address']}")
        if analysis.get("row_label"):
            print(f"Строка: {analysis['row_label']}")
        if analysis.get("formula"):
            print(f"ФОРМУЛА: {analysis['formula']}")
        else:
            print(f"Значение: {analysis.get('value')}")
        print(f"{'='*60}")

        # Спрашиваем Claude
        try:
            print("\nСпрашиваю Claude...")
            answer = ask_claude(client, model_id, analysis, user_input)
            print(f"\n{answer}")
        except anthropic.APIError as e:
            print(f"Ошибка API: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
