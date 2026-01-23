#!/usr/bin/env python3
"""
FM Pro Demo - Find Input Cells
Identifies cells with values (not formulas) - these are the model inputs.
Also explores pycel's dependency graph for custom calc engine.
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pycel import ExcelCompiler
    PYCEL_AVAILABLE = True
except ImportError:
    PYCEL_AVAILABLE = False


def find_input_cells_from_json(json_path: str = 'fm_model.json') -> dict:
    """
    Find all cells with values (not formulas) from JSON model.

    Returns:
        Dict with structure: {sheet: {address: value}}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        model = json.load(f)

    inputs = defaultdict(dict)
    formulas = defaultdict(dict)
    stats = {
        'total_cells': 0,
        'formula_cells': 0,
        'value_cells': 0,
        'empty_cells': 0,
        'text_cells': 0,
        'numeric_inputs': 0,
        'by_sheet': {}
    }

    for sheet_name, sheet_data in model.items():
        cells = sheet_data.get('cells', {})
        sheet_stats = {'formulas': 0, 'values': 0, 'numeric': 0, 'text': 0}

        for address, cell_data in cells.items():
            stats['total_cells'] += 1

            formula = cell_data.get('f')
            value = cell_data.get('v')

            if formula:
                # Cell has formula - it's calculated, not input
                stats['formula_cells'] += 1
                sheet_stats['formulas'] += 1
                formulas[sheet_name][address] = formula
            elif value is not None:
                # Cell has value but no formula - it's an INPUT
                stats['value_cells'] += 1
                sheet_stats['values'] += 1

                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    stats['numeric_inputs'] += 1
                    sheet_stats['numeric'] += 1
                    inputs[sheet_name][address] = value
                elif isinstance(value, str) and value.strip():
                    stats['text_cells'] += 1
                    sheet_stats['text'] += 1
                    # Store text inputs too, they might be labels or categories
                    inputs[sheet_name][address] = value
            else:
                stats['empty_cells'] += 1

        stats['by_sheet'][sheet_name] = sheet_stats

    return inputs, formulas, stats


def analyze_pycel_graph(excel_path: str = 'FM_Касаткина2.xlsx', json_path: str = 'fm_model.json'):
    """
    Analyze pycel's dependency graph.
    Need to evaluate cells first to build the graph (it's lazy).
    """
    if not PYCEL_AVAILABLE:
        print("pycel not available")
        return None, None

    print(f"\nLoading {excel_path} into pycel...")
    calc = ExcelCompiler(filename=excel_path, cycles=True)

    # Load formulas from JSON to know what cells to evaluate
    print("Loading formula list from JSON...")
    with open(json_path, 'r', encoding='utf-8') as f:
        model = json.load(f)

    # Collect all formula cells
    formula_cells = []
    for sheet_name, sheet_data in model.items():
        cells = sheet_data.get('cells', {})
        for address, cell_data in cells.items():
            if cell_data.get('f'):
                formula_cells.append(f"{sheet_name}!{address}")

    print(f"Found {len(formula_cells)} formula cells")

    # Build graph by evaluating a sample of cells
    # Or we can access the internal cell_map
    print("\nBuilding dependency graph...")

    # Alternative: pycel has internal method to get cell dependencies
    # Let's try to access the graph through cell references
    G = calc.dep_graph

    # The graph is built when we traverse cell dependencies
    # Let's evaluate a few key cells to seed the graph
    test_cells = [
        'TS1!J85',    # Key rate
        'DB!P24',     # PF rate
        'DB!U41',     # IRR
        'CF2!P87',    # Revenue
        'DB2!U36',    # Interest
    ]

    print("Evaluating seed cells to build graph...")
    for cell in test_cells:
        try:
            val = calc.evaluate(cell)
            print(f"  {cell} = {val}")
        except Exception as e:
            print(f"  {cell} - error: {e}")

    print(f"\nGraph after seed evaluation:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    # Now evaluate more cells to expand the graph
    print("\nExpanding graph by evaluating first 1000 formula cells...")
    evaluated = 0
    errors = 0
    for cell_addr in formula_cells[:1000]:
        try:
            calc.evaluate(cell_addr)
            evaluated += 1
        except Exception:
            errors += 1

    print(f"  Evaluated: {evaluated}, Errors: {errors}")
    print(f"\nGraph after expansion:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    if G.number_of_nodes() > 0:
        # Find leaf nodes (no incoming edges) - these are pure INPUTS
        leaf_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
        print(f"\nLeaf nodes (pure inputs, no dependencies): {len(leaf_nodes)}")

        # Find root nodes (no outgoing edges) - these are final OUTPUTS
        root_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
        print(f"Root nodes (final outputs, nothing depends on them): {len(root_nodes)}")

        # Sample of leaf nodes
        print(f"\nSample leaf nodes (inputs):")
        for node in sorted(leaf_nodes)[:20]:
            print(f"  {node}")

        # Find high-impact nodes (many things depend on them)
        node_impact = [(n, G.out_degree(n)) for n in G.nodes()]
        node_impact.sort(key=lambda x: -x[1])

        print(f"\nTop 20 high-impact nodes (many dependents):")
        for node, degree in node_impact[:20]:
            in_deg = G.in_degree(node)
            print(f"  {node}: {degree} dependents (in={in_deg})")

        # Check for specific interesting nodes
        print(f"\nChecking key financial inputs:")
        key_inputs = [
            'TS1!J85',  # ключевая ставка (key rate)
            'DB!R8',    # starting price
            'DB2!R8',   # starting price variant
        ]

        for addr in key_inputs:
            if addr in G.nodes():
                in_deg = G.in_degree(addr)
                out_deg = G.out_degree(addr)
                print(f"  {addr}: in_degree={in_deg}, out_degree={out_deg}")

                # What depends on this node?
                if out_deg > 0:
                    successors = list(G.successors(addr))[:10]
                    print(f"    → depends on it: {successors}")
            else:
                print(f"  {addr}: NOT IN GRAPH (may need more evaluations)")

    return calc, G


def get_recalc_order(G, changed_cells: list):
    """
    Given changed input cells, determine optimal recalculation order.
    Uses topological sort of affected subgraph.
    """
    import networkx as nx

    # Find all cells affected by the changes
    affected = set()
    for cell in changed_cells:
        if cell in G.nodes():
            # All descendants (cells that depend on this one)
            descendants = nx.descendants(G, cell)
            affected.update(descendants)
            affected.add(cell)

    if not affected:
        return []

    # Create subgraph of affected nodes
    subgraph = G.subgraph(affected)

    # Topological sort gives optimal calculation order
    try:
        calc_order = list(nx.topological_sort(subgraph))
        return calc_order
    except nx.NetworkXUnfeasible:
        print("Warning: Cycle detected in affected cells")
        return list(affected)


def main():
    # Part 1: Find inputs from JSON
    print("=" * 60)
    print("FINDING INPUT CELLS (VALUES WITHOUT FORMULAS)")
    print("=" * 60)

    json_path = 'fm_model.json'
    if os.path.exists(json_path):
        inputs, formulas, stats = find_input_cells_from_json(json_path)

        print(f"\nOverall Statistics:")
        print(f"  Total cells: {stats['total_cells']}")
        print(f"  Formula cells: {stats['formula_cells']}")
        print(f"  Value cells (inputs): {stats['value_cells']}")
        print(f"    - Numeric: {stats['numeric_inputs']}")
        print(f"    - Text: {stats['text_cells']}")
        print(f"  Empty cells: {stats['empty_cells']}")

        print(f"\nBy sheet (formulas / values / numeric):")
        for sheet, ss in sorted(stats['by_sheet'].items()):
            print(f"  {sheet}: {ss['formulas']} formulas, {ss['values']} values ({ss['numeric']} numeric)")

        # Find sheets with most numeric inputs (likely parameters/assumptions)
        print(f"\nSheets with most numeric inputs (likely parameters):")
        sheets_by_inputs = [(s, stats['by_sheet'][s]['numeric']) for s in stats['by_sheet']]
        sheets_by_inputs.sort(key=lambda x: -x[1])
        for sheet, count in sheets_by_inputs[:10]:
            if count > 0:
                print(f"  {sheet}: {count} numeric inputs")
    else:
        print(f"JSON model not found: {json_path}")
        formulas = {}

    # Part 2: Analyze pycel graph
    print("\n" + "=" * 60)
    print("ANALYZING PYCEL DEPENDENCY GRAPH")
    print("=" * 60)

    excel_path = 'FM_Касаткина2.xlsx'
    if os.path.exists(excel_path) and PYCEL_AVAILABLE:
        calc, G = analyze_pycel_graph(excel_path, json_path)

        if G and G.number_of_nodes() > 0:
            # Test: what would need recalculation if we change key rate?
            print("\n" + "=" * 60)
            print("SMART RECALCULATION TEST")
            print("=" * 60)

            changed = ['TS1!J85']  # Key rate
            print(f"\nIf we change: {changed}")

            recalc_list = get_recalc_order(G, changed)
            print(f"Cells to recalculate: {len(recalc_list)}")

            if recalc_list:
                print(f"\nFirst 20 in calculation order:")
                for i, cell in enumerate(recalc_list[:20]):
                    print(f"  {i+1}. {cell}")

                if len(recalc_list) > 20:
                    print(f"\n... and {len(recalc_list) - 20} more cells")
    else:
        if not os.path.exists(excel_path):
            print(f"Excel file not found: {excel_path}")
        if not PYCEL_AVAILABLE:
            print("pycel not installed")


if __name__ == '__main__':
    main()
