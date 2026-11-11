"""environment.py - ENVIRONMENT: môi trường mê cung dạng lưới 2D.

Quy ước ký tự trong bản đồ:  S = xuất phát, G = đích, # = tường, . = ô trống.
Tọa độ một ô là (hàng, cột) = (x, y) như trong đề bài.
"""
import random
from collections import deque

WALL, FREE, START, GOAL = "#", ".", "S", "G"
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]        # Up, Down, Left, Right
DIR_NAMES = ["Up", "Down", "Left", "Right"]

MAPS = {
    1: {"name": "Bản đồ 1 - ít vật cản", "grid": [
        "S..............",
        "..##....#......",
        "..##....#..###.",
        ".......##......",
        ".####..........",
        ".#.............",
        ".#..######.....",
        ".#..#..........",
        "....#...####...",
        ".####..........",
        "..............G"]},
    2: {"name": "Bản đồ 2 - nhiều ngã rẽ", "grid": [
        "S.....#........",
        ".####.#.######.",
        ".#....#.#....#.",
        ".#.####.#.##.#.",
        ".#......#.#..#.",
        ".########.#.##.",
        "...........#...",
        "##########.#.##",
        "..........#....",
        ".########.#.##.",
        "..........#...G"]},
    3: {"name": "Bản đồ 3 - nhiều đường cụt", "grid": [
        "S...#..........",
        ".##.#.########.",
        ".#..#.#......#.",
        ".#.##.#.####.#.",
        ".#.#..#.#....#.",
        ".#.#.##.#.####.",
        ".#.#....#.#....",
        ".#.######.#.##.",
        ".#........#.#..",
        ".########.#.#.#",
        "..........#...G"]},
}


class Environment:
    """Quản lý bản đồ, vật cản, kiểm tra vị trí hợp lệ và cung cấp thông tin quan sát."""

    def __init__(self, map_id=1, grid=None, name=None):
        if grid is None:
            grid, name = MAPS[map_id]["grid"], MAPS[map_id]["name"]
        self.map_id, self.name = map_id, name or "Bản đồ ngẫu nhiên"
        self.cells = [list(row) for row in grid]
        self.rows, self.cols = len(self.cells), len(self.cells[0])
        self.start = self.goal = None
        self._opt = None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c] == START:
                    self.start = (r, c)
                elif self.cells[r][c] == GOAL:
                    self.goal = (r, c)
                if self.cells[r][c] in (START, GOAL):
                    self.cells[r][c] = FREE           # S và G đều là ô đi được
        if self.start is None or self.goal is None:
            raise ValueError("Bản đồ phải có đúng một S và một G")

    @property
    def optimal(self):
        """Độ dài đường ngắn nhất thật từ S tới G (BFS trên bản đồ thật). Chỉ dùng để đánh giá, robot không được biết."""
        if self._opt is None:
            self._opt = distances_from(self, self.start).get(self.goal)
        return self._opt

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def is_free(self, pos):
        """Vị trí hợp lệ: nằm trong bản đồ và không phải tường."""
        return self.in_bounds(pos) and self.cells[pos[0]][pos[1]] != WALL

    def observe(self, pos, radius=1):
        """Cảm biến: trả về {ô: '#' hoặc '.'} cho các ô trong vùng (2r+1)x(2r+1) quanh pos."""
        seen = {}
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                p = (pos[0] + dr, pos[1] + dc)
                if self.in_bounds(p):
                    seen[p] = self.cells[p[0]][p[1]]
        return seen


def distances_from(env, source):
    """BFS trên bản đồ thật: khoảng cách ngắn nhất từ source tới mọi ô (dùng để kiểm tra và gán nhãn ML)."""
    dist, queue = {source: 0}, deque([source])
    while queue:
        cur = queue.popleft()
        for dr, dc in DIRS:
            nb = (cur[0] + dr, cur[1] + dc)
            if nb not in dist and env.is_free(nb):
                dist[nb] = dist[cur] + 1
                queue.append(nb)
    return dist


def random_environment(rng=None, rows=11, cols=15):
    """Sinh bản đồ ngẫu nhiên có đường đi từ S tới G (dùng để tạo dữ liệu huấn luyện ML)."""
    rng = rng or random.Random()
    while True:
        density = rng.uniform(0.15, 0.38)
        grid = [[WALL if rng.random() < density else FREE for _ in range(cols)] for _ in range(rows)]
        grid[0][0], grid[rows - 1][cols - 1] = START, GOAL
        env = Environment(grid=["".join(r) for r in grid])
        if env.goal in distances_from(env, env.start):
            return env
