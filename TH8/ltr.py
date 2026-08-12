# -------------------------------------------------------------
# File: ltr.py
# Vai trò: Learning-to-Rank (LTR) cho hệ thống tìm kiếm sản phẩm
# Chức năng:
#   1. Trích xuất feature vector (lexical_score, pagerank, doc_length,
#      term_match_count, tfidf_max) cho từng cặp (query, doc).
#   2. Xây dựng tập huấn luyện từ qrels.tsv.
#   3. Huấn luyện mô hình phân loại pointwise (Random Forest).
#   4. Dự đoán điểm liên quan và xếp hạng lại kết quả.
# -------------------------------------------------------------
import json
import math
import pickle
from collections import Counter, defaultdict
from pathlib import Path

from config import (
    DOC_STATS_FILE,
    DOC_STORE_FILE,
    INVERTED_INDEX_FILE,
    PAGERANK_FILE,
    QRELS_FILE,
    QUERIES_FILE,
    RESULTS_DIR,
    RUNS_DIR,
)
from utils import read_json, tokenize

# Đường dẫn lưu model và dataset đã huấn luyện
MODEL_FILE = RESULTS_DIR / 'ltr_model.pkl'
LTR_DATASET_FILE = RESULTS_DIR / 'ltr_dataset.json'


# ──────────────────────────────────────────────
# Tải dữ liệu phụ trợ
# ──────────────────────────────────────────────

def load_pagerank() -> dict:
    scores = {}
    if not PAGERANK_FILE.exists():
        return scores
    with PAGERANK_FILE.open('r', encoding='utf-8') as f:
        next(f, None)          # bỏ qua header
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2:
                scores[parts[0]] = float(parts[1])
    return scores


def load_qrels() -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    if not QRELS_FILE.exists():
        return qrels
    with QRELS_FILE.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                qid, doc_id, rel = parts[0], parts[1], int(parts[2])
                qrels[qid][doc_id] = rel
    return qrels


def load_queries() -> list[tuple[str, str]]:
    queries = []
    if not QUERIES_FILE.exists():
        return queries
    with QUERIES_FILE.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                queries.append((parts[0], parts[1]))
    return queries


# ──────────────────────────────────────────────
# Trích xuất feature
# ──────────────────────────────────────────────

def extract_features(
    query: str,
    doc_id: str,
    inverted_index: dict,
    stats: dict,
    pagerank_scores: dict,
) -> list[float]:
    """
    Trả về vector feature cho cặp (query, doc):

    [0] lexical_score    – điểm TF-IDF tổng hợp giữa query và doc
    [1] pagerank         – điểm PageRank của doc
    [2] doc_length       – số token trong doc (đã normalize bằng avg_doc_len)
    [3] term_match_count – số term của query xuất hiện trong doc
    [4] tfidf_max        – giá trị TF-IDF cao nhất trong số các term query khớp
    """
    terms = tokenize(query)
    idf = stats.get('idf', {})
    doc_lengths = stats.get('doc_lengths', {})
    avg_doc_len = stats.get('avg_doc_len', 1.0) or 1.0

    # Feature 0: lexical score (sum of (1+tf)*idf)
    lexical_score = 0.0
    # Feature 3: term match count
    term_match_count = 0
    # Feature 4: max TF-IDF across matched terms
    tfidf_max = 0.0

    for term in terms:
        postings = inverted_index.get(term, {})
        tf = postings.get(doc_id, 0)
        if tf > 0:
            term_idf = idf.get(term, 0.0)
            contrib = (1 + tf) * term_idf
            lexical_score += contrib
            term_match_count += 1
            tfidf_val = tf * term_idf
            if tfidf_val > tfidf_max:
                tfidf_max = tfidf_val

    # Feature 1: pagerank
    pr = pagerank_scores.get(doc_id, 0.0)

    # Feature 2: normalized doc length
    raw_len = doc_lengths.get(doc_id, 0)
    norm_len = raw_len / avg_doc_len

    return [lexical_score, pr, norm_len, float(term_match_count), tfidf_max]


FEATURE_NAMES = [
    'lexical_score',
    'pagerank',
    'doc_length_norm',
    'term_match_count',
    'tfidf_max',
]


# ──────────────────────────────────────────────
# Xây dựng tập huấn luyện
# ──────────────────────────────────────────────

def build_dataset(
    queries: list[tuple[str, str]],
    qrels: dict,
    inverted_index: dict,
    stats: dict,
    pagerank_scores: dict,
) -> tuple[list, list, list]:
    """
    Tạo (X, y, meta) từ qrels.
    Mỗi dòng ứng với một cặp (query_id, doc_id) có nhãn relevance.
    Dùng pointwise: y = 1 nếu rel > 0, y = 0 nếu rel == 0.
    """
    query_map = {qid: text for qid, text in queries}
    X, y, meta = [], [], []

    for qid, doc_rels in qrels.items():
        query_text = query_map.get(qid, '')
        if not query_text:
            continue
        for doc_id, rel in doc_rels.items():
            feats = extract_features(
                query_text, doc_id, inverted_index, stats, pagerank_scores
            )
            X.append(feats)
            y.append(1 if rel > 0 else 0)
            meta.append({'qid': qid, 'doc_id': doc_id, 'rel': rel})

    return X, y, meta


# ──────────────────────────────────────────────
# Huấn luyện mô hình
# ──────────────────────────────────────────────

def train_model(X: list, y: list):
    """
    Huấn luyện Random Forest Classifier (pointwise LTR).
    Trả về model đã fit.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
    except ImportError as exc:
        raise ImportError(
            'Cần cài scikit-learn: pip install scikit-learn'
        ) from exc

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42,
        class_weight='balanced',
    )
    model.fit(X_train, y_train)

    # Đánh giá nội bộ
    try:
        from sklearn.metrics import classification_report
        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, zero_division=0)
        print('[LTR] Classification report trên tập test:')
        print(report)
    except Exception:
        pass

    return model


def save_model(model, path: Path = MODEL_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        pickle.dump(model, f)
    print(f'[LTR] Mô hình lưu tại: {path}')


def load_model(path: Path = MODEL_FILE):
    if not path.exists():
        raise FileNotFoundError(f'Chưa có mô hình LTR: {path}')
    with path.open('rb') as f:
        return pickle.load(f)


# ──────────────────────────────────────────────
# Dự đoán & xếp hạng lại
# ──────────────────────────────────────────────

def ltr_retrieve(
    query: str,
    candidate_doc_ids: list[str],
    model,
    inverted_index: dict,
    stats: dict,
    pagerank_scores: dict,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    Cho danh sách doc ứng viên, dùng mô hình LTR để tính điểm và xếp hạng lại.
    Trả về list (doc_id, ltr_score) đã sort giảm dần.
    """
    scored = []
    for doc_id in candidate_doc_ids:
        feats = extract_features(query, doc_id, inverted_index, stats, pagerank_scores)
        # Dùng xác suất thuộc lớp 1 (relevant) làm điểm xếp hạng
        prob = model.predict_proba([feats])[0][1]
        scored.append((doc_id, prob))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


# ──────────────────────────────────────────────
# Lấy toàn bộ candidate docs cho một query
# ──────────────────────────────────────────────

def get_candidates(query: str, inverted_index: dict, stats: dict) -> list[str]:
    """Trả về tất cả doc có ít nhất 1 term khớp với query."""
    terms = tokenize(query)
    idf = stats.get('idf', {})
    scores: dict[str, float] = defaultdict(float)
    for term in terms:
        postings = inverted_index.get(term, {})
        term_idf = idf.get(term, 0.0)
        for doc_id, tf in postings.items():
            scores[doc_id] += (1 + tf) * term_idf
    # Sắp xếp để ưu tiên candidate tốt hơn (giới hạn 100 để tránh slow)
    ranked = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    return ranked[:100]


# ──────────────────────────────────────────────
# Main: train pipeline
# ──────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Train Learning-to-Rank model')
    parser.add_argument(
        '--save-dataset', action='store_true',
        help='Lưu dataset ra file JSON để kiểm tra'
    )
    args = parser.parse_args()

    print('[LTR] Đang tải dữ liệu...')
    inverted_index = read_json(INVERTED_INDEX_FILE, default={})
    stats = read_json(DOC_STATS_FILE, default={})
    pagerank_scores = load_pagerank()
    queries = load_queries()
    qrels = load_qrels()

    if not inverted_index:
        raise FileNotFoundError(f'Chưa có inverted index: {INVERTED_INDEX_FILE}')
    if not qrels:
        raise FileNotFoundError(f'Chưa có qrels: {QRELS_FILE}')

    print(f'[LTR] Số query: {len(queries)}  |  Số (query, doc) trong qrels: '
          f'{sum(len(v) for v in qrels.values())}')

    X, y, meta = build_dataset(queries, qrels, inverted_index, stats, pagerank_scores)
    print(f'[LTR] Dataset: {len(X)} mẫu  |  Positive (relevant): {sum(y)}  |  Negative: {len(y)-sum(y)}')

    if args.save_dataset:
        dataset_rows = [
            {**meta[i], 'features': X[i], 'label': y[i]}
            for i in range(len(X))
        ]
        LTR_DATASET_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LTR_DATASET_FILE.open('w', encoding='utf-8') as f:
            json.dump(dataset_rows, f, ensure_ascii=False, indent=2)
        print(f'[LTR] Dataset lưu tại: {LTR_DATASET_FILE}')

    print('[LTR] Đang huấn luyện mô hình Random Forest...')
    model = train_model(X, y)
    save_model(model)

    # In feature importance
    if hasattr(model, 'feature_importances_'):
        print('\n[LTR] Feature importances:')
        for name, imp in zip(FEATURE_NAMES, model.feature_importances_):
            print(f'  {name:<22}: {imp:.4f}')

    print('\n[LTR] Huấn luyện hoàn tất. Chạy run_ltr.py để tạo file kết quả.')
