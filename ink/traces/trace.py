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

    def interpolate(self, target_point_number):
        if self.t is not None: self.t = None # t is not yet supported for interpolation

        if len(self) == 1:
            self.x = self.x * target_point_number
            self.y = self.y * target_point_number
            return

        if target_point_number == 1:
            x_c, y_c = self.get_center()
            self.x = [x_c]
            self.y = [y_c]
            return

        next_dist_for_index = [self.get_direct_distance_between(i, i + 1) for i in range(len(self) - 1)]
        total_length = sum(next_dist_for_index)
        target_segment_length = total_length / (target_point_number - 1)

        if total_length == 0:
            self.x = [self.x[0]] * target_point_number
            self.y = [self.y[0]] * target_point_number
            return

        for i in range(0, target_point_number - 2):
            next_index = self.find_next_index_for_length(target_segment_length, i, next_dist_for_index)
            prev_index = next_index - 1
            prev_index_distance = sum(next_dist_for_index[i:prev_index])

            alpha = (target_segment_length - prev_index_distance) / next_dist_for_index[prev_index]

            interpolated_x = self.x[prev_index] + alpha * (self.x[next_index] - self.x[prev_index])
            interpolated_y = self.y[prev_index] + alpha * (self.y[next_index] - self.y[prev_index])

            self.x = self.x[:i+1] + [interpolated_x] + self.x[next_index:]
            self.y = self.y[:i+1] + [interpolated_y] + self.y[next_index:]

            next_dist_for_index = (next_dist_for_index[:i] +
                                   [self.get_direct_distance_between(i, i+1)] +
                                   [self.get_direct_distance_between(i+1, i+2)] +
                                   next_dist_for_index[next_index:])
            target_segment_length = sum(next_dist_for_index[i:]) / (target_point_number - i - 1)

        self.x = self.x[:target_point_number-1] + [self.x[-1]]
        self.y = self.y[:target_point_number-1] + [self.y[-1]]

    def find_next_index_for_length(self, length, i, next_dist_for_index):
        next_index = i + 1
        distance_to_next = next_dist_for_index[i]
        while distance_to_next < length:
            distance_to_next += next_dist_for_index[next_index]
            next_index += 1
        return next_index

    def copy(self):
        return Trace(list(self.x).copy(), list(self.y).copy(), t=self.t, inkml_id=self.inkml_id)
