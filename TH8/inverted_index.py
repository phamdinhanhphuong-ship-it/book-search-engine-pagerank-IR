# -------------------------------------------------------------
# File: inverted_index.py
# Vai trò: Xây dựng inverted index cho sản phẩm
# Chức năng: Đọc dữ liệu sản phẩm, xử lý văn bản, tokenize mô tả sản phẩm,
# xây dựng inverted index để phục vụ tìm kiếm từ khóa.
# -------------------------------------------------------------
import argparse
import math
from collections import Counter, defaultdict

from config import DOC_STATS_FILE, DOC_STORE_FILE, INVERTED_INDEX_FILE, PRODUCTS_FILE
from utils import read_jsonl, tokenize, write_json



def build_index():
    records = list(read_jsonl(PRODUCTS_FILE))
    if not records:
        raise FileNotFoundError(f'Không có dữ liệu đầu vào: {PRODUCTS_FILE}')

    inverted = defaultdict(dict)
    doc_store = {}
    doc_lengths = {}
    df = Counter()

    for rec in records:
        doc_id = rec['doc_id']
        text = f"{rec.get('title', '')} {rec.get('text', '')}"
        tokens = tokenize(text)
        tf = Counter(tokens)
        doc_lengths[doc_id] = sum(tf.values())
        doc_store[doc_id] = {
            'url': rec['url'],
            'title': rec.get('title', ''),
            'length': doc_lengths[doc_id],
        }
        for term, freq in tf.items():
            inverted[term][doc_id] = freq
            df[term] += 1

    num_docs = len(records)
    avg_doc_len = (sum(doc_lengths.values()) / num_docs) if num_docs else 0.0
    stats = {
        'num_docs': num_docs,
        'avg_doc_len': avg_doc_len,
        'doc_lengths': doc_lengths,
        'df': dict(df),
        'idf': {term: math.log((num_docs + 1) / (df_val + 1)) + 1 for term, df_val in df.items()},
    }

    write_json(INVERTED_INDEX_FILE, {term: postings for term, postings in inverted.items()})
    write_json(DOC_STORE_FILE, doc_store)
    write_json(DOC_STATS_FILE, stats)
    return {'num_docs': num_docs, 'vocab_size': len(inverted)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build inverted index from data/products.jsonl')
    parser.parse_args()
    info = build_index()
    print(f"Indexed {info['num_docs']} documents | vocab_size={info['vocab_size']} -> {INVERTED_INDEX_FILE}")
