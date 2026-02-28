from ink.traces.trace import Trace


class TraceGroup:
    def __init__(self, traces: list[Trace], label=None, xml_id=None, math_annotation=None):
        self.type = None
        self.traces: list[Trace] = traces
        self.label = label
        self.xml_id = xml_id
        self.math_annotation = math_annotation
        self.prediction_logits = None
        self.label_probability = None
        self.alternative_predictions: list[dict] = []
        self.is_fixed = False

    def __add__(self, other):
        return TraceGroup(self.traces + other.traces)

    def __getitem__(self, item):
        return self.traces[item]

    def __len__(self):
        return len(self.traces)

    def __str__(self):
        return f"TraceGroup: {len(self.traces)} traces" + (f", {self.label}" if self.label is not None else "")

    def __eq__(self, other):
        if other is None:
            return False
        if self.label != other.label:
            return False
        if len(self.traces) != len(other.traces):
            return False
        for i in range(len(self.traces)):
            if self.traces[i] != other.traces[i]:
                return False
        return True

    def __hash__(self):
        return hash(tuple(self.traces))

    def sort(self, key, reverse=False):
        self.traces.sort(key=key, reverse=reverse)

    def set_type(self, type):
        self.type = type

    @staticmethod
    def from_array(array):
        traces = [Trace(array[i][0], array[i][1]) for i in range(len(array))]
        return TraceGroup(traces)

    def add_trace(self, trace):
        self.traces.append(trace)

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def remove_empty_traces(self):
        self.traces = [trace for trace in self.traces if len(trace) > 0]

    def get_center(self):
        return (self.get_left() + self.get_right()) / 2, (self.get_top() + self.get_bottom()) / 2

    def center_at_origin(self):
        self.center_at(0, 0)

    def center_at(self, x, y):
        c1, c2 = self.get_center()
        self.move([x - c1, y - c2])

    def get_left(self):
        return min(trace.get_left() for trace in self.traces)

    def get_right(self):
        return max(trace.get_right() for trace in self.traces)

    def get_top(self):
        return max(trace.get_top() for trace in self.traces)

    def get_bottom(self):
        return min(trace.get_bottom() for trace in self.traces)

    def get_size(self):
        return self.get_width(), self.get_height()

    def get_width(self):
        return self.get_right() - self.get_left()

    def get_height(self):
        return self.get_top() - self.get_bottom()

    def move(self, vector):
        [trace.move(vector) for trace in self.traces]

    def move_x(self, x):
        [trace.move_x(x) for trace in self.traces]

    def move_y(self, y):
        [trace.move_y(y) for trace in self.traces]

    def scale(self, dx, dy):
        [trace.scale(dx, dy) for trace in self.traces]

    def left_align_traces(self):
        left = self.get_left()
        self.move_x(-left)

    def right_align_traces(self):
        right = self.get_right()
        self.move_x(-right)

    def get_trace_by_id(self, inkml_id):
        for trace in self.traces:
            if trace.inkml_id == inkml_id:
                return trace
        return None

    def interpolate(self, target_length):
        [trace.interpolate(target_length) for trace in self.traces]

    def copy(self):
        new_group = TraceGroup([trace.copy() for trace in self.traces], self.label, self.xml_id, self.math_annotation)
        if self.prediction_logits is not None:
            new_group.prediction_logits = self.prediction_logits.copy()
        new_group.label_probability = self.label_probability
        new_group.alternative_predictions = [alt.copy() for alt in self.alternative_predictions]
        new_group.is_fixed = self.is_fixed
        return new_group

    @staticmethod
    def order_trace_groups(trace_groups):
        trace_distance_to_zero = [(tg.get_center()[0] ** 2 + tg.get_center()[1] ** 2) ** 0.5
                                  for tg in trace_groups]
        sorted_indices = sorted(range(len(trace_distance_to_zero)), key=lambda x: trace_distance_to_zero[x])
        return [trace_groups[i] for i in sorted_indices]
