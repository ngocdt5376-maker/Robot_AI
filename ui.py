"""ui.py - INTERFACE (Pygame): giao diện giống bản web (cùng bố cục, màu, chữ), vẽ trên một "trang" dài và cuộn bằng chuột.
Interface chỉ vẽ và nhận thao tác; logic nằm ở simulation.py / main.py. handle(event) trả về hành động cho main.py:
    ("click", khóa_nút)  hoặc  ("slider", "speed" | "weight", giá_trị)
"""
import pygame
from environment import MAPS
from robot import IDLE, RUNNING, PAUSED, DONE, STUCK

PAGE_W, PAGE_H, VIEW_H = 1100, 1212, 700
Z = 40                                                      # kích thước một ô (pixel)
AN = {"astar": "Weighted A*", "lrta": "LRTA*"}
LIGHT = dict(bg=(244, 246, 250), card=(255, 255, 255), tx=(27, 34, 51), mut=(102, 112, 133), bd=(216, 221, 231),
             unk=(170, 178, 197), free=(255, 255, 255), wall=(31, 38, 56), vis=(188, 214, 255),
             acc=(37, 99, 235), gl=(22, 163, 74), rb=(225, 29, 72))
DARK = dict(bg=(15, 20, 32), card=(24, 32, 51), tx=(232, 236, 245), mut=(154, 166, 189), bd=(43, 54, 80),
            unk=(59, 69, 94), free=(232, 236, 245), wall=(5, 7, 12), vis=(74, 120, 196),
            acc=(110, 160, 255), gl=(74, 222, 128), rb=(251, 113, 133))
SLIDERS = {"speed": dict(lo=20, hi=500, step=1, rect=pygame.Rect(786, 0, 228, 6)),
           "weight": dict(lo=1, hi=5, step=0.5, rect=pygame.Rect(786, 0, 228, 6))}


def make_font(size, bold=False):
    # Segoe UI / Tahoma / Arial hiển thị được tiếng Việt có dấu trên Windows
    return pygame.font.SysFont("segoeui,tahoma,arial,dejavusans", size, bold=bold)


def wrap(text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.size(trial)[0] <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + ([line] if line else [])


class Interface:
    def __init__(self, screen):
        self.screen = screen
        self.page = pygame.Surface((PAGE_W, PAGE_H))
        self.scroll, self.dark, self.dragging = 0, False, None
        self.f, self.fb = make_font(18), make_font(18, True)
        self.fs, self.fsb = make_font(15), make_font(15, True)
        self.fh = make_font(26, True)
        R = pygame.Rect
        # ---- các thẻ (card), toạ độ trên trang ----
        self.map_card, self.msg_card = R(16, 56, 640, 536), R(16, 606, 640, 140)
        self.ctl_card, self.st_card, self.cmp_card = R(672, 56, 412, 372), R(672, 442, 412, 326), R(16, 782, 1068, 416)
        # ---- nút ----
        x = 686
        b = {}
        for i, k in enumerate(["start", "pause", "step", "reset"]):
            b[k] = R(x + i * 98, 70, 90, 32)
        b["astar"], b["lrta"] = R(x, 110, 188, 32), R(x + 196, 110, 188, 32)
        for i in range(3):
            b[f"map{i + 1}"] = R(x + i * 131, 150, 122, 32)
        b["ml"] = R(x, 190, 384, 32)
        b["cmp"] = R(30, 826, 360, 32)
        self.btn = b
        self.labels = {"start": "Start", "pause": "Pause", "step": "Step", "reset": "Reset",
                       "astar": "Weighted A* (W)", "lrta": "LRTA* (L)", "map1": "Map 1", "map2": "Map 2",
                       "map3": "Map 3", "cmp": "Chạy cả 2 thuật toán trên 3 bản đồ"}
        SLIDERS["speed"]["rect"].y, SLIDERS["weight"]["rect"].y = 312, 344

    # ------------------------------------------------------------------ nhập liệu
    def toggle_theme(self):
        self.dark = not self.dark

    def handle(self, e):
        max_scroll = PAGE_H - VIEW_H
        if e.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(max_scroll, self.scroll - e.y * 50))
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            self.scroll = max(0, min(max_scroll, self.scroll + (VIEW_H - 60) * (1 if e.key == pygame.K_PAGEDOWN else -1)))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            p = (e.pos[0], e.pos[1] + self.scroll)
            for k, r in self.btn.items():
                if r.collidepoint(p):
                    return ("click", k)
            for k, s in SLIDERS.items():
                if s["rect"].inflate(0, 22).collidepoint(p):
                    self.dragging = k
                    return self._slide(k, p[0])
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            return self._slide(self.dragging, e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = None
        return None

    def _slide(self, k, mx):
        s = SLIDERS[k]
        t = max(0.0, min(1.0, (mx - s["rect"].x) / s["rect"].w))
        v = s["lo"] + round(t * (s["hi"] - s["lo"]) / s["step"]) * s["step"]
        return ("slider", k, v)

    # ------------------------------------------------------------------ vẽ
    def text(self, s, pos, font=None, color=None, right=False):
        img = (font or self.f).render(s, True, color or self.C["tx"])
        self.page.blit(img, (pos[0] - img.get_width(), pos[1]) if right else pos)

    def card(self, rect):
        pygame.draw.rect(self.page, self.C["card"], rect, border_radius=12)
        pygame.draw.rect(self.page, self.C["bd"], rect, 1, border_radius=12)

    def draw(self, app):
        self.C = DARK if self.dark else LIGHT
        self.mouse = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] + self.scroll)
        self.page.fill(self.C["bg"])
        self.text("Robot thông minh tìm đường và khám phá mê cung", (16, 14), self.fh)
        for c in (self.map_card, self.msg_card, self.ctl_card, self.st_card, self.cmp_card):
            self.card(c)
        self.draw_map(app.sim)
        self.draw_legend()
        self.draw_message(app.sim)
        self.draw_controls(app)
        self.draw_stats(app.sim)
        self.draw_compare(app)
        self.screen.blit(self.page, (0, 0), pygame.Rect(0, self.scroll, PAGE_W, VIEW_H))
        if PAGE_H > VIEW_H:                                  # thanh cuộn
            h = max(40, VIEW_H * VIEW_H // PAGE_H)
            y = self.scroll * (VIEW_H - h) // (PAGE_H - VIEW_H)
            pygame.draw.rect(self.screen, self.C["bd"], (PAGE_W - 6, y, 4, h), border_radius=2)

    def draw_map(self, sim):
        C, r, env = self.C, sim.robot, sim.env
        ox, oy = 36, 76
        for i in range(env.rows):
            for j in range(env.cols):
                p, v = (i, j), r.known.get((i, j))
                color = C["unk"] if v is None else C["wall"] if v == "#" else C["vis"] if p in r.visited else C["free"]
                rect = pygame.Rect(ox + j * Z, oy + i * Z, Z, Z)
                pygame.draw.rect(self.page, color, rect)
                pygame.draw.rect(self.page, C["bd"], rect, 1)
        mid = lambda p: (ox + p[1] * Z + Z // 2, oy + p[0] * Z + Z // 2)
        if len(r.path) >= 2:                                 # đường đi (trong suốt 70%)
            layer = pygame.Surface((env.cols * Z, env.rows * Z), pygame.SRCALPHA)
            pts = [(mid(p)[0] - ox, mid(p)[1] - oy) for p in r.path]
            pygame.draw.lines(layer, C["acc"] + (178,), False, pts, 4)
            self.page.blit(layer, (ox, oy))
        for p, t, c in [(r.start, "S", "acc"), (r.goal, "G", "gl")]:
            rect = pygame.Rect(ox + p[1] * Z + 4, oy + p[0] * Z + 4, Z - 8, Z - 8)
            pygame.draw.rect(self.page, C[c], rect)
            img = self.fb.render(t, True, (255, 255, 255))
            self.page.blit(img, img.get_rect(center=rect.center))
        pygame.draw.circle(self.page, C["rb"], mid(r.pos), 11)
        pygame.draw.circle(self.page, (255, 255, 255), mid(r.pos), 11, 2)

    def draw_legend(self):
        C = self.C
        items = [("unk", "Chưa khám phá"), ("free", "Ô trống đã biết"), ("vis", "Đã đi qua"), ("wall", "Tường"),
                 ("acc", "S xuất phát"), ("gl", "G đích"), ("rb", "Robot")]
        for i, (k, t) in enumerate(items):
            x, y = 36 + (i % 4) * 150, 534 + (i // 4) * 24
            if k == "rb":
                pygame.draw.circle(self.page, C[k], (x + 7, y + 8), 7)
            else:
                pygame.draw.rect(self.page, C[k], (x, y + 1, 14, 14), border_radius=3)
                pygame.draw.rect(self.page, C["bd"], (x, y + 1, 14, 14), 1, border_radius=3)
            self.text(t, (x + 20, y - 1), self.fs, C["mut"])

    def draw_message(self, sim):
        self.text("Giải thích hành động", (30, 618), self.fb)
        for i, line in enumerate(wrap(sim.message, self.fs, 612)[:4]):
            self.text(line, (30, 648 + i * 20), self.fs)

    def button(self, key, label, on):
        C, r = self.C, self.btn[key]
        hot = r.collidepoint(self.mouse)
        pygame.draw.rect(self.page, C["acc"] if on else C["bg"], r, border_radius=8)
        pygame.draw.rect(self.page, C["acc"] if (on or hot) else C["bd"], r, 1, border_radius=8)
        img = self.f.render(label, True, (255, 255, 255) if on else C["tx"])
        self.page.blit(img, img.get_rect(center=r.center))

    def slider(self, key, value, label, show_value):
        C, s = self.C, SLIDERS[key]
        r = s["rect"]
        self.text(label, (686, r.y - 11))
        pygame.draw.rect(self.page, C["bd"], r, border_radius=3)
        t = (value - s["lo"]) / (s["hi"] - s["lo"])
        pygame.draw.rect(self.page, C["acc"], (r.x, r.y, int(r.w * t), r.h), border_radius=3)
        pygame.draw.circle(self.page, C["acc"], (r.x + int(r.w * t), r.y + 3), 9)
        if show_value:
            self.text(f"{value:g}", (1068, r.y - 11), self.fb, right=True)

    def draw_controls(self, app):
        sim = app.sim
        on = {"astar": sim.algorithm == "astar", "lrta": sim.algorithm == "lrta", f"map{sim.env.map_id}": True,
              "ml": app.use_ml}
        for k in self.btn:
            if k in ("ml", "cmp"):
                continue
            self.button(k, self.labels[k], on.get(k, False))
        if app.model.available:
            self.button("ml", "ML hỗ trợ: " + ("BẬT" if app.use_ml else "TẮT") + " (M)", app.use_ml)
            i = app.model.info
            p = lambda x: f"{round(x * 100)}%"
            info = (f"Random Forest, {i['n']} mẫu, kiểm tra: chính xác {p(i['acc'])} (đoán lớp phổ biến: {p(i['base'])}), "
                    f"precision {p(i['prec'])}, recall {p(i['rec'])}.")
        else:
            self.button("ml", "ML: chưa có scikit-learn", False)
            info = "Cài scikit-learn (pip install scikit-learn) để dùng phần Machine Learning."
        for k, line in enumerate(wrap(info, self.fs, 384)[:3]):
            self.text(line, (686, 230 + k * 18), self.fs, self.C["mut"])
        self.slider("speed", app.speed, "Tốc độ", False)
        self.slider("weight", app.weight, "Hệ số w", True)
        hint = ("Phím tắt: Space chạy/dừng · N một bước · R đặt lại · 1/2/3 bản đồ · W, L chọn thuật toán · "
                "M bật/tắt ML · T đổi sáng/tối · cuộn chuột để xem bảng so sánh")
        for k, line in enumerate(wrap(hint, self.fs, 384)[:3]):
            self.text(line, (686, 368 + k * 18), self.fs, self.C["mut"])

    def draw_stats(self, sim):
        s, r = sim.stats(), sim.robot
        self.text("Thống kê", (686, 454), self.fb)
        rows = [("Thuật toán", s["algorithm"]), ("Bản đồ", s["map"]), ("Trạng thái", s["status"]),
                ("Số bước", s["steps"]), ("Đường ngắn nhất (BFS)", s["opt"]), ("Vị trí robot", f"({r.pos[0]}, {r.pos[1]})"),
                ("Ô đã đi qua", s["visited"]),
                ("Ô đã quan sát", f"{s['observed']} / {sim.env.rows * sim.env.cols}"),
                ("Tỷ lệ khám phá", f"{round(s['explore_rate'] * 100)}%"), ("Số nút mở rộng", s["expanded"]),
                ("Thời gian xử lý", f"{s['time_ms']:.2f} ms")]
        for i, (k, v) in enumerate(rows):
            y = 488 + i * 24
            self.text(k, (686, y))
            font = self.fb
            if self.f.size(k)[0] + font.size(str(v))[0] > 370:
                font = self.fsb                              # giá trị dài (vd. trạng thái) -> dùng chữ nhỏ hơn
            self.text(str(v), (1068, y + (0 if font is self.fb else 2)), font, right=True)

    def draw_compare(self, app):
        C = self.C
        self.text("So sánh thực nghiệm", (30, 796), self.fb)
        self.button("cmp", self.labels["cmp"], False)
        note = "Cùng điểm xuất phát và đích; số liệu cũng được ghi lại khi bạn tự chạy từng cấu hình."
        for k, line in enumerate(wrap(note, self.fs, 640)[:2]):
            self.text(line, (410, 828 + k * 18), self.fs, C["mut"])
        cols = [("Bản đồ", 0), ("Thuật toán", 200), ("Kết quả", 350), ("Số bước", 450), ("Tối ưu (BFS)", 530),
                ("Ô đã đi", 650), ("Ô quan sát", 740), ("Tỷ lệ KP", 850), ("Thời gian (ms)", 940)]
        x0, y = 30, 876
        for name, dx in cols:
            self.text(name, (x0 + dx, y), self.fsb)
        pygame.draw.line(self.page, C["bd"], (x0, y + 22), (1068, y + 22))
        y += 28
        for m in (1, 2, 3):
            for a in ("astar", "lrta"):
                for ml in (False, True):
                    res = app.results.get((m, a, ml))
                    if ml and not res:
                        continue
                    self.text(MAPS[m]["name"], (x0, y), self.fs)
                    self.text(AN[a] + (" + ML" if ml else ""), (x0 + 200, y), self.fs)
                    if res:
                        cells = ["Thành công" if res["success"] else "Thất bại", res["steps"], res["opt"],
                                 res["visited"], res["observed"], f"{round(res['explore_rate'] * 100)}%",
                                 f"{res['time_ms']:.2f}"]
                        for (name, dx), v in zip(cols[2:], cells):
                            self.text(str(v), (x0 + dx, y), self.fs)
                    else:
                        self.text("Chưa chạy", (x0 + 350, y), self.fs, C["mut"])
                    pygame.draw.line(self.page, C["bd"], (x0, y + 22), (1068, y + 22))
                    y += 24
