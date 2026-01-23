#!/usr/bin/env python3
"""
FM Pro Demo - Wave Distribution Engine

Distributes delta across periods when user changes a single cell.

Example:
    User changes July sales: 8208 → 500 m²
    Delta = +7708 m² to redistribute
    Other months get proportionally increased to keep total
"""

from typing import Dict, List, Optional, Literal
import math

WaveMethod = Literal['proportional', 'uniform', 'tail', 's_curve']


def apply_wave(
    values: Dict[str, float],
    changed_key: str,
    new_value: float,
    method: WaveMethod = 'proportional',
    preserve_total: bool = True
) -> Dict[str, float]:
    """
    Apply wave distribution to a row of values.

    Args:
        values: Dict of {period: value}, e.g. {'янв': 100, 'фев': 200, ...}
        changed_key: Which period was changed
        new_value: New value for that period
        method: Distribution algorithm
        preserve_total: If True, redistribute to keep sum constant
                       If False, only change the single cell

    Returns:
        New dict with redistributed values
    """
    if changed_key not in values:
        raise ValueError(f"Key '{changed_key}' not in values")

    old_value = values[changed_key]
    delta = old_value - new_value  # positive = freed up, negative = taken

    if not preserve_total or delta == 0:
        # Just change the single cell
        result = values.copy()
        result[changed_key] = new_value
        return result

    # Get other keys (excluding changed one)
    other_keys = [k for k in values.keys() if k != changed_key]
    other_values = {k: values[k] for k in other_keys}

    if not other_keys:
        # Only one cell, can't distribute
        result = values.copy()
        result[changed_key] = new_value
        return result

    # Distribute delta according to method
    if method == 'proportional':
        distributed = _distribute_proportional(other_values, delta)
    elif method == 'uniform':
        distributed = _distribute_uniform(other_values, delta)
    elif method == 'tail':
        distributed = _distribute_tail(other_values, delta)
    elif method == 's_curve':
        distributed = _distribute_s_curve(other_values, delta)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Build result
    result = distributed.copy()
    result[changed_key] = new_value

    return result


def _distribute_proportional(values: Dict[str, float], delta: float) -> Dict[str, float]:
    """
    Distribute delta proportionally by weight of each period.

    If янв=100, фев=200, мар=300 (total=600) and delta=60:
    - янв gets 60 * (100/600) = 10
    - фев gets 60 * (200/600) = 20
    - мар gets 60 * (300/600) = 30
    """
    total = sum(values.values())

    if total == 0:
        # All zeros - fall back to uniform
        return _distribute_uniform(values, delta)

    result = {}
    for key, val in values.items():
        weight = val / total if total != 0 else 0
        result[key] = val + delta * weight

    return result


def _distribute_uniform(values: Dict[str, float], delta: float) -> Dict[str, float]:
    """
    Distribute delta equally to all periods.
    """
    count = len(values)
    per_period = delta / count if count > 0 else 0

    return {k: v + per_period for k, v in values.items()}


def _distribute_tail(values: Dict[str, float], delta: float) -> Dict[str, float]:
    """
    Put all delta into the last period.
    """
    result = values.copy()
    keys = list(values.keys())
    if keys:
        last_key = keys[-1]
        result[last_key] = values[last_key] + delta
    return result


def _distribute_s_curve(values: Dict[str, float], delta: float) -> Dict[str, float]:
    """
    Distribute using S-curve (sigmoid) - more in the middle.
    """
    keys = list(values.keys())
    n = len(keys)

    if n == 0:
        return values.copy()

    # Generate S-curve weights (sigmoid centered at middle)
    weights = []
    for i in range(n):
        # Normalize position to [-3, 3] range for sigmoid
        x = (i - (n - 1) / 2) / max(1, (n - 1) / 6)
        # Inverted sigmoid - peak in the middle
        w = 1 / (1 + math.exp(-x)) * (1 - 1 / (1 + math.exp(-x))) * 4
        weights.append(max(0.01, w))  # minimum weight

    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    # Apply
    result = {}
    for i, key in enumerate(keys):
        result[key] = values[key] + delta * weights[i]

    return result


def preview_wave(
    values: Dict[str, float],
    changed_key: str,
    new_value: float,
    method: WaveMethod = 'proportional'
) -> Dict[str, Dict]:
    """
    Preview wave distribution without applying.

    Returns:
        Dict with 'before', 'after', 'delta' for each period
    """
    after = apply_wave(values, changed_key, new_value, method, preserve_total=True)

    result = {}
    for key in values.keys():
        result[key] = {
            'before': values[key],
            'after': after[key],
            'delta': after[key] - values[key]
        }

    # Add totals
    result['_total'] = {
        'before': sum(values.values()),
        'after': sum(after.values()),
        'delta': sum(after.values()) - sum(values.values())
    }

    return result


def apply_wave_to_row(
    sheet: str,
    row_num: int,
    changed_col: int,
    new_value: float,
    method: WaveMethod = 'proportional',
    col_start: int = 6,  # F
    col_end: int = 65,   # BM
    version_id: int = 1,
    db_path: str = 'fm_demo.db'
) -> Dict[str, float]:
    """
    Apply wave distribution to a database row.

    Args:
        sheet: Sheet name
        row_num: Row number
        changed_col: Column that was changed (1-based)
        new_value: New value for that column
        method: Distribution method
        col_start, col_end: Column range for periods
        version_id: Version ID
        db_path: Database path

    Returns:
        Dict with new values for all columns
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from db.queries import get_sheet_data, set_override, num_to_col

    # Get row data
    cells = get_sheet_data(
        sheet=sheet,
        version_id=version_id,
        db_path=db_path,
        row_start=row_num,
        row_end=row_num,
        col_start=col_start,
        col_end=col_end
    )

    if not cells:
        return {}

    # Build values dict {col_num: value}
    values = {}
    for cell in cells:
        col = cell['col_num']
        val = cell['final_value'] or 0
        values[col] = val

    # Apply wave
    changed_key = changed_col
    new_values = apply_wave(values, changed_key, new_value, method)

    # Save to DB as overrides
    for col, val in new_values.items():
        address = f"{num_to_col(col)}{row_num}"
        set_override(sheet, address, val, reason=f"wave_{method}")

    return new_values


# CLI for testing
if __name__ == '__main__':
    print("=== ТЕСТ WAVE DISTRIBUTION ===\n")

    # Test data: продажи по месяцам
    sales = {
        'янв': 1000,
        'фев': 1500,
        'мар': 2000,
        'апр': 2500,
        'май': 3000,
        'июн': 3500,
        'июл': 8208,  # ← меняем на 500
        'авг': 3000,
        'сен': 2500,
        'окт': 2000,
        'ноя': 1500,
        'дек': 1000,
    }

    print(f"Исходные данные:")
    print(f"  Сумма: {sum(sales.values()):,.0f}")
    print(f"  Июль: {sales['июл']:,.0f}")

    print(f"\nМеняем июль: 8208 → 500 (дельта +7708 к распределению)")

    for method in ['proportional', 'uniform', 'tail', 's_curve']:
        result = apply_wave(sales, 'июл', 500, method)
        print(f"\n{method.upper()}:")
        print(f"  Сумма: {sum(result.values()):,.0f}")
        print(f"  Июль: {result['июл']:,.0f}")
        changes = {k: result[k] - sales[k] for k in sales if k != 'июл'}
        top3 = sorted(changes.items(), key=lambda x: -abs(x[1]))[:3]
        print(f"  Топ изменения: {', '.join(f'{k}: +{v:.0f}' for k, v in top3)}")
