"""ml_model.py - MachineLearningModel: dự đoán ô có RỦI RO CAO hay không (nhị phân: 0 = thấp, 1 = cao).

Dữ liệu: sinh từ nhiều bản đồ ngẫu nhiên (seed cố định). Mỗi ô có 4 đặc trưng:
  [số ô tường quanh, số hướng đi hợp lệ, số lần robot đã đi qua, khoảng cách Manhattan tới đích]
Nhãn: 1 nếu (đường đi thật tới đích) - (khoảng cách Manhattan) > 4, tức là ô đó buộc phải đi vòng nhiều.
Mô hình: RandomForestClassifier (scikit-learn), đánh giá trên 25% dữ liệu kiểm tra.
Chạy riêng:  python ml_model.py   (huấn luyện + in kết quả đánh giá)
"""
import os
import random
from collections import Counter
from environment import DIRS, random_environment, distances_from
from simulation import Simulation
from algorithms import manhattan

try:
    import numpy as np
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score
    from sklearn.model_selection import train_test_split
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_model.joblib")


def cell_features(known, rows, cols, pos, goal, visits):
    """Đặc trưng của một ô, tính từ bản đồ mà robot đã biết (ô chưa biết không tính là tường)."""
    walls = free = 0
    for dr, dc in DIRS:
        n = (pos[0] + dr, pos[1] + dc)
        if not (0 <= n[0] < rows and 0 <= n[1] < cols) or known.get(n) == "#":
            walls += 1
        elif known.get(n) == "." or n == goal:
            free += 1
    return [walls, free, visits, manhattan(pos, goal)]


def generate_dataset(n_maps=120, seed=7):
    rng, X, y = random.Random(seed), [], []
    for _ in range(n_maps):
        env = random_environment(rng)
        sim = Simulation(env=env, algorithm="lrta")        # chạy LRTA* để lấy số lần đi qua mỗi ô
        sim.run_to_end()
        full = {(r, c): env.cells[r][c] for r in range(env.rows) for c in range(env.cols)}
        for pos, d in distances_from(env, env.goal).items():
            if pos == env.goal:
                continue
            X.append(cell_features(full, env.rows, env.cols, pos, env.goal, sim.robot.visited.get(pos, 0)))
            y.append(1 if d - manhattan(pos, env.goal) > 4 else 0)
    return X, y


class MachineLearningModel:
    def __init__(self):
        self.model, self.info = None, None

    @property
    def available(self):
        return SKLEARN_OK and self.model is not None

    def train(self, verbose=True):
        if not SKLEARN_OK:
            print("Chưa cài scikit-learn -> bỏ qua phần Machine Learning.")
            return
        X, y = generate_dataset()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=1)     # 75% huấn luyện / 25% kiểm tra
        self.model = RandomForestClassifier(n_estimators=60, max_depth=8, class_weight="balanced", random_state=1)
        self.model.fit(Xtr, ytr)
        pred = self.model.predict(Xte)
        self.info = {"n": len(X), "acc": accuracy_score(yte, pred),
                     "base": max(Counter(yte).values()) / len(yte),                       # đoán luôn lớp phổ biến nhất
                     "prec": precision_score(yte, pred, zero_division=0),
                     "rec": recall_score(yte, pred, zero_division=0)}
        if verbose:
            i = self.info
            print(f"[ML] {i['n']} mẫu, nhãn: {dict(sorted(Counter(y).items()))}")
            print(f"[ML] chính xác {i['acc']:.2f} (đoán lớp phổ biến: {i['base']:.2f}), precision {i['prec']:.2f}, recall {i['rec']:.2f}")
            print(classification_report(yte, pred, target_names=["Thấp", "Cao"], zero_division=0))
        joblib.dump({"model": self.model, "info": self.info}, MODEL_PATH)

    def load_or_train(self):
        if not SKLEARN_OK:
            print("Chưa cài scikit-learn -> chạy không có Machine Learning.")
            return
        if os.path.exists(MODEL_PATH):
            try:
                data = joblib.load(MODEL_PATH)
                self.model, self.info = data["model"], data["info"]
                return
            except Exception:
                pass
        print("[ML] Lần chạy đầu: đang huấn luyện mô hình, vui lòng đợi vài giây...")
        self.train()

    def predict_risk(self, robot, positions):
        X = [cell_features(robot.known, robot.rows, robot.cols, p, robot.goal, robot.visited.get(p, 0))
             for p in positions]
        return [int(v) for v in self.model.predict(np.array(X))]


if __name__ == "__main__":
    MachineLearningModel().train()
