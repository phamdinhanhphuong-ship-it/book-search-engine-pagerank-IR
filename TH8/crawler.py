# -------------------------------------------------------------
# File: crawler.py
# Vai trò: Thu thập dữ liệu sản phẩm từ các trang web bán hàng
# Chức năng: Cài đặt spider/crawler sử dụng requests và BeautifulSoup để crawl dữ liệu sản phẩm,
# lưu HTML các trang vào thư mục data/raw_pages, tạo liên kết giữa các trang sản phẩm.
# -------------------------------------------------------------
import argparse
import hashlib
import json
import time
from collections import deque
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import PRODUCTS_FILE, RAW_PAGES_DIR, SEED_FILE, TRACE_DIR
from utils import canonicalize_url


def make_doc_id(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]


def is_navigation_link(anchor) -> bool:
    parent_names = {tag.name.lower() for tag in anchor.parents if getattr(tag, 'name', None) is not None}
    if parent_names & {'nav', 'header', 'footer', 'aside', 'form'}:
        return True

    classes = {str(cls).lower() for cls in anchor.get('class', [])}
    if classes & {'nav', 'navbar', 'menu', 'sidebar', 'header', 'footer'}:
        return True

    anchor_id = str(anchor.get('id', '')).lower()
    if any(token in anchor_id for token in ('nav', 'menu', 'sidebar', 'footer', 'header')):
        return True

    text = anchor.get_text(' ', strip=True).lower()
    if any(token in text for token in ('next', 'previous', 'home', 'books', 'page')) and 'catalogue' not in anchor.get('href', '').lower():
        return True

    return False


class Crawler:
    def __init__(self, delay: float = 1.0, timeout: int = 15, same_domain: bool = True):
        self.delay = delay
        self.timeout = timeout
        self.same_domain = same_domain
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Project6EducationalCrawler/1.0'})

    def fetch(self, url: str):
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def parse(self, url: str, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        text = soup.get_text(' ', strip=True)

        links = []
        base_host = requests.utils.urlparse(url).netloc
        for a in soup.find_all('a', href=True):
            if is_navigation_link(a):
                continue

            link = canonicalize_url(url, a['href'])
            if not link:
                continue
            if self.same_domain and requests.utils.urlparse(link).netloc != base_host:
                continue

            if any(token in link.lower() for token in ('/basket', '/login', '/register', '/account', '/search', 'javascript:')):
                continue

            if link == url:
                continue

            links.append(link)

        return {
            'url': url,
            'title': title,
            'text': text,
            'links': sorted(set(links)),
        }


def crawl(seed_urls: list[str], max_pages: int = 1000, delay: float = 1.0, same_domain: bool = True):
    crawler = Crawler(delay=delay, same_domain=same_domain)
    seen = set()
    queue = deque(seed_urls)
    records = []
    crawl_log_path = TRACE_DIR / 'crawl_log.txt'

    with crawl_log_path.open('w', encoding='utf-8') as log_f:
        while queue and len(records) < max_pages:
            url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)
            try:
                html = crawler.fetch(url)
                parsed = crawler.parse(url, html)
                doc_id = make_doc_id(url)
                parsed['doc_id'] = doc_id
                records.append(parsed)

                (RAW_PAGES_DIR / f'{doc_id}.html').write_text(html, encoding='utf-8', errors='ignore')
                log_f.write(f'OK\t{url}\t{doc_id}\n')

                for link in parsed['links']:
                    if link not in seen:
                        queue.append(link)
                time.sleep(delay)
            except Exception as e:
                log_f.write(f'ERROR\t{url}\t{e}\n')

    with PRODUCTS_FILE.open('w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl seed URLs and save pages to data/raw_pages')
    parser.add_argument('--seed-file', type=Path, default=SEED_FILE)
    parser.add_argument('--max-pages', type=int, default=1000)
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--allow-external', action='store_true')
    args = parser.parse_args()

    if not args.seed_file.exists():
        raise FileNotFoundError(f'Không tìm thấy file seed: {args.seed_file}')

    seed_urls = [line.strip() for line in args.seed_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    records = crawl(seed_urls, max_pages=args.max_pages, delay=args.delay, same_domain=not args.allow_external)
    print(f'Crawled {len(records)} pages. Output: {PRODUCTS_FILE}')
