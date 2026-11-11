"""robot.py - ROBOT (tác tử): lưu vị trí, lịch sử, bản đồ đã biết. Robot KHÔNG biết trước bản đồ."""
from environment import DIRS

IDLE, RUNNING, PAUSED = "Chưa bắt đầu", "Đang chạy", "Đang tạm dừng"
DONE, STUCK = "Đã hoàn thành", "Không tìm thấy hướng di chuyển phù hợp"


class Robot:
    def __init__(self, env):
        # Robot chỉ được biết kích thước bản đồ, điểm xuất phát và điểm đích
        self.rows, self.cols = env.rows, env.cols
        self.start, self.goal = env.start, env.goal
        self.reset()

    def reset(self):
        self.pos = self.start
        self.steps = 0
        self.path = [self.start]            # lịch sử di chuyển
        self.visited = {self.start: 1}      # ô đã đi qua -> số lần đi qua
        self.known = {}                     # ô đã quan sát -> '#' hoặc '.'
        self.status = IDLE

    # ---- cảm nhận -------------------------------------------------------
    def observe(self, env):
        """Quan sát các ô quanh vị trí hiện tại và cập nhật bản đồ đã biết."""
        self.known.update(env.observe(self.pos))

    # ---- tri thức / luật suy luận ----------------------------------------
    def in_bounds(self, p):
        return 0 <= p[0] < self.rows and 0 <= p[1] < self.cols

    def is_passable(self, p):
        """Luật: chỉ đi vào ô đã biết là ô trống (đích luôn được phép). Ô tường/ô chưa biết thì không."""
        return self.in_bounds(p) and (self.known.get(p) == "." or p == self.goal)

    def is_frontier(self, p):
        """Ô biên: ô đi được có ít nhất một ô kề chưa được khám phá."""
        for dr, dc in DIRS:
            n = (p[0] + dr, p[1] + dc)
            if self.in_bounds(n) and n not in self.known and n != self.goal:
                return True
        return False

    def valid_moves(self):
        return [(self.pos[0] + dr, self.pos[1] + dc) for dr, dc in DIRS
                if self.is_passable((self.pos[0] + dr, self.pos[1] + dc))]

    # ---- hành động --------------------------------------------------------
    def move_to(self, p):
        self.pos = p
        self.steps += 1
        self.path.append(p)
        self.visited[p] = self.visited.get(p, 0) + 1
