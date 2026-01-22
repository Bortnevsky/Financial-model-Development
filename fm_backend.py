#!/usr/bin/env python3
"""
Financial Model Backend - Function implementations for Claude API
Provides data access to FM_Касаткина2.xlsx via JSON export
"""

import json
import re
from typing import Optional, Dict, Any, List

# Load data on module import
with open("fm_kasatkina_full.json", "r", encoding="utf-8") as f:
    FM_DATA = json.load(f)

with open("fm_kasatkina_summary.json", "r", encoding="utf-8") as f:
    FM_SUMMARY = json.load(f)


def get_cell(sheet: str, cell: str) -> Dict[str, Any]:
    """Get value and formula for a specific cell"""
    if sheet not in FM_DATA["sheets"]:
        return {"error": f"Sheet '{sheet}' not found. Available: {list(FM_DATA['sheets'].keys())}"}

    cell = cell.upper()
    cells = FM_DATA["sheets"][sheet]["cells"]

    if cell not in cells:
        return {"error": f"Cell {cell} not found in sheet {sheet}"}

    return {
        "sheet": sheet,
        "cell": cell,
        **cells[cell]
    }


def get_range(sheet: str, start_cell: str, end_cell: str) -> Dict[str, Any]:
    """Get values for a range of cells"""
    if sheet not in FM_DATA["sheets"]:
        return {"error": f"Sheet '{sheet}' not found"}

    # Parse cell references
    def parse_cell(ref):
        match = re.match(r'([A-Z]+)(\d+)', ref.upper())
        if not match:
            return None, None
        col = match.group(1)
        row = int(match.group(2))
        return col, row

    def col_to_num(col):
        num = 0
        for c in col:
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num

    def num_to_col(num):
        col = ""
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            col = chr(65 + remainder) + col
        return col

    start_col, start_row = parse_cell(start_cell)
    end_col, end_row = parse_cell(end_cell)

    if not start_col or not end_col:
        return {"error": "Invalid cell reference format"}

    cells = FM_DATA["sheets"][sheet]["cells"]
    result = {}

    for row in range(start_row, end_row + 1):
        for col_num in range(col_to_num(start_col), col_to_num(end_col) + 1):
            col = num_to_col(col_num)
            cell = f"{col}{row}"
            if cell in cells:
                result[cell] = cells[cell]

    return {
        "sheet": sheet,
        "range": f"{start_cell}:{end_cell}",
        "cells": result,
        "count": len(result)
    }


def get_summary() -> Dict[str, Any]:
    """Get project summary with key metrics"""
    return FM_SUMMARY


def search_cells(query: str, sheet: Optional[str] = None) -> Dict[str, Any]:
    """Search for cells containing specific text or value"""
    results = []
    query_lower = query.lower()

    sheets_to_search = [sheet] if sheet else FM_DATA["sheets"].keys()

    for sheet_name in sheets_to_search:
        if sheet_name not in FM_DATA["sheets"]:
            continue
        cells = FM_DATA["sheets"][sheet_name]["cells"]

        for cell_ref, cell_data in cells.items():
            val = cell_data.get("value")
            formula = cell_data.get("formula", "")

            if val and query_lower in str(val).lower():
                results.append({
                    "sheet": sheet_name,
                    "cell": cell_ref,
                    **cell_data
                })
            elif formula and query_lower in formula.lower():
                results.append({
                    "sheet": sheet_name,
                    "cell": cell_ref,
                    **cell_data
                })

            if len(results) >= 50:  # Limit results
                break

        if len(results) >= 50:
            break

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "truncated": len(results) >= 50
    }


def explain_formula(sheet: str, cell: str) -> Dict[str, Any]:
    """Get formula and explain what it calculates"""
    cell_data = get_cell(sheet, cell)

    if "error" in cell_data:
        return cell_data

    if "formula" not in cell_data:
        return {
            "sheet": sheet,
            "cell": cell,
            "value": cell_data.get("value"),
            "note": "This cell contains a static value, not a formula"
        }

    formula = cell_data["formula"]

    # Parse formula to identify dependencies
    dependencies = []

    # Find sheet references like 'SheetName'!A1
    sheet_refs = re.findall(r"'([^']+)'!([A-Z]+\d+)", formula)
    for ref_sheet, ref_cell in sheet_refs:
        dependencies.append({"sheet": ref_sheet, "cell": ref_cell})

    # Find simple cell references like A1, B5
    simple_refs = re.findall(r"\b([A-Z]+\d+)\b", formula)
    for ref in simple_refs:
        dependencies.append({"sheet": sheet, "cell": ref})

    return {
        "sheet": sheet,
        "cell": cell,
        "formula": formula,
        "value": cell_data.get("value"),
        "dependencies": dependencies[:20]  # Limit
    }


def get_cashflow_period(period: str, очередь: Optional[int] = None) -> Dict[str, Any]:
    """Get cash flow data for a specific period"""
    # Period columns in CF sheets start from F (2Q2023)
    # We need to find the column for the requested period

    target_sheet = f"CF{очередь}" if очередь else "CF"

    if target_sheet not in FM_DATA["sheets"]:
        return {"error": f"Sheet {target_sheet} not found"}

    cells = FM_DATA["sheets"][target_sheet]["cells"]

    # Find period column by searching row 7 (period headers)
    period_col = None
    for col_ord in range(ord('F'), ord('Z') + 1):
        col = chr(col_ord)
        cell_ref = f"{col}7"
        if cell_ref in cells:
            if cells[cell_ref].get("value") == period:
                period_col = col
                break

    if not period_col:
        # Try extended columns AA-BN
        for col_ord in range(26, 68):
            col = ('A' if col_ord >= 26 else '') + chr(ord('A') + (col_ord % 26))
            cell_ref = f"{col}7"
            if cell_ref in cells:
                if cells[cell_ref].get("value") == period:
                    period_col = col
                    break

    if not period_col:
        return {"error": f"Period {period} not found in {target_sheet}"}

    # Extract key CF rows for that period
    key_rows = {
        8: "Выручка",
        20: "Инвестиции (всего)",
        65: "СМР жилье",
        100: "Сальдо"
    }

    result = {
        "period": period,
        "очередь": очередь,
        "sheet": target_sheet,
        "data": {}
    }

    for row, name in key_rows.items():
        cell_ref = f"{period_col}{row}"
        if cell_ref in cells:
            result["data"][name] = cells[cell_ref].get("value")

    return result


def get_cost_breakdown(статья: str, очередь: Optional[int] = None) -> Dict[str, Any]:
    """Get breakdown of costs by статья from DETAILS sheet"""
    cells = FM_DATA["sheets"]["DETAILS"]["cells"]

    results = []

    # DETAILS structure: B=статья, C=очередь, D=содержание, E=организация, F=контрагент
    for row in range(5, 420):
        b_cell = f"B{row}"
        if b_cell in cells:
            cell_статья = str(cells[b_cell].get("value", ""))
            if статья in cell_статья:
                row_data = {
                    "row": row,
                    "статья": cell_статья
                }

                # Get очередь (column C)
                if f"C{row}" in cells:
                    row_data["очередь"] = cells[f"C{row}"].get("value")

                # Filter by очередь if specified
                if очередь and row_data.get("очередь") != очередь:
                    continue

                # Get содержание (column D)
                if f"D{row}" in cells:
                    row_data["содержание"] = cells[f"D{row}"].get("value")

                # Get организация (column E)
                if f"E{row}" in cells:
                    row_data["организация"] = cells[f"E{row}"].get("value")

                # Get контрагент (column F)
                if f"F{row}" in cells:
                    row_data["контрагент"] = cells[f"F{row}"].get("value")

                # Get sum (column J typically has totals)
                if f"J{row}" in cells:
                    row_data["сумма"] = cells[f"J{row}"].get("value")

                results.append(row_data)

    return {
        "статья": статья,
        "очередь": очередь,
        "count": len(results),
        "items": results[:50]  # Limit
    }


def get_fact_payments(
    period: Optional[str] = None,
    контрагент: Optional[str] = None,
    статья: Optional[str] = None
) -> Dict[str, Any]:
    """Get actual (fact) payments from FACT sheet"""
    cells = FM_DATA["sheets"]["FACT"]["cells"]

    results = []

    # FACT structure: A=статья, B=сумма, C=период, H=контрагент
    for row in range(2, 200):
        # Get row data
        row_data = {}

        # Статья (A)
        if f"A{row}" in cells:
            row_data["статья"] = cells[f"A{row}"].get("value")
        else:
            continue

        # Filter by статья
        if статья and статья not in str(row_data.get("статья", "")):
            continue

        # Сумма (B)
        if f"B{row}" in cells:
            row_data["сумма"] = cells[f"B{row}"].get("value")

        # Период (C)
        if f"C{row}" in cells:
            row_data["период"] = cells[f"C{row}"].get("value")

        # Filter by period
        if period and row_data.get("период") != period:
            continue

        # Контрагент (I based on earlier analysis)
        if f"I{row}" in cells:
            row_data["контрагент"] = cells[f"I{row}"].get("value")

        # Filter by контрагент
        if контрагент and контрагент.lower() not in str(row_data.get("контрагент", "")).lower():
            continue

        # НазначениеПлатежа (O)
        if f"O{row}" in cells:
            row_data["назначение"] = cells[f"O{row}"].get("value")

        results.append(row_data)

    return {
        "filters": {
            "period": period,
            "контрагент": контрагент,
            "статья": статья
        },
        "count": len(results),
        "total": sum(r.get("сумма", 0) or 0 for r in results if isinstance(r.get("сумма"), (int, float))),
        "payments": results[:100]  # Limit
    }


# Function dispatcher for Claude API
def execute_function(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function by name with given arguments"""
    functions = {
        "get_cell": get_cell,
        "get_range": get_range,
        "get_summary": get_summary,
        "search_cells": search_cells,
        "explain_formula": explain_formula,
        "get_cashflow_period": get_cashflow_period,
        "get_cost_breakdown": get_cost_breakdown,
        "get_fact_payments": get_fact_payments
    }

    if name not in functions:
        return {"error": f"Unknown function: {name}"}

    return functions[name](**arguments)


if __name__ == "__main__":
    # Test functions
    print("=== Testing FM Backend ===\n")

    print("1. get_summary():")
    print(json.dumps(get_summary()["key_metrics"], ensure_ascii=False, indent=2))

    print("\n2. get_cell('DB', 'C2'):")
    print(json.dumps(get_cell("DB", "C2"), ensure_ascii=False, indent=2))

    print("\n3. explain_formula('CF1', 'Q65'):")
    print(json.dumps(explain_formula("CF1", "Q65"), ensure_ascii=False, indent=2))

    print("\n4. search_cells('СМР'):")
    result = search_cells("СМР", "DB")
    print(f"Found {result['count']} cells")

    print("\n5. get_cost_breakdown('5401'):")
    result = get_cost_breakdown("5401")
    print(f"Found {result['count']} items for статья 5401")
