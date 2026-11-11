"""main.py - chương trình chính: khởi tạo hệ thống, vòng lặp Pygame, điều phối các thành phần.
Chạy:  python main.py
"""
import sys
import pygame
from simulation import Simulation
from ml_model import MachineLearningModel
from experiments import run_all


class App:
    """Trạng thái ứng dụng: lựa chọn của người dùng + mô phỏng hiện tại + bảng kết quả. Không phụ thuộc Pygame."""

    def __init__(self):
        self.model = MachineLearningModel()
        self.model.load_or_train()                           # lần đầu sẽ huấn luyện và lưu risk_model.joblib
        self.map_id, self.algo, self.weight, self.speed = 1, "astar", 1.5, 350
        self.use_ml = False
        self.results = {}                                    # (bản đồ, thuật toán, có ML) -> thống kê
        self.load()

    @property
    def delay(self):                                         # ms giữa hai bước tự động
        return 520 - self.speed

    def load(self):
        self.sim = Simulation(self.map_id, self.algo, risk_model=self.model, use_ml=self.use_ml, weight=self.weight)

    def tick(self):
        """Một bước mô phỏng; khi kết thúc thì ghi kết quả vào bảng so sánh."""
        self.sim.step()
        if self.sim.finished:
            self.results[(self.map_id, self.algo, self.use_ml and self.model.available)] = self.sim.stats()

    def do(self, action):
        kind = action[0]
        if kind == "slider":
            _, name, value = action
            if name == "speed":
                self.speed = value
            elif value != self.weight:
                self.weight = value
                self.load()
            return
        key = action[1]
        if key == "start":
            self.sim.start()
        elif key == "pause":
            self.sim.pause()
        elif key == "step":
            self.sim.pause()
            self.tick()
        elif key == "reset":
            self.load()
        elif key in ("astar", "lrta"):
            self.algo = key
            self.load()
        elif key.startswith("map"):
            self.map_id = int(key[3:])
            self.load()
        elif key == "ml":
            if self.model.available:
                self.use_ml = not self.use_ml
                self.load()
        elif key == "toggle":
            self.sim.toggle()
        elif key == "cmp":
            self.results.update(run_all(self.model, self.weight, with_ml=True))


def main():
    from ui import Interface, PAGE_W, VIEW_H
    pygame.init()
    screen = pygame.display.set_mode((PAGE_W, VIEW_H))
    pygame.display.set_caption("Robot thông minh tìm đường và khám phá mê cung")
    app, ui, clock, last = App(), Interface(screen), pygame.time.Clock(), 0
    keys = {pygame.K_SPACE: "toggle", pygame.K_n: "step", pygame.K_r: "reset", pygame.K_1: "map1",
            pygame.K_2: "map2", pygame.K_3: "map3", pygame.K_w: "astar", pygame.K_l: "lrta", pygame.K_m: "ml"}
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
                ui.toggle_theme()
            if e.type == pygame.KEYDOWN and e.key in keys:
                app.do(("click", keys[e.key]))
            action = ui.handle(e)
            if action:
                app.do(action)
        now = pygame.time.get_ticks()
        if app.sim.running and now - last >= app.delay:      # tự chạy từng bước theo tốc độ đã chọn
            app.tick()
            last = now
        ui.draw(app)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
