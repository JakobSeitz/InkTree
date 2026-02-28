from ink.nodes.relation_node import RelationNode


def finalize_graph(graph: RelationNode) -> RelationNode:
    if graph is None:
        return None
    for node in graph.get_all_nodes():
        if hasattr(node, "fill_placeholders"):
            node.fill_placeholders()
    graph.fix()
    return graph
