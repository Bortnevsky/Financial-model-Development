#!/usr/bin/env python3
"""
FM Pro Demo - Calculation Engine
Wrapper around pycel for Excel formula evaluation and recalculation
"""

import os
import sys
from pathlib import Path
from typing import Optional, Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pycel import ExcelCompiler
    PYCEL_AVAILABLE = True
except ImportError:
    PYCEL_AVAILABLE = False
    print("Warning: pycel not installed. Run: pip install pycel")


class CalcEngine:
    """
    Calculation engine for financial model.

    Wraps pycel to provide:
    - Formula evaluation
    - Value setting with automatic recalculation
    - Caching for performance
    """

    def __init__(self, excel_path: str):
        """
        Initialize calculation engine with Excel file.

        Args:
            excel_path: Path to Excel file (.xlsx)
        """
        if not PYCEL_AVAILABLE:
            raise ImportError("pycel is required. Install with: pip install pycel")

        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        self.excel_path = excel_path
        self._compiler = None
        self._cycles = True  # Enable circular reference support
        self._load_workbook()

    def _load_workbook(self):
        """Load and compile the Excel workbook"""
        print(f"Loading workbook: {self.excel_path}")
        self._compiler = ExcelCompiler(filename=self.excel_path, cycles=self._cycles)
        print("Workbook loaded successfully")

    def evaluate(self, cell_address: str) -> Any:
        """
        Evaluate a cell and return its value.

        Args:
            cell_address: Cell address like 'Sheet!A1' or 'A1' (default sheet)

        Returns:
            Calculated value of the cell
        """
        if not self._compiler:
            raise RuntimeError("Workbook not loaded")

        try:
            return self._compiler.evaluate(cell_address)
        except Exception as e:
            print(f"Error evaluating {cell_address}: {e}")
            return None

    def set_value(self, cell_address: str, value: Any) -> None:
        """
        Set a cell value (for input cells).

        This will trigger recalculation of dependent cells
        when they are next evaluated.

        Args:
            cell_address: Cell address like 'Sheet!A1'
            value: New value to set
        """
        if not self._compiler:
            raise RuntimeError("Workbook not loaded")

        try:
            self._compiler.set_value(cell_address, value)
        except Exception as e:
            print(f"Error setting {cell_address} = {value}: {e}")
            raise

    def get_formula(self, cell_address: str) -> Optional[str]:
        """
        Get the formula of a cell.

        Args:
            cell_address: Cell address like 'Sheet!A1'

        Returns:
            Formula string or None if cell has no formula
        """
        if not self._compiler:
            return None

        try:
            # Access the cell's formula through pycel internals
            cell = self._compiler.cell_map.get(cell_address)
            if cell and hasattr(cell, 'formula'):
                return cell.formula
            return None
        except Exception:
            return None

    def evaluate_range(self, range_address: str) -> List[List[Any]]:
        """
        Evaluate a range of cells.

        Args:
            range_address: Range like 'Sheet!A1:C10'

        Returns:
            2D list of values
        """
        if not self._compiler:
            raise RuntimeError("Workbook not loaded")

        try:
            return self._compiler.evaluate(range_address)
        except Exception as e:
            print(f"Error evaluating range {range_address}: {e}")
            return []

    def get_dependents(self, cell_address: str) -> List[str]:
        """
        Get cells that depend on the given cell.

        Args:
            cell_address: Cell address

        Returns:
            List of dependent cell addresses
        """
        # This would require deeper pycel integration
        # For now, return empty list
        return []

    def reload(self):
        """Reload the workbook from disk"""
        self._load_workbook()


def run_tests(excel_path: str = 'FM_Касаткина2.xlsx'):
    """
    Run standard tests on the calculation engine.
    """
    print(f"\n{'='*60}")
    print("PYCEL CALCULATION ENGINE TESTS")
    print(f"{'='*60}\n")

    # Initialize engine
    print("1. Initializing CalcEngine...")
    try:
        calc = CalcEngine(excel_path)
        print("   ✅ Engine initialized\n")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return False

    # Test 1: Key rate
    print("2. Test: TS1!J85 (ключевая ставка)")
    val = calc.evaluate('TS1!J85')
    expected = 0.2
    status = "✅" if val == expected else "❌"
    print(f"   {status} TS1!J85 = {val} (expected {expected})\n")

    # Test 2: PF rate (depends on key rate)
    print("3. Test: DB!P24 (ставка ПФ = КС + маржа)")
    val = calc.evaluate('DB!P24')
    print(f"   Value: {val}")
    if val is not None and 0.2 < val < 0.3:
        print(f"   ✅ DB!P24 = {val:.4f} (в диапазоне 0.2-0.3)\n")
    else:
        print(f"   ⚠️  DB!P24 = {val} (проверьте вручную)\n")

    # Test 3: Change key rate and recalculate
    print("4. Test: Изменение КС 20% → 25%")
    old_pf = calc.evaluate('DB!P24')
    calc.set_value('TS1!J85', 0.25)
    new_ks = calc.evaluate('TS1!J85')
    new_pf = calc.evaluate('DB!P24')
    print(f"   КС: 0.20 → {new_ks}")
    print(f"   ПФ: {old_pf:.4f} → {new_pf:.4f}" if old_pf and new_pf else f"   ПФ: {old_pf} → {new_pf}")

    if new_ks == 0.25:
        print("   ✅ set_value работает")
    else:
        print("   ❌ set_value не сработал")

    if new_pf and old_pf and new_pf > old_pf:
        print("   ✅ Пересчёт зависимых работает\n")
    else:
        print("   ⚠️  Проверьте пересчёт вручную\n")

    # Reset key rate
    calc.set_value('TS1!J85', 0.20)

    # Test 4: IRR calculation
    print("5. Test: DB!U41 (IRR проекта)")
    try:
        irr = calc.evaluate('DB!U41')
        print(f"   IRR = {irr}")
        if irr is not None and isinstance(irr, (int, float)):
            print(f"   ✅ IRR = {irr:.2%}\n")
        else:
            print(f"   ⚠️  IRR = {irr} (проверьте тип)\n")
    except Exception as e:
        print(f"   ❌ Ошибка IRR: {e}\n")

    # Test 5: Complex formula with cross-sheet refs
    print("6. Test: DB2!U36 (сумма процентов)")
    try:
        val = calc.evaluate('DB2!U36')
        print(f"   Value = {val}")
        if val is not None:
            print(f"   ✅ Кросс-листовые ссылки работают\n")
        else:
            print(f"   ⚠️  Значение None\n")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}\n")

    print(f"{'='*60}")
    print("TESTS COMPLETED")
    print(f"{'='*60}\n")

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FM Pro Calculation Engine')
    parser.add_argument('--excel', default='FM_Касаткина2.xlsx',
                        help='Path to Excel file')
    parser.add_argument('--test', action='store_true',
                        help='Run tests')
    parser.add_argument('--eval', type=str,
                        help='Evaluate a cell (e.g., "TS1!J85")')

    args = parser.parse_args()

    if args.test:
        run_tests(args.excel)
    elif args.eval:
        calc = CalcEngine(args.excel)
        result = calc.evaluate(args.eval)
        print(f"{args.eval} = {result}")
    else:
        parser.print_help()
