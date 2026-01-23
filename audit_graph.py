#!/usr/bin/env python3
"""
Аудит графа зависимостей финансовой модели.
Проверяет полноту и корректность данных графа.
"""

import json
import re
from collections import defaultdict


def parse_cell_references(formula: str) -> list[tuple[str, str]]:
    """
    Парсит ссылки на ячейки из формулы Excel.
    Возвращает список (sheet, cell) кортежей.
    """
    refs = []

    # Паттерн для ссылок: опциональный лист + ячейка
    # Примеры: A1, $A$1, Sheet1!A1, 'Sheet Name'!A1, DB!$A$1

    # Ссылки с листом (Sheet!Cell)
    sheet_ref = r"(?:'([^']+)'|([A-Za-z0-9_А-Яа-яЁё]+))!\$?([A-Z]+)\$?(\d+)"
    for m in re.finditer(sheet_ref, formula):
        sheet = m.group(1) or m.group(2)
        cell = f"{m.group(3)}{m.group(4)}"
        refs.append((sheet, cell))

    # Простые ссылки без листа (локальные)
    # Исключаем то, что уже поймали как Sheet!Cell
    simple_ref = r"(?<![A-Za-z0-9_!])(\$?[A-Z]+\$?\d+)(?![A-Za-z0-9_])"
    formula_no_sheets = re.sub(sheet_ref, '', formula)
    for m in re.finditer(simple_ref, formula_no_sheets):
        cell = m.group(1).replace('$', '')
        refs.append((None, cell))  # None = текущий лист

    return refs


def parse_range_references(formula: str) -> list[tuple[str, str, str]]:
    """
    Парсит диапазоны ячеек из формулы.
    Возвращает список (sheet, start_cell, end_cell) кортежей.
    """
    ranges = []

    # Диапазон с листом: Sheet!A1:B10
    sheet_range = r"(?:'([^']+)'|([A-Za-z0-9_А-Яа-яЁё]+))!\$?([A-Z]+)\$?(\d+):\$?([A-Z]+)\$?(\d+)"
    for m in re.finditer(sheet_range, formula):
        sheet = m.group(1) or m.group(2)
        start = f"{m.group(3)}{m.group(4)}"
        end = f"{m.group(5)}{m.group(6)}"
        ranges.append((sheet, start, end))

    # Простой диапазон без листа: A1:B10
    simple_range = r"(?<![A-Za-z0-9_!])(\$?[A-Z]+\$?\d+):(\$?[A-Z]+\$?\d+)"
    formula_no_sheets = re.sub(sheet_range, '', formula)
    for m in re.finditer(simple_range, formula_no_sheets):
        start = m.group(1).replace('$', '')
        end = m.group(2).replace('$', '')
        ranges.append((None, start, end))

    return ranges


def expand_range(start: str, end: str) -> list[str]:
    """Раскрывает диапазон в список ячеек."""
    col_start = re.match(r'([A-Z]+)', start).group(1)
    row_start = int(re.search(r'(\d+)', start).group(1))
    col_end = re.match(r'([A-Z]+)', end).group(1)
    row_end = int(re.search(r'(\d+)', end).group(1))

    def col_to_num(col):
        num = 0
        for c in col:
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num

    def num_to_col(num):
        result = ''
        while num > 0:
            num -= 1
            result = chr(num % 26 + ord('A')) + result
            num //= 26
        return result

    cells = []
    for col_num in range(col_to_num(col_start), col_to_num(col_end) + 1):
        for row in range(row_start, row_end + 1):
            cells.append(f"{num_to_col(col_num)}{row}")

    return cells


def audit_graph(model_path: str = 'fm_model.json', graph_path: str = 'graph_data.json'):
    """Выполняет комплексный аудит графа."""

    print("=" * 60)
    print("АУДИТ ГРАФА ЗАВИСИМОСТЕЙ")
    print("=" * 60)

    # Загрузка данных
    with open(model_path) as f:
        model = json.load(f)

    with open(graph_path) as f:
        graph = json.load(f)

    nodes = {n['id']: n for n in graph['nodes']}
    edges = graph['edges']
    graph_sheets = set(graph.get('sheets', []))

    print(f"\n📊 ОБЗОР:")
    print(f"   Листов в модели: {len(model)}")
    print(f"   Листов в графе: {len(graph_sheets)} ({', '.join(sorted(graph_sheets))})")
    print(f"   Узлов в графе: {len(nodes)}")
    print(f"   Связей в графе: {len(edges)}")

    # ============================================
    # ТЕСТ 1: Количественная сверка по листам
    # ============================================
    print("\n" + "=" * 60)
    print("ТЕСТ 1: КОЛИЧЕСТВЕННАЯ СВЕРКА")
    print("=" * 60)

    total_model_formulas = 0
    total_graph_nodes = 0
    issues = []

    for sheet in sorted(graph_sheets):
        if sheet not in model:
            issues.append(f"⚠️  Лист '{sheet}' есть в графе, но нет в модели!")
            continue

        # Формулы в модели для этого листа
        model_formulas = {
            f"{sheet}!{addr}"
            for addr, cell in model[sheet].get('cells', {}).items()
            if cell.get('f')
        }

        # Узлы графа для этого листа
        graph_nodes_sheet = {
            node_id for node_id in nodes
            if node_id.startswith(f"{sheet}!")
        }

        total_model_formulas += len(model_formulas)
        total_graph_nodes += len(graph_nodes_sheet)

        # Сравнение
        missing_in_graph = model_formulas - graph_nodes_sheet
        extra_in_graph = graph_nodes_sheet - model_formulas

        status = "✅" if not missing_in_graph and not extra_in_graph else "⚠️"
        print(f"\n{status} {sheet}:")
        print(f"   Формул в модели: {len(model_formulas)}")
        print(f"   Узлов в графе: {len(graph_nodes_sheet)}")

        if missing_in_graph:
            print(f"   ❌ Отсутствуют в графе: {len(missing_in_graph)}")
            if len(missing_in_graph) <= 10:
                for m in sorted(missing_in_graph)[:10]:
                    print(f"      - {m}")
            else:
                for m in sorted(missing_in_graph)[:5]:
                    print(f"      - {m}")
                print(f"      ... и ещё {len(missing_in_graph) - 5}")

        if extra_in_graph:
            print(f"   ⚠️  Лишние в графе (нет формулы): {len(extra_in_graph)}")
            for e in sorted(extra_in_graph)[:5]:
                print(f"      - {e}")

    print(f"\n📈 ИТОГО по листам графа:")
    print(f"   Формул в модели: {total_model_formulas}")
    print(f"   Узлов в графе: {total_graph_nodes}")

    # ============================================
    # ТЕСТ 2: Полнота связей
    # ============================================
    print("\n" + "=" * 60)
    print("ТЕСТ 2: ПОЛНОТА СВЯЗЕЙ")
    print("=" * 60)

    # Строим карту зависимостей из графа
    graph_deps = defaultdict(set)  # node -> {dependencies}
    for edge in edges:
        graph_deps[edge['to']].add(edge['from'])

    missing_deps = []
    checked = 0

    for node_id, node in nodes.items():
        formula = node.get('formula', '')
        if not formula or not formula.startswith('='):
            continue

        checked += 1
        sheet = node.get('sheet', node_id.split('!')[0])

        # Парсим зависимости из формулы
        refs = parse_cell_references(formula)
        ranges = parse_range_references(formula)

        expected_deps = set()

        # Добавляем прямые ссылки
        for ref_sheet, ref_cell in refs:
            ref_sheet = ref_sheet or sheet  # если None - текущий лист
            expected_deps.add(f"{ref_sheet}!{ref_cell}")

        # Добавляем диапазоны (только границы для проверки)
        for range_sheet, start, end in ranges:
            range_sheet = range_sheet or sheet
            expected_deps.add(f"{range_sheet}!{start}")
            expected_deps.add(f"{range_sheet}!{end}")

        # Фильтруем только ячейки из листов графа
        expected_deps = {
            d for d in expected_deps
            if d.split('!')[0] in graph_sheets
        }

        # Проверяем наличие в графе
        actual_deps = graph_deps.get(node_id, set())

        missing = expected_deps - actual_deps
        if missing:
            # Проверяем - может эти ячейки просто не в графе (значения, не формулы)
            truly_missing = [m for m in missing if m in nodes]
            if truly_missing:
                missing_deps.append({
                    'node': node_id,
                    'formula': formula[:80] + '...' if len(formula) > 80 else formula,
                    'missing': truly_missing
                })

    print(f"   Проверено формул: {checked}")
    print(f"   Проблемных: {len(missing_deps)}")

    if missing_deps:
        print("\n   ❌ Примеры недостающих связей:")
        for item in missing_deps[:5]:
            print(f"      {item['node']}: {item['formula']}")
            print(f"         Нет связей от: {item['missing']}")
    else:
        print("   ✅ Все связи корректны!")

    # ============================================
    # ТЕСТ 3: Сироты (узлы без связей)
    # ============================================
    print("\n" + "=" * 60)
    print("ТЕСТ 3: АНАЛИЗ СТРУКТУРЫ ГРАФА")
    print("=" * 60)

    # Собираем статистику связей
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for edge in edges:
        out_degree[edge['from']] += 1
        in_degree[edge['to']] += 1

    # Изолированные узлы (нет ни входящих, ни исходящих)
    orphans = [n for n in nodes if in_degree[n] == 0 and out_degree[n] == 0]

    # Входные узлы (нет входящих, но есть исходящие)
    inputs = [n for n in nodes if in_degree[n] == 0 and out_degree[n] > 0]

    # Выходные узлы (есть входящие, но нет исходящих)
    outputs = [n for n in nodes if in_degree[n] > 0 and out_degree[n] == 0]

    print(f"   Изолированные (сироты): {len(orphans)}")
    print(f"   Входные (листья): {len(inputs)}")
    print(f"   Выходные (корни): {len(outputs)}")

    if orphans:
        print("\n   ⚠️  Изолированные узлы (подозрительно!):")
        for o in orphans[:10]:
            node = nodes[o]
            formula = node.get('formula', node.get('value', ''))
            print(f"      {o}: {str(formula)[:50]}")

    # ============================================
    # ТЕСТ 4: Edge-cases парсера
    # ============================================
    print("\n" + "=" * 60)
    print("ТЕСТ 4: ПРОВЕРКА ПАРСЕРА ФОРМУЛ")
    print("=" * 60)

    test_cases = [
        ("=A1+B2", [("A1", None), ("B2", None)]),
        ("=SUM(A1:A10)", []),  # диапазон, не прямые ссылки
        ("=DB!A1+DB1!B2", [("A1", "DB"), ("B2", "DB1")]),
        ("='Sheet Name'!A1", [("A1", "Sheet Name")]),
        ("=$A$1+B$2+$C3", [("A1", None), ("B2", None), ("C3", None)]),
        ("=IF(A1>0,B1,C1)", [("A1", None), ("B1", None), ("C1", None)]),
        ("=VLOOKUP(A1,DB!A:B,2,FALSE)", [("A1", None)]),  # A:B - диапазон колонок
    ]

    passed = 0
    failed = 0

    for formula, expected in test_cases:
        refs = parse_cell_references(formula)
        # Нормализуем для сравнения
        actual = [(cell.replace('$', ''), sheet) for sheet, cell in refs]
        expected_norm = [(cell.replace('$', ''), sheet) for cell, sheet in expected]

        if set(actual) == set(expected_norm):
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"

        print(f"   {status} {formula}")
        if set(actual) != set(expected_norm):
            print(f"      Ожидалось: {expected_norm}")
            print(f"      Получено: {actual}")

    print(f"\n   Пройдено: {passed}/{len(test_cases)}")

    # ============================================
    # ИТОГОВЫЙ ОТЧЁТ
    # ============================================
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)

    # Считаем общее количество формул в модели для всех листов
    all_formulas = sum(
        len([c for c in data.get('cells', {}).values() if c.get('f')])
        for data in model.values()
    )

    coverage = (total_graph_nodes / all_formulas * 100) if all_formulas > 0 else 0

    print(f"""
    📊 Покрытие модели:
       Всего формул в модели: {all_formulas}
       Формул на листах графа: {total_model_formulas}
       Узлов в графе: {total_graph_nodes}
       Покрытие: {coverage:.1f}%

    ⚠️  ВНИМАНИЕ: Граф содержит только {len(graph_sheets)} из {len(model)} листов!
       Отсутствующие листы: {set(model.keys()) - graph_sheets}
    """)


if __name__ == '__main__':
    audit_graph()
