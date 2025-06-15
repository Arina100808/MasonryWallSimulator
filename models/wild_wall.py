from models.wall_base import BaseWall
import random

class WildBondWall(BaseWall):
    def get_wild_row_plan(self, y, row_index=0) -> list:
        """
        Generate one row plan for wild bond (controlled random bond) fully filling wall width.
        :param y: The vertical position of the row in the wall.
        :param row_index: The index of the row (used for staggering).
        :return: A list of Brick instances representing the wild row plan.
        """
        row_plan = []

        # 1/4 brick stagger offset for even rows
        quarter_length = (self.brick_half_length - self.head_joint)/2
        stagger_offset = quarter_length if row_index % 2 == 0 else 0.0
        x = 0.0

        # Left edge compensation
        if stagger_offset > 0:
            # Add quarter brick filler
            small_filler = self.create_brick(x=x, y=y, is_half=True, length=quarter_length)
            row_plan.append(small_filler)
            x += quarter_length + self.head_joint

        consecutive_half = 0
        consecutive_full = 0
        c = 0
        limit = 4
        while x < self.width:
            remaining_space = self.width - x

            if remaining_space == quarter_length:
                brick = self.create_brick(x=x, y=y, is_half=True, length=quarter_length)
                row_plan.append(brick)
                break
            elif remaining_space == self.brick_half_length:
                brick = self.create_brick(x=x, y=y, is_half=True, length=self.brick_half_length)
                row_plan.append(brick)
                break
            elif remaining_space == self.brick_half_length + self.head_joint + quarter_length:
                # Add half brick and quarter brick filler
                half_brick = self.create_brick(x=x, y=y, is_half=True, length=self.brick_half_length)
                row_plan.append(half_brick)
                x += self.brick_half_length + self.head_joint
                small_filler = self.create_brick(x=x, y=y, is_half=True, length=quarter_length)
                row_plan.append(small_filler)
                break

            # Decide possible bricks based on remaining space and consecutive limits
            possible_bricks = []
            if consecutive_full < 5 and remaining_space >= self.brick_length:
                possible_bricks.append(("full", self.brick_length))
            if consecutive_half == 0 and remaining_space >= self.brick_half_length:
                possible_bricks.append(("half", self.brick_half_length))
            if not possible_bricks:
                break

            brick_choice = random.choice(possible_bricks)
            brick_length = brick_choice[1]
            temp_x1 = x + brick_length

            y_below = y + self.course_height
            falling_teeth = 0
            staggered_steps_left, staggered_steps_right = 0, 0
            fixed_step_left, fixed_step_right = 0, 0

            unwanted_patters = False

            if len(possible_bricks) > 1 and y != self.height - self.course_height and \
                    y + self.course_height * limit < self.height:
                left_edge = temp_x1
                right_edge = temp_x1
                count_row = 1
                potential_unwanted_left, potential_unwanted_right, potential_unwanted_teeth = True, True, True
                while y_below <= y + self.course_height * 6:
                    if potential_unwanted_left:
                        left_brick_below = max((b for b in self.brick_plan if b.y == y_below and \
                                                b.x + b.length < left_edge), key=lambda b: b.x, default=None)
                        if left_brick_below:
                            step_left = left_edge - (left_brick_below.x + left_brick_below.length)
                            if y_below == y + self.course_height:
                                fixed_step_left = step_left
                            repeated_step_left = step_left == fixed_step_left

                            if repeated_step_left:
                                staggered_steps_left += 1
                            else:
                                potential_unwanted_left = False
                            left_edge = left_brick_below.x + left_brick_below.length

                    if potential_unwanted_teeth:
                        brick_below_middle = max((b for b in self.brick_plan if b.y == y_below and \
                                                  b.x + b.length <= temp_x1), key=lambda b: b.x, default=None)
                        if brick_below_middle:
                            falling_teeth_step = temp_x1 - (brick_below_middle.x + brick_below_middle.length)
                            falling_teeth_target_step = fixed_step_left if count_row % 2 == 1 else 0
                            falling_teeth_pattern = falling_teeth_step == falling_teeth_target_step

                            if falling_teeth_pattern:
                                falling_teeth += 1
                            else:
                                potential_unwanted_teeth = False

                    if potential_unwanted_right:
                        right_brick_below = min((b for b in self.brick_plan if b.y == y_below and \
                                                 b.x + b.length > right_edge), key=lambda b: b.x, default=None)

                        if right_brick_below:
                            step_right = right_brick_below.x + right_brick_below.length - right_edge
                            if y_below == y + self.course_height:
                                fixed_step_right = step_right

                            repeated_step_right = step_right == fixed_step_right
                            if repeated_step_right:
                                staggered_steps_right += 1
                            else:
                                potential_unwanted_right = False
                            right_edge = right_brick_below.x + right_brick_below.length

                    if not potential_unwanted_left and not potential_unwanted_right and not potential_unwanted_teeth:
                        break

                    # When we see that if we add a chosen brick, it will result in 6 staggered steps/falling teeth,
                    # we need to change the brick choice
                    if staggered_steps_left == limit or falling_teeth == limit or staggered_steps_right == limit:
                        possible_bricks.remove(brick_choice)
                        unwanted_patters = True
                        break
                    y_below += self.course_height
                    count_row += 1

            if unwanted_patters:
                brick_choice = possible_bricks[0]

            is_half = brick_choice[0] == "half"
            brick_length = brick_choice[1]

            # Calculate x increment: add head joint only if this is NOT the last brick
            if x + brick_length + self.head_joint < self.width:
                x_increment = brick_length + self.head_joint
            else:
                x_increment = brick_length

            brick = self.create_brick(x=x, y=y, is_half=is_half, length=brick_length)
            row_plan.append(brick)

            if is_half:
                consecutive_half += 1
                consecutive_full = 0
            else:
                consecutive_full += 1
                consecutive_half = 0

            x += x_increment
            c += 1
        return row_plan

    def get_brick_plan(self) -> None:
        """
        Generate the full wall plan, alternating between odd and even rows.
        """

        for row in range(self.courses - 1, -1, -1):
            y = row * self.course_height
            row_plan = self.get_wild_row_plan(y=y, row_index=row)
            self.brick_plan.extend(row_plan)