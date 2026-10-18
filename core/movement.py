"""Grid movement rules, independent of the renderer."""
from collections import deque


def find_path(start, destination, walkable):
    """Return the shortest orthogonal route, excluding start; None if illegal."""
    if start not in walkable or destination not in walkable:
        return None
    frontier = deque([start])
    previous = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == destination:
            path = []
            while current != start:
                path.append(current)
                current = previous[current]
            return list(reversed(path))
        x, z = current
        for neighbour in [(x + 1, z), (x, z + 1), (x - 1, z), (x, z - 1)]:
            if neighbour in walkable and neighbour not in previous:
                previous[neighbour] = current
                frontier.append(neighbour)
    return None
