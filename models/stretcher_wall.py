from models.wall_base import BaseWall

class BondLayoutHelper:
    """
    A mixin class to generate odd row plans for stretcher and English bond walls.
    """
    def get_odd_row_plan(self, y) -> list:
        """
        Generate the plan for odd rows of the wall.
        Odd rows end with a half-brick on the right.
        :param y: The vertical position of the row in the wall.
        :return: A list of Brick instances representing the odd row plan.
        """
        odd_row_plan = []
        m = 0
        row_length = 0.0
        while row_length < self.width:
            x = m * self.module_length
            brick = self.create_brick(x, y=y)
            row_length = x + brick.length
            if row_length > self.width:
                break
            odd_row_plan.append(brick)  # Full brick
            m += 1
        x = self.modules * self.module_length
        half_brick = self.create_brick(x=x, y=y, is_half=True, length=self.brick_half_length)
        odd_row_plan.append(half_brick)  # Half-brick
        return odd_row_plan

    def get_brick_plan(self) -> None:
        """
        Generate the full wall plan, alternating between odd and even rows.
        """
        remainder = self.courses % 2

        for row in range(self.courses - 1, -1, -1):
            y = row * self.course_height
            row_plan = self.get_odd_row_plan(y) if row % 2 != remainder else self.get_even_row_plan(y)
            self.brick_plan.extend(row_plan)

class StretcherBondWall(BaseWall, BondLayoutHelper):
    def get_even_row_plan(self, y) -> list:
        """
        Generate the plan for even rows of the wall.
        Even rows start with a half-brick on the left.
        :param y: The vertical position of the row in the wall.
        :return: A list of Brick instances representing the even row plan.
        """
        length = self.brick_length
        half_length = self.brick_half_length

        even_row_plan = [self.create_brick(x=0, y=y, is_half=True, length=half_length)] # Half-brick
        m = 0
        row_length = 0.0
        while row_length < self.width:
            x = half_length + self.head_joint + m * (length + self.head_joint)
            brick = self.create_brick(x=x, y=y, length=length)
            row_length = x + length
            if row_length > self.width:
                break
            even_row_plan.append(brick)  # Full brick
            m += 1

        return even_row_plan
