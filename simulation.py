"""simulation.py - điều phối Environment + Robot + thuật toán, thu thập thống kê (không phụ thuộc Pygame)."""
import time
from environment import Environment
from robot import Robot, IDLE, RUNNING, PAUSED, DONE, STUCK
from algorithms import WeightedAStarAgent, LRTAStarAgent, no_risk

MAX_STEPS = 3000


class Simulation:
    def __init__(self, map_id=1, algorithm="astar", env=None, risk_model=None, use_ml=False, weight=1.5):
        self.risk_model, self.use_ml, self.weight = risk_model, use_ml, weight
        self.algorithm = algorithm
        self.load_map(map_id, env)

    # ---- thiết lập ----------------------------------------------------------
    def load_map(self, map_id=1, env=None):
        self.env = env or Environment(map_id)
        self.reset()

    def set_algorithm(self, algorithm):
        self.algorithm = algorithm
        self.reset()

    def toggle_ml(self):
        self.use_ml = not self.use_ml
        self.reset()

    def reset(self):
        self.robot = Robot(self.env)
        risk = self._risk if (self.use_ml and self.ml_available) else no_risk
        self.agent = (WeightedAStarAgent(self.weight, risk) if self.algorithm == "astar"
                      else LRTAStarAgent(risk))
        self.compute_ms = 0.0
        self.message = "Robot đứng ở điểm xuất phát. Bấm Start hoặc Step."
        self.robot.observe(self.env)                       # quan sát lần đầu

    @property
    def ml_available(self):
        return self.risk_model is not None and self.risk_model.available

    def _risk(self, robot, positions):
        return self.risk_model.predict_risk(robot, positions)

    # ---- điều khiển -----------------------------------------------------------
    @property
    def finished(self):
        return self.robot.status in (DONE, STUCK)

    @property
    def running(self):
        return self.robot.status == RUNNING

    def start(self):
        if not self.finished:
            self.robot.status = RUNNING

    def pause(self):
        if self.robot.status == RUNNING:
            self.robot.status = PAUSED

    def toggle(self):
        self.pause() if self.running else self.start()

    def step(self):
        """Thực hiện đúng một bước: quan sát -> thuật toán quyết định -> kiểm tra hợp lệ -> di chuyển."""
        r = self.robot
        if self.finished:
            return
        if r.status == IDLE:
            r.status = PAUSED
        t0 = time.perf_counter()
        nxt, self.message = self.agent.decide(r)
        self.compute_ms += (time.perf_counter() - t0) * 1000
        if nxt is None:
            r.status = STUCK
            return
        if not self.env.is_free(nxt):                      # không cho đi xuyên tường / ra ngoài bản đồ
            r.status, self.message = STUCK, "Hành động không hợp lệ (tường hoặc ngoài bản đồ)."
            return
        r.move_to(nxt)
        r.observe(self.env)
        if r.pos == r.goal:
            r.status, self.message = DONE, "Robot đã tới đích."
        elif r.steps >= MAX_STEPS:
            r.status, self.message = STUCK, "Vượt quá số bước tối đa."

    def run_to_end(self):
        self.start()
        while not self.finished:
            self.step()

    # ---- thống kê ---------------------------------------------------------------
    def stats(self):
        r, e = self.robot, self.env
        return {
            "algorithm": self.agent.name + (" + ML" if self.use_ml and self.ml_available else ""),
            "map": e.name,
            "status": r.status,
            "success": r.status == DONE,
            "steps": r.steps,
            "opt": e.optimal,                              # đường ngắn nhất thật (BFS)
            "visited": len(r.visited),                     # ô đã đi qua
            "observed": len(r.known),                      # ô đã quan sát (đã biết)
            "explore_rate": len(r.known) / (e.rows * e.cols),
            "time_ms": self.compute_ms,
            "expanded": self.agent.expanded,
        }
