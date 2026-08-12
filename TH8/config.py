# -------------------------------------------------------------
# File: config.py
# Vai trò: Cấu hình các đường dẫn, file dữ liệu, thư mục lưu trữ
# Chức năng: Định nghĩa các biến toàn cục cho toàn bộ hệ thống tìm kiếm sản phẩm,
# bao gồm các đường dẫn đến dữ liệu, index, kết quả, trace, v.v.
# -------------------------------------------------------------
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_PAGES_DIR = DATA_DIR / 'raw_pages'
INDEX_DIR = PROJECT_ROOT / 'indexes'
RESULTS_DIR = PROJECT_ROOT / 'results'
RUNS_DIR = PROJECT_ROOT / 'runs'
TRACE_DIR = PROJECT_ROOT / 'trace'

PRODUCTS_FILE = DATA_DIR / 'products.jsonl'
SEED_FILE = DATA_DIR / 'seed_urls.txt'
QUERIES_FILE = DATA_DIR / 'queries.tsv'
QRELS_FILE = DATA_DIR / 'qrels.tsv'

GRAPH_FILE = INDEX_DIR / 'graph.txt'
URL_MAP_FILE = INDEX_DIR / 'url_to_doc_id.json'
PAGERANK_FILE = INDEX_DIR / 'page_ranks.txt'
INVERTED_INDEX_FILE = INDEX_DIR / 'inverted_index.txt'
DOC_STORE_FILE = INDEX_DIR / 'doc_store.json'
DOC_STATS_FILE = INDEX_DIR / 'doc_stats.json'

for path in [DATA_DIR, RAW_PAGES_DIR, INDEX_DIR, RESULTS_DIR, RUNS_DIR, TRACE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
