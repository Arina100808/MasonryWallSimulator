import math

def distance(brick1, brick2):
    return math.sqrt((brick2.x - brick1.x)**2 + (brick2.y - brick1.y)**2)