# -------------------------------------------------------------
# File: graph_builder.py
# Vai trò: Xây dựng đồ thị liên kết giữa các trang sản phẩm
# Chức năng: Đọc dữ liệu sản phẩm, tạo đồ thị liên kết (graph) giữa các sản phẩm dựa trên các liên kết (links),
# lưu đồ thị dưới dạng edgelist để phục vụ tính PageRank.
# -------------------------------------------------------------
import argparse
from collections import Counter

import networkx as nx

from config import GRAPH_FILE, PRODUCTS_FILE, RESULTS_DIR, URL_MAP_FILE
from utils import read_jsonl, write_json



def build_graph():
    records = list(read_jsonl(PRODUCTS_FILE))
    if not records:
        raise FileNotFoundError(f'Không có dữ liệu đầu vào: {PRODUCTS_FILE}')

    url_to_doc = {r['url']: r['doc_id'] for r in records}
    graph = nx.DiGraph()

    for record in records:
        src = record['doc_id']
        graph.add_node(src)
        for url in record.get('links', []):
            dst = url_to_doc.get(url)
            if not dst or src == dst:
                continue
            graph.add_edge(src, dst)

    nx.write_edgelist(graph, GRAPH_FILE, data=False)
    write_json(URL_MAP_FILE, url_to_doc)

    stats = {
        'num_documents': graph.number_of_nodes(),
        'num_edges': graph.number_of_edges(),
        'out_degree_top5': Counter(dict(graph.out_degree())).most_common(5),
        'in_degree_top5': Counter(dict(graph.in_degree())).most_common(5),
    }
    write_json(RESULTS_DIR / 'graph_stats.json', stats)
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build directed graph from crawled pages.')
    parser.parse_args()
    stats = build_graph()
    print(f"Graph saved to {GRAPH_FILE} | nodes={stats['num_documents']} edges={stats['num_edges']}")
