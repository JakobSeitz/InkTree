"""
Load InkML files into RelationNode graphs.

Public API:
    load_inkml_file(file, ...)   -> RelationNode | None
    load_inkml_files(files, ...) -> list[RelationNode]
"""

import os
from tqdm import tqdm

from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.relation_node import RelationNode
from ink.inkml import InkmlProcessor
from ink.preprocess import PreProcessor


def get_relation_graph_from_file(file, print_errors=False, scale=True, interpolate=True,
                                  keep_undefined=False):
    try:
        proc = InkmlProcessor(file)
    except Exception as e:
        if print_errors:
            print(f"[ink.graph] Error loading {os.path.basename(file)}: {e}")
        return None

    traces = proc.extract_traces()
    trace_groups = proc.group_traces_by_trace_groups(traces)
    trace_groups = PreProcessor.remove_empty_trace_groups(trace_groups)
    if not trace_groups:
        if print_errors:
            print(f"[ink.graph] No trace groups in {os.path.basename(file)}")
        return None

    if scale:
        PreProcessor.scale_formula(trace_groups)
    if interpolate:
        PreProcessor.interpolate_trace_groups(trace_groups, target_length=20)

    try:
        graph = proc.get_relation_graph(trace_groups, print_errors=print_errors)
    except Exception as e:
        if print_errors:
            print(f"[ink.graph] Error building graph for {os.path.basename(file)}: {e}")
        return None

    if graph is None:
        return None

    graph.fix()

    if not keep_undefined and graph.contains_undefined_relations():
        return None

    return graph


def get_relation_graphs_from_files(files, print_errors=False, scale=True, interpolate=True,
                                    keep_undefined=False):
    graphs: list[RelationNode] = []
    for file in tqdm(files):
        g = get_relation_graph_from_file(file, print_errors=print_errors, scale=scale,
                                          interpolate=interpolate, keep_undefined=keep_undefined)
        if g is not None:
            graphs.append(g)
    return graphs


# Public API aliases
load_inkml_file  = get_relation_graph_from_file
load_inkml_files = get_relation_graphs_from_files
