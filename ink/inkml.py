import xml.etree.ElementTree as ET

import numpy as np

from ink.nodes.node_utils import finalize_graph
from ink.nodes.frac_node import FracNode
from ink.nodes.row_node import RowNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.sub_node import SubNode
from ink.nodes.sup_node import SupNode
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.nodes_factory import create_relation_node, get_undefined_node_from_trace_groups
from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup


class InkmlProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.root = self.load_inkml_file(file_path)

    def __str__(self):
        return f"InkmlProcessor: {self.file_path} ({self.get_annotation_text()})"

    def load_inkml_file(self, file_path):
        """Load and parse an INKML file and return the root element."""
        root = ET.parse(file_path).getroot()
        # check if root is ink element
        if root.tag.split('}')[1] != 'ink':
            raise ValueError(f"File {file_path} is not an INKML file")
        return root

    def get_namespaces(self):
        """Get the namespaces from the root element."""
        namespace = self.root.tag.split('}')[0][1:]
        return {'inkml': namespace,
                'math': 'http://www.w3.org/1998/Math/MathML',
                'xml': "http://www.w3.org/XML/1998/namespace"}

    def extract_traces(self):
        """Extract ink data from the INKML root element and return a list of traces."""
        namespaces = self.get_namespaces()
        trace_group = TraceGroup([])

        for trace in self.root.findall(f'.//inkml:trace', namespaces):
            points = [list(map(float, point.split())) for point in trace.text.strip().split(',')]

            if len(points[0]) == 3:
                x, y, t = zip(*points)
            else:
                x, y = zip(*points)
                t = None
            trace_group.add_trace(Trace(x=x, y=y, t=t, inkml_id=int(trace.get('id'))))

        return trace_group

    def group_traces_by_trace_groups(self, ungrouped_trace_group, print_errors=False):
        namespaces = self.get_namespaces()
        trace_groups = []

        # we want to skip the first tracegroup because it is the entire equation
        first_iteration = True

        for inkml_trace_group in self.root.findall(f'.//inkml:traceGroup', namespaces):
            if first_iteration:
                first_iteration = False
                continue
            xml_id = inkml_trace_group.get("{" + namespaces["xml"] + "}id")  # TODO: this can probably be solved cleaner
            xml_id = int(xml_id) if xml_id.isnumeric() else None

            math_annotation = inkml_trace_group.find("inkml:annotationXML", namespaces)
            math_annotation = math_annotation.get("href") if math_annotation is not None else None

            label = inkml_trace_group.find(f'.//inkml:annotation[@type="truth"]', namespaces).text

            trace_group = TraceGroup([], label=label, xml_id=xml_id, math_annotation=math_annotation)
            for traceview in inkml_trace_group.findall(f'.//inkml:traceView', namespaces):
                trace_id = int(traceview.get('traceDataRef'))

                trace = ungrouped_trace_group.get_trace_by_id(trace_id)
                if trace is None:
                    if print_errors: print(f"Theres no trace for ID {trace_id} in file {self.file_path}")
                    continue
                trace_group.add_trace(trace)
            trace_groups.append(trace_group)

        return trace_groups

    def get_annotation_text(self):
        namespaces = self.get_namespaces()
        # Erst im Root suchen
        ann = self.root.find("./inkml:annotation[@type='truth']", namespaces)
        return "Kein Label" if ann is None else ann.text

    def get_channel_attributes(self):
        namespaces = self.get_namespaces()
        trace_format = self.root.find("./inkml:traceFormat", namespaces)
        if trace_format is None:
            return None
        channels = trace_format.findall("./inkml:channel", namespaces)
        attributes = [channel.attrib for channel in channels]
        return attributes

    # returns a dictionary containing type and annotation content
    def get_annotations(self) -> dict:
        namespaces = self.get_namespaces()
        annotations = self.root.findall("./inkml:annotation", namespaces)
        return {annotation.get("type"): annotation.text for annotation in annotations}

    # get relation graph and adds the type extracted from the annoationXML to the trace_groups
    def get_relation_graph(self, trace_groups, print_errors=True):
        if any([trace_group.math_annotation is None for trace_group in trace_groups]):
            if print_errors:
                print(f"Error: Not all trace groups have a math annotation in {self.file_path}")
            return get_undefined_node_from_trace_groups(trace_groups, latex=self.get_annotation_text())

        trace_groups_dict = {trace_group.math_annotation: trace_group for trace_group in trace_groups}

        namespaces = self.get_namespaces()
        annotationXML = self.root.find(".//inkml:annotationXML", namespaces)
        if annotationXML is None:
            if print_errors:
                print(
                    f"Error: No annotationXML found in {self.file_path}")  # some files have no annotationXML element (seems to ba a problem with files from 2003)
            return get_undefined_node_from_trace_groups(trace_groups, latex=self.get_annotation_text())

        math = annotationXML.find("math:math", namespaces)
        if math is None:
            math = annotationXML.find("inkml:math", namespaces) # in some cases the math namespace is not used
        if math is None:
            if print_errors:
                print(
                    f"Error: No math element found in {self.file_path}")  # some files have no math element (seems to ba a problem with files from 2003)
            return get_undefined_node_from_trace_groups(trace_groups, latex=self.get_annotation_text())

        id_attribute = "{" + namespaces["xml"] + "}" + "id"

        inkml_to_node = {}
        root = None
        to_process = [c for c in math]
        if len(to_process) == 0:
            if print_errors:
                print(f"Error: No children found in math element in file {self.file_path}")
            return get_undefined_node_from_trace_groups(trace_groups, latex=self.get_annotation_text())
        if len(to_process) > 1:
            # add a mrow root
            root = create_relation_node("mrow")
            for child in to_process:
                child.set("parent", math)
            inkml_to_node[math] = root
        while len(to_process) > 0:
            current = to_process.pop(0)
            for child in current:
                child.set("parent", current)
                to_process.append(child)
            type = current.tag.split("}")[1]

            parent = current.get("parent")
            if inkml_to_node != {} and parent not in inkml_to_node:
                if print_errors:
                    print(f"Error: Parent {parent} not found in inkml_to_node in file {self.file_path}. Maybe multiple roots?")
                return get_undefined_node_from_trace_groups(trace_groups, latex=self.get_annotation_text())
            parent = None if inkml_to_node == {} else inkml_to_node[parent]

            id = current.attrib[id_attribute] if id_attribute in current.attrib else None
            trace_group = trace_groups_dict[id] if id in trace_groups_dict else None
            if trace_group is not None: trace_group.set_type(type)

            node = create_relation_node(type, parent=parent, trace_group=trace_group)
            if root is None: root = node
            if parent is not None: parent.add_child(node)
            inkml_to_node[current] = node

        relation_graph = finalize_graph(root)
        return relation_graph

    def get_relation_graph_from_sym_lg(self, trace_groups, sym_lg_path):
        sym_lg = np.genfromtxt(sym_lg_path, delimiter=", ", dtype=str)
        objects = sym_lg[sym_lg[:, 0] == 'O'][:, [1, 4]]
        relations = sym_lg[sym_lg[:, 0] == 'R'][:, 1:4]

        origin_id = next((id for id, relation_str in objects if relation_str == "O"), None)
        if origin_id is None:
            print(f"Error: Origin trace group not found in file {self.file_path}")
            return None

        origin_tg = next((tg for tg in trace_groups if tg.math_annotation == origin_id), None)
        if origin_tg is None:
            print(f"Error: Origin trace group not found in file {self.file_path}")
            return None

        tg_relations = []
        for id_1, id_2, relation in relations:
            tg1 = next((tg for tg in trace_groups if tg.math_annotation == id_1), None)
            tg2 = next((tg for tg in trace_groups if tg.math_annotation == id_2), None)
            if tg1 is None or tg2 is None:
                print(f"Error: Trace group not found in file {self.file_path}")
                return None
            tg_relations.append((tg1, tg2, relation))

        return InkmlProcessor.create_node(origin_tg, tg_relations)

    @staticmethod
    def create_node(trace_group, tg_relations):
        relation_partners_and_types = []
        for relation in tg_relations:
            if relation[0].math_annotation == trace_group.math_annotation:
                relation_partners_and_types.append(({"partner": relation[1], "type": relation[2]}))

        above_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Above"]
        below_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Below"]
        sub_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Sub"]
        sup_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Sup"]
        right_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Right"]
        inside_node = [relation["partner"] for relation in relation_partners_and_types if relation["type"] == "Inside"]

        this_node = SymbolNode(trace_group=trace_group)
        if len(above_node) == 1 and len(below_node) == 1 and trace_group.label == "-":
            above_node = InkmlProcessor.create_node(above_node[0], tg_relations)
            below_node = InkmlProcessor.create_node(below_node[0], tg_relations)
            this_node = FracNode(children=[above_node, below_node], trace_group=trace_group)
        if len(inside_node) == 1 and trace_group.label == "\\sqrt":
            inside_node = InkmlProcessor.create_node(inside_node[0], tg_relations)
            this_node = SqrtNode(children=[inside_node], trace_group=trace_group)
        if len(sub_node) == 1:
            sub_node = InkmlProcessor.create_node(sub_node[0], tg_relations)
            this_node = SubNode(children=[this_node, sub_node])
        if len(sup_node) == 1:
            sup_node = InkmlProcessor.create_node(sup_node[0], tg_relations)
            this_node = SupNode(children=[this_node, sup_node])
        if len(right_node) == 1:
            right_node = InkmlProcessor.create_node(right_node[0], tg_relations)
            this_node = RowNode(children=[this_node, right_node])
        return this_node
