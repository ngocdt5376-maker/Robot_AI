"""experiments.py - thực nghiệm không cần giao diện (cũng được ui.py/main.py gọi cho nút "Chạy cả 2 thuật toán").
Chạy:  python experiments.py            (thêm --ml để chạy cả bản có hỗ trợ ML)
Kết quả in ra màn hình và lưu vào results.csv (mở bằng Excel).
"""
import argparse
import csv
from simulation import Simulation
from ml_model import MachineLearningModel


def run_config(map_id, algo, use_ml, model, weight):
    """Chạy một cấu hình từ đầu tới khi kết thúc, trả về dict thống kê."""
    sim = Simulation(map_id, algo, risk_model=model, use_ml=use_ml, weight=weight)
    sim.run_to_end()
    return sim.stats()


def run_all(model=None, weight=1.5, with_ml=False):
    """Cùng bản đồ, cùng điểm xuất phát/đích cho mọi cấu hình. Trả về {(map, thuật toán, có ML): thống kê}."""
    ml_options = [False, True] if (with_ml and model is not None and model.available) else [False]
    return {(m, a, ml): run_config(m, a, ml, model, weight)
            for m in (1, 2, 3) for a in ("astar", "lrta") for ml in ml_options}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weight", type=float, default=1.5, help="hệ số w của Weighted A*")
    ap.add_argument("--ml", action="store_true", help="chạy thêm các cấu hình có ML")
    args = ap.parse_args()
    model = None
    if args.ml:
        model = MachineLearningModel()
        model.load_or_train()
    rows = list(run_all(model, args.weight, args.ml).values())

    print(f"{'Bản đồ':<28}{'Thuật toán':<18}{'Kết quả':<11}{'Bước':>6}{'Tối ưu':>8}{'Đã đi':>7}{'Quan sát':>10}{'Tỷ lệ KP':>10}{'ms':>9}")
    for s in rows:
        print(f"{s['map']:<28}{s['algorithm']:<18}{'Thành công' if s['success'] else 'Thất bại':<11}{s['steps']:>6}"
              f"{s['opt']:>8}{s['visited']:>7}{s['observed']:>10}{s['explore_rate']:>9.0%}{s['time_ms']:>9.2f}")
    with open("results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("Đã lưu results.csv")


if __name__ == "__main__":
    main()
