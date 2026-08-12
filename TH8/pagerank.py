# -------------------------------------------------------------
# File: pagerank.py
# Vai trò: Tính điểm PageRank cho các sản phẩm
# Chức năng: Đọc đồ thị liên kết giữa các sản phẩm, sử dụng thuật toán PageRank
# để tính điểm cho từng sản phẩm, lưu kết quả để tích hợp vào hệ thống tìm kiếm.
# -------------------------------------------------------------
import argparse

import networkx as nx

from config import GRAPH_FILE, PAGERANK_FILE, RESULTS_DIR
from utils import write_json



def compute_pagerank(alpha: float = 0.85, max_iter: int = 100):
    if not GRAPH_FILE.exists():
        raise FileNotFoundError(f'Không tìm thấy đồ thị: {GRAPH_FILE}')

    graph = nx.read_edgelist(GRAPH_FILE, create_using=nx.DiGraph(), nodetype=str)
    scores = nx.pagerank(graph, alpha=alpha, max_iter=max_iter, tol=1e-08)

    with PAGERANK_FILE.open('w', encoding='utf-8') as f:
        f.write('doc_id\tpagerank\n')
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            f.write(f'{doc_id}\t{score:.12f}\n')

    write_json(RESULTS_DIR / 'pagerank_top10.json', [{'doc_id': d, 'score': s} for d, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]])
    return scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute PageRank from indexes/graph.edgelist')
    parser.add_argument('--alpha', type=float, default=0.85, help='Damping factor for NetworkX PageRank')
    parser.add_argument('--max-iter', type=int, default=100, help='Number of iterations for PageRank')
    args = parser.parse_args()
    scores = compute_pagerank(alpha=args.alpha, max_iter=args.max_iter)
    print(f'Computed PageRank for {len(scores)} documents. Output: {PAGERANK_FILE}')
