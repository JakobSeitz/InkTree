from ink.traces.trace_group import TraceGroup
from ink.symbols import get_allowed_symbols, get_small_symbols, get_large_symbols


class PreProcessor:
    @staticmethod
    def scale_formula(trace_groups):
        # scale traces so that 0123456789bdfghijkltβ has a size of 1
        trace_groups_with_large_symbol = [trace_group for trace_group in trace_groups if trace_group.label in get_large_symbols()]
        if len(trace_groups_with_large_symbol) != 0:
            large_symbols_avg_height = PreProcessor.get_avg_height(trace_groups_with_large_symbol)
            if large_symbols_avg_height != 0:
                PreProcessor.scale_trace_groups(trace_groups, 1 / large_symbols_avg_height)
                return

        # if there is no large symbol scale traces that acemnopqrsuvwxyzπαγ has a size of 0,5
        trace_groups_with_small_symbol = [trace_group for trace_group in trace_groups if trace_group.label in get_small_symbols()]
        if len(trace_groups_with_small_symbol) != 0:
            small_symbols_avg_height = PreProcessor.get_avg_height(trace_groups_with_small_symbol)
            if small_symbols_avg_height != 0:
                PreProcessor.scale_trace_groups(trace_groups, 0.5 / small_symbols_avg_height)
                return

        # if there is only one trace_group, scale it so that it fits in a 1x1 square
        if len(trace_groups) == 1:
            PreProcessor.fit_trace_group_to_one_times_one_square(trace_groups[0])
            return

        # if no trace_group contains one of the symbols, scale trace_group so that the total height is 1
        max_y = max([trace_group.get_top() for trace_group in trace_groups])
        min_y = min([trace_group.get_bottom() for trace_group in trace_groups])
        total_height = max_y - min_y
        if total_height != 0:
            PreProcessor.scale_trace_groups(trace_groups, 1 / total_height)

    @staticmethod
    def scale_trace_groups(trace_groups, factor):
        [trace_group.scale(factor, factor) for trace_group in trace_groups]

    @staticmethod
    def normalize(trace_group):
        PreProcessor.fit_trace_group_to_one_times_one_square(trace_group)

    @staticmethod
    def fit_trace_group_to_one_times_one_square(trace_group):
        width, height = trace_group.get_size()
        scale_factor = 1 / max(width, height) if max(width, height) != 0 else 1
        trace_group.scale(scale_factor, scale_factor)
        trace_group_center = trace_group.get_center()
        trace_group.move([- trace_group_center[0], - trace_group_center[1]])

    @staticmethod
    def get_avg_height(trace_groups):
        return sum([trace_group.get_height() for trace_group in trace_groups]) / len(trace_groups)

    @staticmethod
    def preprocess_symbol_trace_groups(trace_groups):
        trace_groups = PreProcessor.remove_empty_trace_groups(trace_groups)
        trace_groups = PreProcessor.remove_unallowed_trace_groups(trace_groups)
        [PreProcessor.fit_trace_group_to_one_times_one_square(trace_group) for trace_group in trace_groups]
        PreProcessor.interpolate_trace_groups(trace_groups, target_length=20)

        return trace_groups

    @staticmethod
    def preprocess_single_trace_group(trace_group):
        PreProcessor.normalize(trace_group)
        trace_group.interpolate(target_point_number=20)
        return trace_group

    @staticmethod
    def create_preprocessed_formula_trace_group(trace_groups):
        trace_groups = PreProcessor.remove_empty_trace_groups(trace_groups)
        PreProcessor.scale_formula(trace_groups)
        PreProcessor.interpolate_trace_groups(trace_groups, target_length=20)
        return trace_groups

    @staticmethod
    def remove_empty_trace_groups(trace_groups):
        for trace_group in trace_groups:
            trace_group.remove_empty_traces()
        return [trace_group for trace_group in trace_groups if len(trace_group) > 0]

    @staticmethod
    def remove_unallowed_trace_groups(trace_groups):
        return [trace_group for trace_group in trace_groups if PreProcessor.is_symbol_allowed(trace_group.label)]

    @staticmethod
    def interpolate_trace_groups(trace_groups: list[TraceGroup], target_length=20):
        [trace_group.interpolate(target_length) for trace_group in trace_groups]

    @staticmethod
    def is_symbol_allowed(latex_str):
        return latex_str in get_allowed_symbols()