import math


class Trace:
    def __init__(self, x, y, inkml_id=None, t=None):
        self.x = x
        self.y = y
        self.t = t
        self.inkml_id = inkml_id

    def __len__(self):
        return len(self.x)

    def __str__(self):
        result = f"Trace: {len(self.x)} points"
        if self.inkml_id is not None:
            result += f", ID: {self.inkml_id}"
        return result

    def __eq__(self, other):
        if other is None or len(self) != len(other):
            return False
        return all([self.x[i] == other.x[i] and self.y[i] == other.y[i] for i in range(len(self.x))]) and self.inkml_id == other.inkml_id

    def __hash__(self):
        return hash(tuple(self.x + self.y))

    def scale(self, dx, dy):
        self.x = [x * dx for x in self.x]
        self.y = [y * dy for y in self.y]

    def move(self, vector):
        self.move_x(vector[0])
        self.move_y(vector[1])

    def move_x(self, dx):
        self.x = [x + dx for x in self.x]

    def move_y(self, dy):
        self.y = [y + dy for y in self.y]

    def get_center(self):
        return (self.get_left() + self.get_right()) / 2, (self.get_top() + self.get_bottom()) / 2

    def get_size(self):
        return self.get_right() - self.get_left(), self.get_top() - self.get_bottom()

    def get_left(self):
        return min(self.x)

    def get_right(self):
        return max(self.x)

    def get_bottom(self):
        return min(self.y)

    def get_top(self):
        return max(self.y)

    def get_direct_distance_between(self, first_index, second_index):
        return self.euclid_distance(self.get_point(first_index), self.get_point(second_index))

    @staticmethod
    def euclid_distance(point1, point2):
        return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

    def length(self):
        length = 0
        for i in range(len(self) - 1):
            length += self.get_direct_distance_between(i, i + 1)
        return length

    def get_point(self, index):
        return self.x[index], self.y[index]

    def copy(self):
        return Trace(list(self.x).copy(), list(self.y).copy(), t=self.t, inkml_id=self.inkml_id)
