class Brick:
    def __init__(self, x:float, y:float,
                 length: float, width: float, height: float,
                 is_half=False, is_built=False, stride=(0, 0)):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.height = height
        self.is_half = is_half
        self.is_built = is_built
        self.stride = stride

    def draw(self, canvas, scale, brick_color, mortar_color):
        canvas.create_rectangle(self.x*scale, self.y*scale, (self.x + self.length)*scale, (self.y + self.height)*scale,
                                fill=brick_color, outline=mortar_color)
