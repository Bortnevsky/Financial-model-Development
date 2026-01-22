#!/usr/bin/env python3
"""
Financial Model Assistant - интерфейс для анализа Excel-моделей через Claude API
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string

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
        print(f"Используется сохранённый API ключ: {config['api_key'][:10]}...")
        use_saved = input("Использовать его? (Enter - да, n - ввести новый): ").strip().lower()
        if use_saved != "n":
            return config["api_key"]

    api_key = input("Введите ваш Anthropic API ключ: ").strip()

    if api_key:
        config["api_key"] = api_key
        save_config(config)
        print("API ключ сохранён!")

    return api_key


def select_model() -> str:
    """Выбрать модель Claude"""
    config = load_config()

    print("\nДоступные модели:")
    for key, (model_id, name) in MODELS.items():
        marker = " (текущая)" if config.get("model") == model_id else ""
        print(f"  {key}. {name}{marker}")

    if "model" in config:
        print(f"\nEnter - оставить текущую ({config.get('model_name', config['model'])})")

    choice = input("Выберите модель (1-3): ").strip()

    if choice in MODELS:
        model_id, model_name = MODELS[choice]
        config["model"] = model_id
        config["model_name"] = model_name
        save_config(config)
        print(f"Выбрана модель: {model_name}")
        return model_id
    elif "model" in config:
        return config["model"]
    else:
        # По умолчанию Sonnet
        model_id, model_name = MODELS["1"]
        config["model"] = model_id
        config["model_name"] = model_name
        save_config(config)
        return model_id


def parse_cell_reference(ref: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Парсит ссылку на ячейку вида 'Sheet!A1' или 'A1'
    Возвращает (sheet_name, cell_address)
    """
    ref = ref.strip()

    # Проверяем формат Sheet!Cell
    if "!" in ref:
        parts = ref.split("!", 1)
        sheet_name = parts[0].strip("'\"")
        cell_addr = parts[1].upper()
        return sheet_name, cell_addr

    # Только адрес ячейки
    match = re.match(r"^([A-Za-z]+)(\d+)$", ref)
    if match:
        return None, ref.upper()

    return None, None


def get_cell_info(workbook: openpyxl.Workbook, sheet_name: Optional[str], cell_addr: str) -> Dict[str, Any]:
    """Получить полную информацию о ячейке"""

    # Определяем лист
    if sheet_name:
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
        else:
            # Пробуем найти похожее имя (без учёта регистра)
            for name in workbook.sheetnames:
                if name.lower() == sheet_name.lower():
                    sheet = workbook[name]
                    sheet_name = name
                    break
            else:
                return {"error": f"Лист '{sheet_name}' не найден. Доступные листы: {workbook.sheetnames}"}
    else:
        sheet = workbook.active
        sheet_name = sheet.title

    try:
        cell = sheet[cell_addr]
    except:
        return {"error": f"Некорректный адрес ячейки: {cell_addr}"}

    info = {
        "sheet": sheet_name,
        "address": cell_addr,
        "full_address": f"'{sheet_name}'!{cell_addr}",
        "value": cell.value,
        "formula": None,
        "data_type": cell.data_type,
    }

    # Проверяем, есть ли формула
    if cell.data_type == "f" or (isinstance(cell.value, str) and cell.value.startswith("=")):
        info["formula"] = cell.value

    # Получаем вычисленное значение если есть формула
    if info["formula"]:
        # В openpyxl нет прямого способа получить вычисленное значение
        # но мы можем попробовать получить cached_value
        if hasattr(cell, 'value') and cell.value != info["formula"]:
            info["calculated_value"] = cell.value

    # Форматирование
    if cell.number_format:
        info["format"] = cell.number_format

    return info


def get_sheet_context(workbook: openpyxl.Workbook, sheet_name: str, cell_addr: str, radius: int = 5) -> str:
    """Получить контекст вокруг ячейки для лучшего понимания"""

    if sheet_name not in workbook.sheetnames:
        for name in workbook.sheetnames:
            if name.lower() == sheet_name.lower():
                sheet_name = name
                break
        else:
            return ""

    sheet = workbook[sheet_name]

    # Парсим адрес ячейки
    match = re.match(r"^([A-Za-z]+)(\d+)$", cell_addr)
    if not match:
        return ""

    col_letter = match.group(1).upper()
    row = int(match.group(2))
    col = column_index_from_string(col_letter)

    # Определяем диапазон
    start_row = max(1, row - radius)
    end_row = min(sheet.max_row or row + radius, row + radius)
    start_col = max(1, col - radius)
    end_col = min(sheet.max_column or col + radius, col + radius)

    context_lines = []
    context_lines.append(f"Контекст листа '{sheet_name}' вокруг ячейки {cell_addr}:")
    context_lines.append("")

    # Заголовок с колонками
    header = "     "
    for c in range(start_col, end_col + 1):
        header += f"{get_column_letter(c):>12}"
    context_lines.append(header)

    # Данные
    for r in range(start_row, end_row + 1):
        row_str = f"{r:4} "
        for c in range(start_col, end_col + 1):
            cell = sheet.cell(row=r, column=c)
            val = cell.value
            if val is None:
                val_str = ""
            elif isinstance(val, str) and val.startswith("="):
                val_str = "[F]"  # Формула
            elif isinstance(val, (int, float)):
                val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
            else:
                val_str = str(val)[:10]

            # Помечаем целевую ячейку
            if r == row and c == col:
                val_str = f">>>{val_str}<<<"

            row_str += f"{val_str:>12}"
        context_lines.append(row_str)

    return "\n".join(context_lines)


def get_referenced_cells(workbook: openpyxl.Workbook, formula: str, current_sheet: str) -> Dict[str, Any]:
    """Извлечь значения ячеек, на которые ссылается формула"""

    if not formula or not formula.startswith("="):
        return {}

    references = {}

    # Паттерн для поиска ссылок на ячейки: Sheet!A1 или просто A1
    # Также ищем диапазоны A1:B2
    pattern = r"(?:'([^']+)'!)?([A-Za-z]+\d+)(?::([A-Za-z]+\d+))?"

    for match in re.finditer(pattern, formula):
        sheet_name = match.group(1) or current_sheet
        start_cell = match.group(2).upper()
        end_cell = match.group(3)

        if end_cell:
            # Это диапазон
            key = f"'{sheet_name}'!{start_cell}:{end_cell.upper()}"
            references[key] = "[диапазон]"
        else:
            # Одиночная ячейка
            key = f"'{sheet_name}'!{start_cell}"
            try:
                if sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                else:
                    for name in workbook.sheetnames:
                        if name.lower() == sheet_name.lower():
                            sheet = workbook[name]
                            break
                    else:
                        continue

                cell = sheet[start_cell]
                val = cell.value
                if isinstance(val, str) and val.startswith("="):
                    references[key] = f"[формула: {val[:50]}...]" if len(val) > 50 else f"[формула: {val}]"
                else:
                    references[key] = val
            except:
                references[key] = "[ошибка чтения]"

    return references


def analyze_cell_with_claude(client: anthropic.Anthropic, model: str,
                             cell_info: Dict[str, Any], context: str,
                             referenced_cells: Dict[str, Any],
                             user_question: str) -> str:
    """Отправить запрос к Claude для анализа ячейки"""

    system_prompt = """Ты эксперт по финансовому моделированию и Excel.
Твоя задача - анализировать формулы и данные в финансовых моделях.
Отвечай на русском языке. Будь конкретен и понятен.
Когда объясняешь формулу:
1. Покажи саму формулу
2. Разбери каждую часть формулы
3. Объясни бизнес-смысл простыми словами
4. Если есть ссылки на другие ячейки - объясни что в них"""

    # Формируем сообщение
    message_parts = [
        f"Пользователь спрашивает о ячейке: {cell_info.get('full_address', 'неизвестно')}",
        f"\nИнформация о ячейке:",
        f"- Значение: {cell_info.get('value')}",
    ]

    if cell_info.get("formula"):
        message_parts.append(f"- ФОРМУЛА: {cell_info['formula']}")

    if cell_info.get("format"):
        message_parts.append(f"- Формат: {cell_info['format']}")

    if referenced_cells:
        message_parts.append("\nЗначения ячеек, на которые ссылается формула:")
        for ref, val in referenced_cells.items():
            message_parts.append(f"  {ref} = {val}")

    if context:
        message_parts.append(f"\n{context}")

    message_parts.append(f"\nВопрос пользователя: {user_question}")

    full_message = "\n".join(message_parts)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": full_message}
        ]
    )

    return response.content[0].text


def list_sheets(workbook: openpyxl.Workbook) -> None:
    """Показать список листов в книге"""
    print("\nЛисты в файле:")
    for i, name in enumerate(workbook.sheetnames, 1):
        sheet = workbook[name]
        print(f"  {i}. {name} ({sheet.max_row}x{sheet.max_column})")


def select_excel_file() -> Optional[str]:
    """Выбрать Excel файл из текущей директории"""
    excel_files = list(Path(".").glob("*.xlsx")) + list(Path(".").glob("*.xls"))

    if not excel_files:
        print("Excel файлы не найдены в текущей директории!")
        return None

    print("\nДоступные Excel файлы:")
    for i, f in enumerate(excel_files, 1):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {i}. {f.name} ({size_mb:.2f} MB)")

    choice = input("\nВыберите файл (номер) или введите путь: ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(excel_files):
            return str(excel_files[idx])
    except ValueError:
        if Path(choice).exists():
            return choice

    return None


def main():
    print("=" * 60)
    print("  Financial Model Assistant")
    print("  Анализ Excel-моделей с помощью Claude AI")
    print("=" * 60)

    # Получаем API ключ
    api_key = get_api_key()
    if not api_key:
        print("API ключ не указан. Выход.")
        return

    # Выбираем модель
    model = select_model()

    # Создаём клиент
    try:
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Ошибка создания клиента: {e}")
        return

    # Выбираем файл
    os.chdir(Path(__file__).parent)
    excel_path = select_excel_file()
    if not excel_path:
        print("Файл не выбран. Выход.")
        return

    print(f"\nЗагрузка файла: {excel_path}...")
    try:
        # data_only=False чтобы видеть формулы
        workbook = openpyxl.load_workbook(excel_path, data_only=False)
        print(f"Файл загружен успешно!")
    except Exception as e:
        print(f"Ошибка загрузки файла: {e}")
        return

    list_sheets(workbook)

    print("\n" + "-" * 60)
    print("Команды:")
    print("  - Введите адрес ячейки: CF2!P87 или просто P87")
    print("  - 'листы' или 'sheets' - показать список листов")
    print("  - 'модель' или 'model' - сменить модель Claude")
    print("  - 'файл' или 'file' - выбрать другой файл")
    print("  - 'выход' или 'q' - выход")
    print("-" * 60)

    current_sheet = workbook.active.title

    while True:
        try:
            user_input = input(f"\n[{current_sheet}] Ваш вопрос: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not user_input:
            continue

        lower_input = user_input.lower()

        if lower_input in ("выход", "q", "exit", "quit"):
            print("До свидания!")
            break

        if lower_input in ("листы", "sheets", "list"):
            list_sheets(workbook)
            continue

        if lower_input in ("модель", "model"):
            model = select_model()
            continue

        if lower_input in ("файл", "file"):
            new_path = select_excel_file()
            if new_path:
                try:
                    workbook = openpyxl.load_workbook(new_path, data_only=False)
                    excel_path = new_path
                    current_sheet = workbook.active.title
                    print(f"Загружен: {excel_path}")
                    list_sheets(workbook)
                except Exception as e:
                    print(f"Ошибка: {e}")
            continue

        # Ищем упоминание ячейки в вопросе
        # Паттерны: CF2!P87, 'CF2'!P87, лист CF2 ячейка P87, на листе cf2 в ячейке p87
        cell_patterns = [
            r"(?:'?([A-Za-zА-Яа-я0-9_\s]+)'?[!])?([A-Za-z]+\d+)",  # Sheet!Cell или Cell
            r"(?:лист[еа]?\s+)([A-Za-zА-Яа-я0-9_]+)\s+(?:в\s+)?(?:ячейк[аеи]\s+)?([A-Za-z]+\d+)",  # на листе X ячейка Y
            r"(?:ячейк[аеи]\s+)([A-Za-z]+\d+)\s+(?:на\s+)?(?:лист[еа]?\s+)?([A-Za-zА-Яа-я0-9_]+)",  # ячейка Y на листе X
        ]

        sheet_name = None
        cell_addr = None

        for pattern in cell_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    if groups[0] and re.match(r"^[A-Za-z]+\d+$", groups[0]):
                        # Второй паттерн - сначала ячейка, потом лист
                        cell_addr = groups[0].upper()
                        sheet_name = groups[1]
                    else:
                        sheet_name = groups[0]
                        cell_addr = groups[1].upper() if groups[1] else None
                break

        if not cell_addr:
            # Пробуем найти просто адрес ячейки
            simple_match = re.search(r"\b([A-Za-z]{1,3}\d{1,5})\b", user_input)
            if simple_match:
                cell_addr = simple_match.group(1).upper()

        if cell_addr:
            target_sheet = sheet_name if sheet_name else current_sheet
            print(f"\nАнализирую ячейку {target_sheet}!{cell_addr}...")

            # Получаем информацию о ячейке
            cell_info = get_cell_info(workbook, target_sheet, cell_addr)

            if "error" in cell_info:
                print(f"Ошибка: {cell_info['error']}")
                continue

            # Получаем контекст
            context = get_sheet_context(workbook, cell_info["sheet"], cell_addr)

            # Получаем значения ячеек из формулы
            referenced_cells = {}
            if cell_info.get("formula"):
                referenced_cells = get_referenced_cells(workbook, cell_info["formula"], cell_info["sheet"])

            # Показываем информацию
            print(f"\n{'=' * 50}")
            print(f"Ячейка: {cell_info['full_address']}")
            print(f"Значение: {cell_info['value']}")
            if cell_info.get("formula"):
                print(f"ФОРМУЛА: {cell_info['formula']}")
            print(f"{'=' * 50}")

            # Спрашиваем Claude
            try:
                print("\nСпрашиваю Claude...")
                answer = analyze_cell_with_claude(
                    client, model, cell_info, context,
                    referenced_cells, user_input
                )
                print(f"\n{answer}")
            except anthropic.APIError as e:
                print(f"Ошибка API: {e}")
            except Exception as e:
                print(f"Ошибка: {e}")

        else:
            # Общий вопрос без конкретной ячейки
            print("Не нашёл упоминания ячейки в вопросе.")
            print("Укажите ячейку, например: 'что в ячейке CF2!P87?' или 'объясни P87'")


if __name__ == "__main__":
    main()
