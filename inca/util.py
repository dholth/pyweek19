
def clamp(coord, lower, upper):
    """
    Clamp coord to lay between lower and upper.
    """
    return min(upper, max(coord, lower))
