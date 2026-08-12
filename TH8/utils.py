# -------------------------------------------------------------
# File: utils.py
# Vai trò: Cung cấp các hàm tiện ích dùng chung cho toàn bộ hệ thống
# Chức năng: Định nghĩa các hàm xử lý văn bản, đọc/ghi file, chuẩn hóa URL, tokenize, loại bỏ stopwords, v.v.
# -------------------------------------------------------------
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'of', 'to', 'in', 'on', 'for', 'with',
    'is', 'are', 'this', 'that', 'it', 'be', 'by', 'as', 'at', 'from',
    'một', 'các', 'và', 'là', 'cho', 'trên', 'dưới', 'của', 'được', 'với'
}


def canonicalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
        return None
    abs_url = urljoin(base_url, href)
    parsed = urlparse(abs_url)
    if parsed.scheme not in {'http', 'https'}:
        return None
    cleaned = parsed._replace(fragment='', query='')
    return urlunparse(cleaned)


TOKEN_PATTERN = re.compile(r"[\w']+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_PATTERN.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]



def read_jsonl(path: Path):
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)



def write_json(path: Path, data):
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def read_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)
