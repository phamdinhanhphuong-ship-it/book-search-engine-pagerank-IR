# -------------------------------------------------------------
# File: compare_methods.py
# Vai trò: So sánh tất cả các phương pháp: Lexical, PageRank, Hybrid, LTR
# Chức năng: Tính P@10, Recall@100, NDCG@10 cho mỗi run file và in bảng so sánh.
# Sử dụng:
#   python TH8/compare_methods.py
# -------------------------------------------------------------
import json
import math
from collections import defaultdict
from pathlib import Path

from config import QRELS_FILE, RESULTS_DIR, RUNS_DIR


# ──────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────

def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    if not path.exists():
        raise FileNotFoundError(f'Không tìm thấy qrels: {path}')
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                qid, doc_id, rel = parts[0], parts[1], int(parts[2])
                qrels[qid][doc_id] = rel
    return qrels


def load_run(path: Path) -> dict[str, list[tuple[str, int, float]]]:
    """Đọc TREC run file, trả về {qid: [(doc_id, rank, score), ...]}."""
    runs: dict[str, list] = defaultdict(list)
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 6:
                continue
            qid, _, doc_id, rank, score, _ = parts[:6]
            runs[qid].append((doc_id, int(rank), float(score)))
    for qid in runs:
        runs[qid].sort(key=lambda x: x[1])
    return runs


# ──────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────

def precision_at_k(ranked: list, relevant: dict, k: int = 10) -> float:
    top = [d for d, _, _ in ranked[:k]]
    hits = sum(1 for d in top if relevant.get(d, 0) > 0)
    return hits / k if k else 0.0


def recall_at_k(ranked: list, relevant: dict, k: int = 100) -> float:
    rel_set = {d for d, r in relevant.items() if r > 0}
    if not rel_set:
        return 0.0
    top_set = {d for d, _, _ in ranked[:k]}
    return len(top_set & rel_set) / len(rel_set)


def ndcg_at_k(ranked: list, relevant: dict, k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain @k."""
    def dcg(docs, k):
        gain = 0.0
        for i, doc_id in enumerate(docs[:k], start=1):
            rel = relevant.get(doc_id, 0)
            gain += rel / math.log2(i + 1)
        return gain

    top_docs = [d for d, _, _ in ranked[:k]]
    actual_dcg = dcg(top_docs, k)

    # Ideal DCG: sort by relevance descending
    ideal_docs = sorted(relevant.keys(), key=lambda d: relevant[d], reverse=True)
    ideal_dcg = dcg(ideal_docs, k)

    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def evaluate_run(run_path: Path, qrels: dict) -> dict:
    runs = load_run(run_path)
    p10_list, r100_list, ndcg_list = [], [], []
    per_query = {}

    for qid, relevant in qrels.items():
        ranked = runs.get(qid, [])
        p10 = precision_at_k(ranked, relevant, k=10)
        r100 = recall_at_k(ranked, relevant, k=100)
        ndcg = ndcg_at_k(ranked, relevant, k=10)
        per_query[qid] = {'P@10': p10, 'Recall@100': r100, 'NDCG@10': ndcg}
        p10_list.append(p10)
        r100_list.append(r100)
        ndcg_list.append(ndcg)

    return {
        'run_file': run_path.name,
        'mean_P@10': sum(p10_list) / len(p10_list) if p10_list else 0.0,
        'mean_Recall@100': sum(r100_list) / len(r100_list) if r100_list else 0.0,
        'mean_NDCG@10': sum(ndcg_list) / len(ndcg_list) if ndcg_list else 0.0,
        'per_query': per_query,
    }


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    qrels = load_qrels(QRELS_FILE)

    # Tìm tất cả run file
    run_files = sorted(RUNS_DIR.glob('run_*.txt'))
    if not run_files:
        print('Không tìm thấy run file nào trong thư mục runs/')
        return

    results = []
    for run_path in run_files:
        try:
            summary = evaluate_run(run_path, qrels)
            results.append(summary)
        except Exception as e:
            print(f'[WARN] Bỏ qua {run_path.name}: {e}')

    # ── In bảng so sánh ──
    header = f"{'Method':<22} {'P@10':>8} {'Recall@100':>12} {'NDCG@10':>10}"
    print('\n' + '=' * len(header))
    print('SO SÁNH CÁC PHƯƠNG PHÁP')
    print('=' * len(header))
    print(header)
    print('-' * len(header))

    for r in results:
        name = r['run_file'].replace('run_', '').replace('.txt', '')
        print(
            f"{name:<22} "
            f"{r['mean_P@10']:>8.4f} "
            f"{r['mean_Recall@100']:>12.4f} "
            f"{r['mean_NDCG@10']:>10.4f}"
        )

    print('=' * len(header))

    # ── Lưu JSON chi tiết ──
    out_path = RESULTS_DIR / 'comparison_all_methods.json'
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nKết quả chi tiết lưu tại: {out_path}')

    # ── In kết quả theo query cho run LTR (nếu có) ──
    ltr_result = next((r for r in results if 'ltr' in r['run_file']), None)
    if ltr_result:
        print('\nKết quả LTR theo từng query:')
        print(f"  {'Query':<8} {'P@10':>8} {'Recall@100':>12} {'NDCG@10':>10}")
        print(f"  {'-'*40}")
        for qid, metrics in sorted(ltr_result['per_query'].items()):
            print(
                f"  {qid:<8} "
                f"{metrics['P@10']:>8.4f} "
                f"{metrics['Recall@100']:>12.4f} "
                f"{metrics['NDCG@10']:>10.4f}"
            )


if __name__ == '__main__':
    main()
