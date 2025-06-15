from models.wall_base import BaseWall
from models.stretcher_wall import BondLayoutHelper

class EnglishBondWall(BaseWall, BondLayoutHelper):
    def get_even_row_plan(self, y) -> list:
        """
        Generate the plan for even rows of the wall.
        Even rows start with a half-brick on the left.
        :param y: The vertical position of the row in the wall.
        :return: A list of Brick instances representing the even row plan.
        """
        length = self.brick_half_length
        half_length = (length - self.head_joint) / 2.0

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

        x_last = half_length + self.head_joint + m * (length + self.head_joint)
        even_row_plan.append(self.create_brick(x=x_last, y=y, is_half=True, length=half_length))

        return even_row_plan
