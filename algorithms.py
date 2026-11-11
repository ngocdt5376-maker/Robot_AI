"""algorithms.py - WeightedAStar, LRTAStar và cơ chế khám phá (biên giữa vùng biết / chưa biết).

Mỗi tác tử có hàm decide(robot) -> (ô_kế_tiếp hoặc None, câu giải thích).
risk_fn(robot, [ô...]) -> [mức rủi ro 0/1/2 ...] là đầu ra của mô hình ML (không bắt buộc).
"""
import heapq
import itertools
from collections import deque
from environment import DIRS, DIR_NAMES


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def direction_name(a, b):
    return DIR_NAMES[DIRS.index((b[0] - a[0], b[1] - a[1]))]


def no_risk(robot, positions):
    return [0] * len(positions)


# ============================ Weighted A* ===================================
class WeightedAStar:
    """f(n) = g(n) + w * h(n), h = khoảng cách Manhattan. w > 1 thì không đảm bảo đường ngắn nhất."""

    def __init__(self, weight=1.5):
        self.weight = weight

    def search(self, passable, start, goal):
        """Tìm đường trên bản đồ đã biết. Trả về (đường đi [start..goal] hoặc None, số nút đã mở rộng)."""
        tie = itertools.count()
        g, parent = {start: 0}, {start: None}
        heap = [(self.weight * manhattan(start, goal), next(tie), 0, start)]
        expanded = 0
        while heap:
            _, _, gval, cur = heapq.heappop(heap)
            if gval > g[cur]:
                continue                                   # bản ghi cũ
            expanded += 1
            if cur == goal:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                return path[::-1], expanded
            for dr, dc in DIRS:
                nb = (cur[0] + dr, cur[1] + dc)
                if not passable(nb):
                    continue
                ng = gval + 1                              # chi phí mỗi bước = 1
                if ng < g.get(nb, float("inf")):
                    g[nb], parent[nb] = ng, cur
                    heapq.heappush(heap, (ng + self.weight * manhattan(nb, goal), next(tie), ng, nb))
        return None, expanded


def bfs_distances(passable, start):
    dist, queue = {start: 0}, deque([start])
    while queue:
        cur = queue.popleft()
        for dr, dc in DIRS:
            nb = (cur[0] + dr, cur[1] + dc)
            if nb not in dist and passable(nb):
                dist[nb] = dist[cur] + 1
                queue.append(nb)
    return dist


class WeightedAStarAgent:
    """Có đường tới đích trên bản đồ đã biết -> đi theo Weighted A*.
    Chưa có đường (thiếu thông tin) -> chọn ô biên tốt nhất rồi dùng Weighted A* đi tới đó để khám phá."""
    name = "Weighted A*"

    def __init__(self, weight=1.5, risk_fn=no_risk):
        self.weight, self.risk_fn = weight, risk_fn
        self.planner = WeightedAStar(weight)
        self.reset()

    def reset(self):
        self.target, self.expanded = None, 0

    def decide(self, robot):
        path, n = self.planner.search(robot.is_passable, robot.pos, robot.goal)
        self.expanded += n
        if path:
            self.target = None
            return path[1], (f"Weighted A* (w={self.weight}): đã có đường tới đích trên bản đồ đã biết, "
                             f"dài {len(path) - 1} bước. Đi {direction_name(robot.pos, path[1])}.")
        # Chưa thấy đường -> khám phá biên
        dist = bfs_distances(robot.is_passable, robot.pos)
        frontiers = [p for p in dist if robot.is_frontier(p)]
        if not frontiers:
            return None, "Không còn ô biên nào để khám phá và chưa có đường tới đích."
        if self.target not in frontiers:                   # giữ mục tiêu cũ cho tới khi tới nơi
            risks = self.risk_fn(robot, frontiers)
            score = lambda i: dist[frontiers[i]] + self.weight * manhattan(frontiers[i], robot.goal) + 2 * risks[i]
            self.target = frontiers[min(range(len(frontiers)), key=score)]
        path, n = self.planner.search(robot.is_passable, robot.pos, self.target)
        self.expanded += n
        if not path or len(path) < 2:
            return None, "Không tìm được đường tới ô biên cần khám phá."
        return path[1], (f"Chưa có đường tới đích. Khám phá: đi tới ô biên {self.target}. "
                         f"Đi {direction_name(robot.pos, path[1])}.")


# ================================ LRTA* =====================================
class LRTAStarAgent:
    """Learning Real-Time A*: H(s) = min_a { c(s,a) + H(s') }, rồi đi tới s' đạt giá trị nhỏ nhất."""
    name = "LRTA*"

    def __init__(self, risk_fn=no_risk):
        self.risk_fn = risk_fn
        self.reset()

    def reset(self):
        self.H = {}              # giá trị H đã học; ô chưa học dùng Manhattan tới đích
        self.expanded = 0

    def h(self, p, goal):
        return self.H.get(p, manhattan(p, goal))

    def decide(self, robot):
        moves = robot.valid_moves()
        if not moves:
            return None, "Robot bị bao vây, không có hành động hợp lệ."
        self.expanded += 1
        risks = self.risk_fn(robot, moves)
        # f = c + H(s'), c = 1. Hòa nhau thì chọn ô có rủi ro (ML) thấp hơn, rồi theo thứ tự Up, Down, Left, Right
        scored = sorted((1 + self.h(m, robot.goal), risks[i], i, m) for i, m in enumerate(moves))
        best_f, _, _, best = scored[0]
        old = self.h(robot.pos, robot.goal)
        self.H[robot.pos] = best_f                         # cập nhật H(s)
        detail = ", ".join(f"{direction_name(robot.pos, m)}={1 + self.h(m, robot.goal)}" for m in moves)
        return best, (f"LRTA*: f = 1 + H của các ô kề: {detail}. "
                      f"Cập nhật H{robot.pos} từ {old} thành {best_f}, đi {direction_name(robot.pos, best)}.")
