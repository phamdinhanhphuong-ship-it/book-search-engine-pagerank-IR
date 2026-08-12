# -------------------------------------------------------------
# File: retrieve_with_pagerank.py
# Vai trò: Tìm kiếm sản phẩm tích hợp PageRank
# Chức năng: Thực hiện truy vấn tìm kiếm sản phẩm dựa trên inverted index và điểm PageRank,
# kết hợp hai yếu tố này theo công thức score(query, doc) = lexical_score + weight * pageRank,
# xuất kết quả để đánh giá.
# -------------------------------------------------------------
import argparse
import math
from collections import defaultdict

from config import DOC_STATS_FILE, DOC_STORE_FILE, INVERTED_INDEX_FILE, PAGERANK_FILE, QUERIES_FILE, RESULTS_DIR, RUNS_DIR
from utils import read_json, tokenize



def load_pagerank():
    scores = {}
    if not PAGERANK_FILE.exists():
        return scores
    with PAGERANK_FILE.open('r', encoding='utf-8') as f:
        next(f, None)
        for line in f:
            doc_id, score = line.rstrip('\n').split('\t')
            scores[doc_id] = float(score)
    return scores



def lexical_retrieve(query: str, inverted_index: dict, stats: dict) -> dict:
    scores = defaultdict(float)
    terms = tokenize(query)
    idf = stats.get('idf', {})
    for term in terms:
        postings = inverted_index.get(term, {})
        term_idf = idf.get(term, 0.0)
        for doc_id, tf in postings.items():
            scores[doc_id] += (1 + tf) * term_idf
    return scores



def combined_retrieve(query: str, inverted_index: dict, stats: dict, pagerank_scores: dict, weight: float):
    lexical_scores = lexical_retrieve(query, inverted_index, stats)

    if not lexical_scores:
        return []

    doc_ids = list(lexical_scores.keys())

    max_lex = max(lexical_scores.values()) if lexical_scores else 1.0
    max_pr = max(pagerank_scores.get(did, 0.0) for did in doc_ids) if doc_ids else 1.0

    final_scores = []
    for doc_id, lex_score in lexical_scores.items():
        pr = pagerank_scores.get(doc_id, 0.0)
        lex_term = math.log1p(lex_score + 1e-12) / math.log1p(max_lex + 1e-12) if max_lex > 0 else 0.0
        pr_term = math.log1p(pr + 1e-12) / math.log1p(max_pr + 1e-12) if max_pr > 0 else 0.0
        final = lex_term + weight * pr_term
        final_scores.append((doc_id, lex_score, pr, final))
        
    final_scores.sort(key=lambda x: x[3], reverse=True)
    return final_scores



def read_queries(path=QUERIES_FILE):
    if not path.exists():
        return [('Q1', 'smartphone')]
    queries = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                queries.append((parts[0], parts[1]))
    return queries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run lexical + PageRank retrieval and save run files to runs/')
    parser.add_argument('--weight', type=float, default=1.0)
    parser.add_argument('--top-k', type=int, default=10)
    args = parser.parse_args()

    # Tạo thư mục nếu chưa tồn tại
    RUNS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    inverted_index = read_json(INVERTED_INDEX_FILE, default={})
    stats = read_json(DOC_STATS_FILE, default={})
    doc_store = read_json(DOC_STORE_FILE, default={})
    pagerank_scores = load_pagerank()
    queries = read_queries()

    if not inverted_index:
        raise FileNotFoundError(f'Chưa có index: {INVERTED_INDEX_FILE}')

    run_file = RUNS_DIR / f'run_w{args.weight:.1f}.txt'
    result_file = RESULTS_DIR / f'results_weight_{args.weight:.1f}.txt'

    with run_file.open('w', encoding='utf-8') as run_f, result_file.open('w', encoding='utf-8') as res_f:
        # Ghi header cho file kết quả
        res_f.write('query_id\tdoc_id\tscore\trank\n')
        for qid, query in queries:
            ranked = combined_retrieve(query, inverted_index, stats, pagerank_scores, args.weight)[: args.top_k]
            for rank, (doc_id, lex_score, pr, final) in enumerate(ranked, start=1):
                run_f.write(f'{qid}\tQ0\t{doc_id}\t{rank}\t{final:.6f}\tlexical_pagerank\n')
                res_f.write(f'{qid}\t{doc_id}\t{final:.6f}\t{rank}\n')

    print(f'Run saved to {run_file}\nResults saved to {result_file}')
