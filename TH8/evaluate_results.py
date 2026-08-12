# -------------------------------------------------------------
# File: evaluate_results.py
# Vai trò: Đánh giá chất lượng kết quả tìm kiếm
# Chức năng: Đọc file qrels.tsv và các file kết quả truy vấn, tính toán các chỉ số đánh giá như Precision@K, Recall@100,
# so sánh hiệu quả giữa các mô hình lexical retrieval, PageRank và Hybrid.
# -------------------------------------------------------------
import argparse
import json
from collections import defaultdict
from pathlib import Path

from config import QRELS_FILE, RESULTS_DIR, RUNS_DIR



def load_qrels(path: Path):
    qrels = defaultdict(dict)
    if not path.exists():
        raise FileNotFoundError(f'Không tìm thấy qrels: {path}')
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            qid, doc_id, rel = line.split('\t')[:3]
            qrels[qid][doc_id] = int(rel)
    return qrels



def load_run(path: Path):
    runs = defaultdict(list)
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            qid, _, doc_id, rank, score, _ = line.strip().split('\t')
            runs[qid].append((doc_id, int(rank), float(score)))
    for qid in runs:
        runs[qid].sort(key=lambda x: x[1])
    return runs



def precision_at_k(ranked_docs, relevant_docs, k=10):
    top_docs = [doc_id for doc_id, _, _ in ranked_docs[:k]]
    if k == 0:
        return 0.0
    hits = sum(1 for doc_id in top_docs if relevant_docs.get(doc_id, 0) > 0)
    return hits / k



def recall_at_k(ranked_docs, relevant_docs, k=100):
    rel_set = {doc_id for doc_id, rel in relevant_docs.items() if rel > 0}
    if not rel_set:
        return 0.0
    top_docs = {doc_id for doc_id, _, _ in ranked_docs[:k]}
    return len(top_docs & rel_set) / len(rel_set)



def evaluate(run_path: Path, qrels_path: Path):
    qrels = load_qrels(qrels_path)
    runs = load_run(run_path)
    per_query = {}
    p10_list, r100_list = [], []

    for qid, relevant_docs in qrels.items():
        ranked_docs = runs.get(qid, [])
        p10 = precision_at_k(ranked_docs, relevant_docs, k=10)
        r100 = recall_at_k(ranked_docs, relevant_docs, k=100)
        per_query[qid] = {'P@10': p10, 'Recall@100': r100}
        p10_list.append(p10)
        r100_list.append(r100)

    summary = {
        'run_file': str(run_path.name),
        'mean_P@10': sum(p10_list) / len(p10_list) if p10_list else 0.0,
        'mean_Recall@100': sum(r100_list) / len(r100_list) if r100_list else 0.0,
        'per_query': per_query,
    }
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate a run file using qrels.tsv')
    parser.add_argument('--run-file', type=Path, default=RUNS_DIR / 'run_w1.0.txt')
    parser.add_argument('--qrels-file', type=Path, default=QRELS_FILE)
    args = parser.parse_args()

    summary = evaluate(args.run_file, args.qrels_file)
    out_path = RESULTS_DIR / f'eval_{args.run_file.stem}.json'
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'Evaluation saved to {out_path}')
