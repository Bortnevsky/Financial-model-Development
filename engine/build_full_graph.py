#!/usr/bin/env python3
"""
Build complete dependency graph from pycel by evaluating all formula cells.
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pycel import ExcelCompiler

def build_full_graph(excel_path: str = 'FM_Касаткина2.xlsx', json_path: str = 'fm_model.json'):
    """Force pycel to build complete graph by evaluating all formulas."""

    print(f"Loading {excel_path}...")
    start = time.time()
    calc = ExcelCompiler(filename=excel_path, cycles=True)
    print(f"Loaded in {time.time()-start:.1f}s")

    # Get all formula cells from JSON
    print(f"\nReading formula list from {json_path}...")
    with open(json_path) as f:
        model = json.load(f)

    formula_cells = []
    for sheet, data in model.items():
        for addr, cell in data.get('cells', {}).items():
            if cell.get('f'):
                formula_cells.append(f"{sheet}!{addr}")

    print(f"Found {len(formula_cells)} formula cells")

    # Evaluate ALL to build graph
    print(f"\nEvaluating all formulas to build graph...")
    start = time.time()

    evaluated = 0
    errors = 0
    for i, cell in enumerate(formula_cells):
        try:
            calc.evaluate(cell)
            evaluated += 1
        except Exception:
            errors += 1

        if (i + 1) % 5000 == 0:
            print(f"  Progress: {i+1}/{len(formula_cells)} ({evaluated} ok, {errors} errors)")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s ({evaluated} evaluated, {errors} errors)")

    # Now check the graph
    G = calc.dep_graph
    print(f"\n=== COMPLETE GRAPH ===")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")

    # Find inputs (leaf nodes)
    leaf_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"\nInput cells (no dependencies): {len(leaf_nodes)}")

    # Find outputs (root nodes)
    root_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
    print(f"Output cells (nothing depends on them): {len(root_nodes)}")

    # High-impact nodes
    impacts = sorted([(n, G.out_degree(n)) for n in G.nodes()], key=lambda x: -x[1])
    print(f"\nTop 10 high-impact cells:")
    for node, degree in impacts[:10]:
        print(f"  {node}: {degree} dependents")

    # Test: what depends on key rate?
    key_rate = 'TS1!J85'
    if key_rate in G.nodes():
        import networkx as nx
        descendants = nx.descendants(G, key_rate)
        print(f"\nKey rate ({key_rate}) affects {len(descendants)} cells")

    return calc, G


if __name__ == '__main__':
    calc, G = build_full_graph()

    # Save graph for later use
    import networkx as nx
    print(f"\nSaving graph to fm_graph.gexf...")
    nx.write_gexf(G, 'fm_graph.gexf')
    print("Done! Open in Gephi for visualization.")
