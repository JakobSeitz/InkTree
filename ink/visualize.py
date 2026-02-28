import matplotlib.pyplot as plt

from ink.nodes.lines_node import LineNode
from ink.graph import get_relation_graphs_from_files
from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from datasets.crohme import CrohmeFileManager

import numpy as np

np.random.seed(0)
colors = np.random.rand(50, 3)

class TraceVisualizer:
    @staticmethod
    def plot_trace(trace, mask_value=None, draw_line=True):
        if mask_value is None: color = None
        else:
            if mask_value >= len(colors): print(f"Mask value {mask_value} is too high, using modulo {mask_value % len(colors)}")
            mask_value = int(mask_value) % len(colors)
            color = colors[mask_value]
        if draw_line: plt.plot(trace.x, trace.y, marker='.', linestyle='-', color=color)
        else: plt.scatter(trace.x, trace.y, marker='.', color=color)

    @staticmethod
    def plot_traces(traces, title=None, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        for trace in traces:
            ax.plot(trace.x, trace.y)
        ax.set_aspect("equal")
        ax.invert_yaxis()
        ax.axis("off")
        if title:
            ax.set_title(title)

    @staticmethod
    def plot_trace_groups(trace_groups: list[TraceGroup], title=None):
        plt.figure(figsize=(8, 6))
        mask_value = 0
        for trace_group in trace_groups:
            mask_value += 1
            for trace in trace_group:
                TraceVisualizer.plot_trace(trace, mask_value % len(colors))
        TraceVisualizer.finalize_plot(title)

    @staticmethod
    def plot_trace_group(trace_group: TraceGroup, title=None, ax=None):
        if title is None:
            if trace_group.label == "\\lt": title = f"$<$"
            elif trace_group.label == "\\gt": title = f"$>$"
            elif trace_group.label == "\\sqrt": title = f"$\\sqrt{{\u25A1}}$"
            else: title = f"${trace_group.label}$"
        TraceVisualizer.plot_traces(trace_group.traces, title=title, ax=ax)

    @staticmethod
    def plot_trace_group_with_mask(trace_group, mask, title=None):
        if title is None:
            if trace_group.label == "\\lt": title = f"$<$"
            elif trace_group.label == "\\gt": title = f"$>$"
            elif trace_group.label == "\\sqrt": title = f"$\\sqrt{{\u25A1}}$"
            else: title = f"${trace_group.label}$"
        plt.figure(figsize=(8, 6))
        for trace, mask_value in zip(trace_group, mask):
            TraceVisualizer.plot_trace(trace, mask_value)
        TraceVisualizer.finalize_plot(title)

    @staticmethod
    def plot_trace_groups_with_mask(trace_groups, mask, title=None):
        plt.figure(figsize=(8, 6))
        for trace_group, mask_value in zip(trace_groups, mask):
            for trace in trace_group:
                TraceVisualizer.plot_trace(trace, mask_value)
        TraceVisualizer.finalize_plot(title)

    @staticmethod
    def finalize_plot(title=None, show=True):
        plt.gca().set_aspect('equal', adjustable='box')
        plt.gca().invert_yaxis()
        plt.title(title)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid(True)
        if show:
            plt.show()

    @staticmethod
    def plot_relation_graph(relation_graph, plot_arrows=True):
        relation_graph = relation_graph.copy() # make sure we don't change the original graph
        mask_value = 0
        plt.figure(figsize=(8, 6))
        nodes_with_tgs = relation_graph.get_all_nodes_with_trace_groups()
        for node in nodes_with_tgs:
            mask_value += 1
            for trace in node.trace_group:
                TraceVisualizer.plot_trace(trace, mask_value % len(colors))
            if plot_arrows:
                above = node.get_above()
                sup = node.get_sup()
                right = node.get_right()
                sub = node.get_sub()
                below = node.get_below()
                above = above.get_leftmost_node().get_all_trace_groups() if above is not None else []
                sup = sup.get_leftmost_node().get_all_trace_groups() if sup is not None else []
                right = right.get_leftmost_node().get_all_trace_groups() if right is not None else []
                sub = sub.get_leftmost_node().get_all_trace_groups() if sub is not None else []
                below = below.get_leftmost_node().get_all_trace_groups() if below is not None else []

                for tg in above + sup + right + sub + below:
                    color = 'black'
                    if tg in above:
                        color = 'red'
                    elif tg in sup:
                        color = 'green'
                    elif tg in right:
                        color = 'blue'
                    elif tg in sub:
                        color = 'yellow'
                    elif tg in below:
                        color = 'purple'
                    plt.arrow(
                        node.trace_group.get_center()[0],
                        node.trace_group.get_center()[1],
                        tg.get_center()[0] - node.trace_group.get_center()[0],
                        tg.get_center()[1] - node.trace_group.get_center()[1],
                        color=color,
                        head_width=.1,
                        zorder=5
                    )

        # add legend to the plot
        if plot_arrows:
            plt.plot([], [], color='red', label='above')
            plt.plot([], [], color='green', label='sup')
            plt.plot([], [], color='blue', label='right')
            plt.plot([], [], color='yellow', label='sub')
            plt.plot([], [], color='purple', label='below')
            plt.legend( loc='lower center', bbox_to_anchor=(0.5, -0.5), ncol=5, fontsize='small')
        latex = relation_graph.latex()
        if isinstance(relation_graph, LineNode): TraceVisualizer.finalize_plot(f"{latex}", show=False)
        else: TraceVisualizer.finalize_plot(f"${latex}$", show=False)
        try:
            plt.subplots_adjust(top=0.75)
            plt.show()
        except:
            title=relation_graph.as_pretty_formula()
            plt.title(title, wrap=True)
            plt.subplots_adjust(top=0.75)
            plt.show()

    @staticmethod
    def plot_relation_graph_alt(relation_graph, title, plot_arrows=True):
        relation_graph = relation_graph.copy()  # make sure we don't change the original graph
        mask_value = 0
        plt.figure(figsize=(8, 6))
        nodes_with_tgs = relation_graph.get_all_nodes_with_trace_groups()
        for node in nodes_with_tgs:
            mask_value += 1
            for trace in node.trace_group:
                TraceVisualizer.plot_trace(trace, mask_value % len(colors))
            if plot_arrows:
                above = node.get_above()
                sup = node.get_sup()
                right = node.get_right()
                sub = node.get_sub()
                below = node.get_below()
                above = above.get_leftmost_node().get_all_trace_groups() if above is not None else []
                sup = sup.get_leftmost_node().get_all_trace_groups() if sup is not None else []
                right = right.get_leftmost_node().get_all_trace_groups() if right is not None else []
                sub = sub.get_leftmost_node().get_all_trace_groups() if sub is not None else []
                below = below.get_leftmost_node().get_all_trace_groups() if below is not None else []

                for tg in above + sup + right + sub + below:
                    color = 'black'
                    if tg in above:
                        color = 'red'
                    elif tg in sup:
                        color = 'green'
                    elif tg in right:
                        color = 'blue'
                    elif tg in sub:
                        color = 'yellow'
                    elif tg in below:
                        color = 'purple'
                    plt.arrow(
                        node.trace_group.get_center()[0],
                        node.trace_group.get_center()[1],
                        tg.get_center()[0] - node.trace_group.get_center()[0],
                        tg.get_center()[1] - node.trace_group.get_center()[1],
                        color=color,
                        head_width=.1,
                        zorder=5
                    )

        # add legend to the plot
        if plot_arrows:
            plt.plot([], [], color='red', label='above')
            plt.plot([], [], color='green', label='sup')
            plt.plot([], [], color='blue', label='right')
            plt.plot([], [], color='yellow', label='sub')
            plt.plot([], [], color='purple', label='below')
            plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.5), ncol=5, fontsize='small')
        latex = relation_graph.latex()
        if isinstance(relation_graph, LineNode):
            TraceVisualizer.finalize_plot(title, show=False)
        else:
            TraceVisualizer.finalize_plot(title, show=False)
        try:
            plt.show()
        except:
            title = relation_graph.as_pretty_formula()
            plt.title(title)
            plt.show()

if __name__ == '__main__':
    files = CrohmeFileManager.get_artificial_train_files()[:100]
    graph = get_relation_graphs_from_files(files, keep_undefined=True)
    TraceVisualizer.plot_relation_graph(graph[5])
    tgs = graph[5].get_all_trace_groups()
    # for tg in tgs:
    #     TraceVisualizer.plot_trace_group(tg)
