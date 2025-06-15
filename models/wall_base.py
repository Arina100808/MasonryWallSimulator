from utils.exceptions import InvalidDimensionError, NonModularWallError
from utils.colors import get_extended_colors, rgb_to_hex
from utils.geometry import distance
from collections import defaultdict
from models.brick import Brick
from typing import Any
import tkinter as tk

class BaseWall:
    """
    A class to represent a stretcher bond wall, calculate its layout, validate dimensions,
    and visualize the wall and its (optimized) building plan using tkinter.
    """
    def __init__(self, height: float, width: float,
                 brick_length=210.0, brick_width=100.0, brick_height=50.0,
                 head_joint=10.0, bed_joint=12.5, bond="stretcher"):
        """
        Initialize a StretcherBondWall object with the given dimensions and brick parameters.
        :param height: Height of the wall in mm.
        :param width: Width of the wall in mm.
        :param brick_length: Length of a full brick in mm.
        :param brick_width: Width of a full brick in mm.
        :param brick_height: Height of a full brick in mm.
        :param head_joint: Thickness of the head joint in mm.
        :param bed_joint: Thickness of the bed joint in mm.
        :param bond: Type of bond, currently only "stretcher" and "english" are supported.
        :raises InvalidDimensionError: If the height or width is not positive.
        :raises NonModularWallError: If the wall cannot be built with whole bricks based on the given dimensions.
        """
        self.height = height
        self.width = width

        self.brick_length = brick_length
        self.brick_width = brick_width
        self.brick_height = brick_height

        self.head_joint = head_joint
        self.bed_joint = bed_joint
        self.bond = bond.lower()
        if self.bond not in ["stretcher", "english", "wild"]:
            raise ValueError("Currently, only 'stretcher', 'english', and 'wild' bond types are supported.")

        self.brick_half_length = (self.brick_length - self.head_joint) / 2.0
        self.course_height = self.brick_height + self.bed_joint
        self.module_length = self.brick_length + self.head_joint

        self.modules, self.courses = self.get_layout()
        self.brick_plan = []

        try:
            self.validate_dimension()
        except InvalidDimensionError as e:
            print(f"Input Error: {e}")
            exit(1)
        except NonModularWallError as e:
            print(f"Modular Error: {e}")
            exit(1)

        self.modules, self.courses = int(self.modules), int(self.courses)

        self.get_brick_plan()

    def create_brick(self, x, y, is_half=False, is_built=False, length=None) -> Brick:
        """
        Create a Brick object with the specified parameters.
        :param x: The x-coordinate of the brick.
        :param y: The y-coordinate of the brick.
        :param is_half: Whether the brick is a half-brick.
        :param is_built: Whether the brick is built (default is False).
        :param length: The length of the brick. If None, use the default brick length.
        :return: A Brick instance with the specified parameters.
        """
        length = self.brick_length if length is None else length
        return Brick(x, y,
                     length, self.brick_width, self.brick_height,
                     is_half, is_built)

    def get_layout(self) -> tuple:
        """
        Calculate the number of "modules" and "courses" for a stretcher bond wall.
        A "module" consists of a brick and a head joint, and a "course" consists of a brick with a bed joint below it.
        In addition, check if the wall can be built with whole bricks based on the given dimensions.

        Assumptions:
        1. There are no joints on the sides of the wall.
        2. The sides of the wall are straight. So, if the wall is built with stretcher bond,
           each course = n "modules" (brick + head joint) + 1 half-brick.
        3. The lowest course includes a brick with a bed joint beneath it <=> the wall starts with a joint,
           and there is no joint at the top of the wall.

        :return: A tuple containing the number of modules and courses.
        """
        modules = (self.width - self.brick_half_length) / self.module_length
        courses = self.height / self.course_height

        return modules, courses

    def validate_dimension(self) -> None:
        """
        Validate the dimensions of the wall to ensure it can be built with whole bricks.
        :raises InvalidDimensionError: If the height or width is not positive or too small for a stretcher bond wall.
        :raises NonModularWallError: If the wall cannot be built with whole bricks based on the given dimensions.
        """
        if self.height <= 0 or self.width <= 0:
            raise InvalidDimensionError("Height and width must be positive numbers.")

        if self.modules < 1:
            raise InvalidDimensionError(f"Width is too small for a stretcher bond wall. "
                                        f"The minimum width is {self.brick_half_length + self.module_length} mm.")

        if self.height < self.course_height:
            raise InvalidDimensionError(f"Height is too small for a stretcher bond wall. "
                                        f"The minimum height is {self.course_height} mm.")

        # If the calculated number of modules or courses are not an integer, the wall cannot be built with whole bricks.
        # So, it is suggested to choose a different width and/or length.
        valid_width = self.modules.is_integer()
        valid_height = self.courses.is_integer()

        if not valid_width or not valid_height:
            change_width = (f"width (e.g., {int(self.modules) * self.module_length + self.brick_half_length} or "
                            f"{(int(self.modules) + 1) * self.module_length + self.brick_half_length})")\
                            if not valid_width else ""
            change_height = (f"height (e.g., {int(self.courses) * self.course_height} "
                             f"or {(int(self.courses) + 1) * self.course_height})") if not valid_height else ""
            delimiter = " and " if change_width and change_height else ""
            raise NonModularWallError(f"For given parameters, the wall cannot be built with whole bricks.\n"
                                      f"Please change the following parameter(s): "
                                      f"{change_width}{delimiter}"
                                      f"{change_height}.")

    def sort_brick_plan(self, reverse=False) -> list:
        """
        Sort the build plan:
        - First by stride_y (vertical)
        - Then by stride_x (horizontal)
        - Then snake bricks inside each stride
        :param reverse: If True, sort in descending order.
        :return: A list of sorted Brick instances.
        """
        # Sort strides vertically
        stride_ys = sorted(set(b.stride[1] for b in self.brick_plan), reverse=reverse)
        ordered_bricks = []

        for sy in stride_ys:
            # Filter bricks for this stride_y
            stride_row_bricks = [b for b in self.brick_plan if b.stride[1] == sy]

            # Always sort stride_x left to right (NO snake at this level)
            stride_xs = sorted(set(b.stride[0] for b in stride_row_bricks))

            for sx in stride_xs:
                # Filter bricks for this stride
                stride_bricks = [b for b in stride_row_bricks if b.stride[0] == sx]

                # Sort by y
                brick_ys = sorted(set(b.y for b in stride_bricks), reverse=True)

                for i, y_val in enumerate(brick_ys):
                    # Snake logic inside each row
                    row_bricks = [b for b in stride_bricks if b.y == y_val]
                    row_bricks.sort(key=lambda b: b.x, reverse=(i % 2 == 1))
                    ordered_bricks.extend(row_bricks)

        return ordered_bricks

    def is_base_built(self, brick) -> bool:
        """
        Check if the base of the given brick is built.
        :param brick: The Brick instance to check.
        :return: True if the base is built, False otherwise.
        """
        row_below = brick.y + self.course_height
        if row_below == self.height:
            # If the brick is in the bottom row, it always can be built
            return True
        target_x = brick.x + brick.length
        left_brick, right_brick = None, None
        covered_x = 0.0

        for b in self.brick_plan:
            if b.y == row_below:
                if b.x <= brick.x:
                    if b.is_built:
                        left_brick = b
                else:
                    if right_brick is None and (left_brick is None or left_brick.x +
                                                left_brick.length + self.head_joint < b.x):
                        return False
                    elif right_brick is None:
                        covered_x = left_brick.x + left_brick.length
                        if covered_x >= target_x:
                            return True
                        elif not b.is_built:
                            return False
                        else:
                            right_brick = b
                            covered_x += self.head_joint + right_brick.length
                            if covered_x >= target_x:
                                return True
                    elif b.is_built:
                        right_brick = b
                        covered_x += self.head_joint + right_brick.length
                        if covered_x >= target_x:
                            return True
                    else:
                        return False

        if left_brick is not None:
            covered_x = left_brick.x + left_brick.length
            if covered_x >= target_x:
                return True
        return False

    def collect_triangle_bricks(self, bricks_to_build, stride_width, stride_height, edge) -> list:
        """
        Collect bricks belonging to a triangle structure starting from the lowest brick on the edge,
        constrained by stride dimensions and edge alignment.

        :param bricks_to_build: List of Brick instances (sorted by y and x)
        :param stride_width: The width of a stride
        :param stride_height: The height of a stride
        :param edge: "left" or "right" - which side stride is aligned to
        :return:  the List of bricks that belong to the triangle
        """
        # Find the starting brick (the lowest brick on the given edge)
        edge_x = 0.0 if edge == "left" else self.width

        if edge == "left":
            edge_bricks = [b for b in bricks_to_build if b.x == edge_x]
        else:
            edge_bricks = [b for b in bricks_to_build if b.x + b.length == edge_x]

        if not edge_bricks:
            return []

        start_brick = max(edge_bricks, key=lambda b: b.y)

        # Calculate stride boundaries based on edge
        stride_x0 = 0.0 if edge == "left" else self.width - stride_width
        stride_x1 = stride_x0 + stride_width
        stride_y_bottom = start_brick.y + self.course_height
        stride_y_top = stride_y_bottom - stride_height

        # Build fast lookup for bricks by row
        bricks_by_y = {}
        for b in bricks_to_build:
            bricks_by_y.setdefault(b.y, []).append(b)

        # Collect bricks row by row, starting from start_brick
        triangle_bricks = [start_brick]
        current_row_y = start_brick.y - self.course_height
        prev_brick_x0 = start_brick.x
        prev_brick_x1 = prev_brick_x0 + start_brick.length

        while current_row_y in bricks_by_y:
            row_bricks = bricks_by_y[current_row_y]
            row_added = False
            first_brick_in_row_right_tr = True

            for brick in row_bricks:

                # Check if brick is inside stride rectangle
                if not (stride_x0 <= brick.x < stride_x1 and brick.x + brick.length <= stride_x1 and
                        stride_y_bottom > brick.y >= stride_y_top):
                    if edge == "left":
                        last_added_row = min(b.y for b in triangle_bricks)
                        triangle_bricks = [br for br in triangle_bricks if br.y != last_added_row]
                        return triangle_bricks
                    else:
                        continue

                # Check if brick can be added
                if (brick.x < prev_brick_x1 and edge == "left") or \
                        (brick.x + brick.length > prev_brick_x0 and edge == "right"):
                    if edge == "right" and brick.x >= prev_brick_x0 and first_brick_in_row_right_tr:
                        return triangle_bricks
                    triangle_bricks.append(brick)
                    row_added = True

                    if edge == "left":
                        current_edge_x = brick.x + brick.length
                        if current_edge_x >= prev_brick_x1:
                            prev_brick_x1 = current_edge_x
                            break  # stop processing this row after extending the right edge
                    else:
                        if first_brick_in_row_right_tr:
                            prev_brick_x0 = brick.x
                            first_brick_in_row_right_tr = False

            if not row_added:
                break

            current_row_y -= self.course_height

        return triangle_bricks

    def is_brick_built(self, x, y, is_half=False) -> bool:
        """
        Check if a brick is built at the specified coordinates.
        :param x: The coordinates of the brick.
        :param y: The coordinates of the brick.
        :param is_half: Whether the brick is a half-brick.
        :return: True if the brick is built, False otherwise.
        """
        found_brick = next((b for b in self.brick_plan if b.x == x and b.y == y and b.is_half == is_half), None)
        return found_brick.is_built if found_brick else False

    def has_built_brick_below(self, brick, side="right") -> bool:
        """
        Check if there is a built brick below the given brick on the specified side.
        :param brick: The Brick instance to check.
        :param side: "right" or "left" - which side to check for a built brick below.
        :return: True if there is a built brick below on the specified side, False otherwise.
        """
        row_below_y = brick.y + self.course_height
        if side == "right":
            right_edge = brick.x + brick.length
            for b in self.brick_plan:
                if b.y == row_below_y and b.is_built and b.x < right_edge <= b.x + b.length:
                    return True
        else:
            left_edge = brick.x
            for b in self.brick_plan:
                if b.y == row_below_y and b.is_built and b.x + b.length > left_edge >= b.x:
                    return True

        return False

    def get_optimized_building_plan(self, stride_width, stride_height) -> set[Any]:
        """
        Generate an optimized building plan based on the provided brick plan and stride dimensions.
        Assumptions:
                    1. The head joint of the last brick in a stride is included in the stride width.
        :param stride_width: The width of the stride in mm.
        :param stride_height: The height of the stride in mm.
        :return: A set of tuples representing the strides (sx, sy) where bricks are built.
        """
        # Print key parameters: max number of bricks in a stride, in width and in height
        max_bricks_in_width = stride_width // self.module_length # include head joint of the last brick in a stride
        max_bricks_in_width += 0.5 if (stride_width % self.module_length >= self.brick_half_length +
                                       self.head_joint) else 0
        max_bricks_in_height = stride_height // self.course_height
        print(f"\nGiven stride: {stride_width} (width), {stride_height} (height);")
        if self.bond == "stretcher":
            print(f"Max bricks in width: {max_bricks_in_width};")
            print(f"Max bricks in height: {max_bricks_in_height};")

        x0 = 0.0
        y0 = self.height  # axis y is inverted in tkinter
        sx, sy = 0, 0
        strides = set()
        center_is_filled = False
        lowest_closest_brick = self.create_brick(self.width - self.brick_half_length,
                                                 self.height - self.course_height, True)

        left_triangle, right_triangle = [], []
        params = (0, 0, False)
        top_right_brick, top_left_brick = self.create_brick(*params), self.create_brick(*params)
        lowest_left_brick, lowest_right_brick = self.create_brick(*params), self.create_brick(*params)

        bricks_to_build = self.brick_plan

        while bricks_to_build:
            # Calculate the coordinates of the current stride
            x1 = x0 + stride_width
            y1 = y0 - stride_height

            # Build all the possible bricks in the current stride
            for brick in bricks_to_build:
                # Calculate the right edge of the brick (with head joint)
                bx1 = brick.x + brick.length + self.head_joint

                # Skip bricks that are out of the stride
                if x0 <= brick.x <= x1 and (bx1 <= x1 or bx1 == x1 + self.head_joint - 0.1) and y0 >= brick.y >= y1:
                    # If not building the first two pyramids and the center is not filled,
                    # check if the brick is inside the triangle contour
                    if not center_is_filled and ((sx, sy) not in [(0, 0), (2, 0)]):
                        brick_is_in_left_tr = brick in left_triangle
                        brick_is_in_right_tr = brick in right_triangle
                        if brick_is_in_left_tr or brick_is_in_right_tr:
                            continue
                    # Check if the "base" is built
                    # The base is defined as the two bricks below the current brick
                    # (If the stride is at the bottom of the wall, the base is built)
                    base_built = self.is_base_built(brick)
                    if base_built:
                        # Build the brick in the stride
                        brick.stride = (sx, sy)
                        brick.is_built = True
                        strides.add((sx, sy))

            bricks_to_build = [b for b in bricks_to_build if not b.is_built]

            if not bricks_to_build:
                break

            # If a pyramid or a triangle was just built, find the next triangle
            if center_is_filled or (sy == 0 and (sx == 0 or sx == 2)):
                # Define the next triangle - the largest stride that can be built
                if x0 == 0.0 or (sy == 0 and sx == 0):
                    left_triangle = self.collect_triangle_bricks(bricks_to_build, stride_width, stride_height,
                                                                 edge="left")
                    if left_triangle:
                        max_y, min_y = min(b.y for b in left_triangle), max(b.y for b in left_triangle)
                        top_right_brick = max([b for b in left_triangle if b.y == max_y], key=lambda b: b.x)
                else:
                    right_triangle = self.collect_triangle_bricks(bricks_to_build, stride_width, stride_height,
                                                                  edge="right")
                    if right_triangle:
                        max_y, min_y = min(b.y for b in right_triangle), max(b.y for b in right_triangle)
                        lowest_right_brick = max([b for b in right_triangle if b.y == min_y], key=lambda b: b.x)
                        top_left_brick = min([b for b in right_triangle if b.y == max_y], key=lambda b: b.x)

            else: # Check if the center is finished
                left_tr_has_base = self.has_built_brick_below(top_right_brick, side="right")
                right_tr_has_base = self.has_built_brick_below(top_left_brick, side="left")
                if left_tr_has_base and right_tr_has_base:
                    center_is_filled = True
                else:
                    center_is_filled = False

            if sy == 0 and (sx == 0 or sx == 2):
                filtered_bricks_to_build = bricks_to_build
                if stride_width < self.width:
                    # Building pyramids on the left and right sides
                    center_is_filled = False
                else:
                    # If the stride is wider than the wall, we can just build the wall
                    center_is_filled = True
            elif not center_is_filled:
                filtered_bricks_to_build = [b for b in bricks_to_build if (not b in left_triangle) and\
                                            (not b in right_triangle)]
            else:
                filtered_bricks_to_build = bricks_to_build

            # Find the lowest row with a not-built brick
            possible_lowest_bricks = [b for b in filtered_bricks_to_build if self.is_base_built(b)]

            lowest_y = max(b.y for b in possible_lowest_bricks)
            # Find all bricks in the lowest row
            lowest_bricks = [b for b in possible_lowest_bricks if b.y == lowest_y]

            # Fill in the base of the wall (shifting to the right)
            if sy == 0 and (sx == 0 or sx == 2):
                # Build a triangle pyramid on the right side
                if sx == 0:
                    x0 = self.width - stride_width + 0.1
                    sx = 2
                # Shift to fill in the gap between two triangle pyramids
                elif sx == 2:
                    pyramid_bases = max_bricks_in_width + (max_bricks_in_width - 0.5)
                    left_pyramid_base = max_bricks_in_width if max_bricks_in_width.is_integer()\
                                        else max_bricks_in_width - 0.5
                    right_pyramid_base = pyramid_bases - left_pyramid_base
                    x0 = self.width - self.brick_half_length - int(right_pyramid_base)*self.module_length - stride_width
                    sx = 1
            else:
                if sy == 0 and sx == 1:
                    sx = 2
                prev_x, prev_y = lowest_closest_brick.x, lowest_closest_brick.y
                lowest_closest_brick = min(lowest_bricks, key=lambda b: abs(b.x - x0))
                if not (lowest_closest_brick.x == 0.0 or
                        lowest_closest_brick.x + lowest_closest_brick.length == self.width):
                    center_is_filled = False
                dy = lowest_closest_brick.y - prev_y
                if center_is_filled:
                    x0 = 0.0 if lowest_closest_brick.x == 0.0 else self.width - stride_width + 0.1
                else:
                    if not max_bricks_in_width.is_integer():
                        shift = - self.module_length
                        if right_triangle:
                            dist_low = distance(lowest_closest_brick, top_left_brick)
                            dist_mid = distance(lowest_closest_brick, lowest_right_brick)
                            if dist_low <= self.module_length*1.5 or dist_mid <= self.module_length*1.5:
                                shift *= 2
                    else:
                        shift = 2*self.module_length - stride_width
                    x0 = lowest_closest_brick.x + shift
                y0 = lowest_closest_brick.y + self.course_height
                sy += 1 if abs(dy) > 0 else 0
                sx += 1 if dy == 0 else -sx

        return strides

    def visualize_plan(self, scale=0.4, bg_color="#f0f0f0", brick_color="#f6f2f1", mortar_color="#cbbdbb",
                       built_color="#58413d", stride_width=None, stride_height=None, debug=False) -> None:
        """
        Visualize the stretcher bond wall plan with optional interactive and stride-based optimization.

        If stride_width and stride_height are provided, an optimized build order is used.
        Otherwise, bricks are drawn from bottom to top, starting from the left.

        Assumptions:
        1. The robot starts from the left side and builds the wall in a bottom-up manner.

        :param scale: The scale factor for the visualization.
        :param bg_color: The background color of the canvas.
        :param brick_color: The color of the bricks.
        :param mortar_color: The color of the mortar between bricks.
        :param built_color: The color of the bricks that are built.
        :param stride_width: The width of the stride in mm for optimization.
        :param stride_height: The height of the stride in mm for optimization.
        :param debug: If True, prints additional debug information.
        :return: None
        """
        width_px = self.width * scale
        height_px = self.height * scale

        print(f"Visualizing wall: {self.courses} courses;")
        if self.bond == "stretcher":
            print(f"{self.modules + 1} bricks per course;")
        print(f"Dimensions: {self.width}mm (width) x {self.height}mm (height);")
        if debug: print(f"\nCanvas size: {width_px}px (width) x {height_px}px (height), scale: {scale}.\n")

        root = tk.Tk()
        if self.bond == "english":
            root.title("English Bond Wall Plan")
        elif self.bond == "stretcher":
            root.title("Stretcher Bond Wall Plan")
        else:
            root.title("Wild Bond Wall Plan")

        canvas = tk.Canvas(root, width=width_px, height=height_px, bg=bg_color)
        canvas.pack()

        # Draw design bricks in background color
        for brick in self.brick_plan:
            brick.draw(canvas, scale, brick_color, mortar_color)

        stride_colors = defaultdict()
        one_stride = stride_width is None and stride_height is None
        if stride_width is None and stride_height is None:
            strides = [(0, 0)]
            stride_colors[strides[0]] = built_color
        else:
            strides = self.get_optimized_building_plan(stride_width, stride_height)
            strides = sorted(strides, key=lambda s: (s[1], s[0]))
            colors = get_extended_colors(len(strides))
            hex_colors = [rgb_to_hex(c) for c in colors]
            stride_colors = dict(zip(strides, hex_colors))

        sorted_bricks = self.sort_brick_plan()

        print(f"\nThe wall can be built in {len(strides)} stride(s).")
        current_index = [0]
        sorted_bricks_built = [b for b in sorted_bricks if b.is_built] if not one_stride else sorted_bricks
        def on_enter(event=None):
            if current_index[0] < len(sorted_bricks_built):
                current_brick = sorted_bricks_built[current_index[0]]
                current_stride_key = current_brick.stride
                color = stride_colors[current_stride_key]
                if not current_brick.is_built:
                    color = built_color # when the stride is not used
                current_brick.draw(canvas, scale, color, mortar_color)
                if debug:
                    print(f"Built brick at ({current_brick.x:.1f}, {current_brick.y:.1f}) in stride {current_stride_key}")
                current_index[0] += 1
            else:
                print(f"All bricks built.")
        root.bind("<Return>", on_enter)

        root.mainloop()
