# -------------------------------------------------------------
# File: run_ltr.py
# Vai trò: Chạy hệ thống tìm kiếm với mô hình Learning-to-Rank
# Chức năng:
#   1. Nạp model LTR đã huấn luyện (từ ltr.py).
#   2. Với mỗi query, lấy candidate docs qua lexical retrieval.
#   3. Dùng LTR để xếp hạng lại và lưu run file (định dạng TREC).
#   4. Lưu file kết quả chi tiết (tsv) để so sánh với baseline.
# Sử dụng:
#   python run_ltr.py [--top-k 10]
# -------------------------------------------------------------
import argparse
from pathlib import Path

from config import (
    DOC_STATS_FILE,
    DOC_STORE_FILE,
    INVERTED_INDEX_FILE,
    RESULTS_DIR,
    RUNS_DIR,
)
from ltr import (
    MODEL_FILE,
    get_candidates,
    load_model,
    load_pagerank,
    load_queries,
    ltr_retrieve,
)
from utils import read_json


def main():
    parser = argparse.ArgumentParser(description='Run LTR retrieval and save results')
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--model', type=Path, default=MODEL_FILE)
    args = parser.parse_args()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print('[run_ltr] Đang nạp dữ liệu...')
    inverted_index = read_json(INVERTED_INDEX_FILE, default={})
    stats = read_json(DOC_STATS_FILE, default={})
    doc_store = read_json(DOC_STORE_FILE, default={})
    pagerank_scores = load_pagerank()
    queries = load_queries()

    if not inverted_index:
        raise FileNotFoundError(f'Chưa có inverted index: {INVERTED_INDEX_FILE}')

    print(f'[run_ltr] Nạp mô hình LTR từ: {args.model}')
    model = load_model(args.model)

    run_file = RUNS_DIR / 'run_ltr.txt'
    result_file = RESULTS_DIR / 'results_ltr.txt'

    with run_file.open('w', encoding='utf-8') as run_f, \
         result_file.open('w', encoding='utf-8') as res_f:

        res_f.write('query_id\tdoc_id\tscore\trank\ttitle\n')

        for qid, query_text in queries:
            # Bước 1: Lấy candidate docs qua lexical retrieval
            candidates = get_candidates(query_text, inverted_index, stats)

            if not candidates:
                continue

            # Bước 2: Xếp hạng lại bằng LTR
            ranked = ltr_retrieve(
                query_text, candidates, model,
                inverted_index, stats, pagerank_scores,
                top_k=args.top_k,
            )

            for rank, (doc_id, score) in enumerate(ranked, start=1):
                title = doc_store.get(doc_id, {}).get('title', doc_id)
                # TREC run format: qid Q0 docid rank score tag
                run_f.write(f'{qid}\tQ0\t{doc_id}\t{rank}\t{score:.6f}\tltr\n')
                res_f.write(f'{qid}\t{doc_id}\t{score:.6f}\t{rank}\t{title}\n')

    print(f'[run_ltr] Run file lưu tại  : {run_file}')
    print(f'[run_ltr] Result file lưu tại: {result_file}')
    print('\nĐánh giá LTR:')
    print(f'  python TH8/evaluate_results.py --run-file runs/run_ltr.txt')
    print(f'  python TH8/compare_methods.py')


if __name__ == '__main__':
    main()
