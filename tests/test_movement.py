from core.movement import find_path


def test_shortest_route_stays_on_adjacent_tiles():
    cells = {(x, z) for x in range(4) for z in range(4)}
    route = find_path((0, 0), (3, 2), cells)
    assert len(route) == 5
    previous = (0, 0)
    for current in route:
        assert abs(previous[0] - current[0]) + abs(previous[1] - current[1]) == 1
        previous = current
    assert previous == (3, 2)


def test_route_goes_around_blocked_tile():
    cells = {(x, z) for x in range(3) for z in range(3)} - {(1, 0)}
    route = find_path((0, 0), (2, 0), cells)
    assert len(route) == 4
    assert (1, 0) not in route


def test_invalid_unreachable_and_current_destinations():
    assert find_path((0, 0), (2, 0), {(0, 0), (2, 0)}) is None
    assert find_path((0, 0), (-1, 0), {(0, 0)}) is None
    assert find_path((0, 0), (0, 0), {(0, 0)}) == []
