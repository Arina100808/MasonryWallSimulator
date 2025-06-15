# Custom Exceptions
class InvalidDimensionError(Exception):
    """Raised when height or width are invalid."""
    pass

class NonModularWallError(Exception):
    """Raised when the wall can't be built with whole bricks."""
    pass