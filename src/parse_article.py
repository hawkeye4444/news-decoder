
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from readability import Document
try:
    from newspaper import Article
except Exception:
    Article = None
from dateutil import parser as dateutil_parser

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsDecoder/1.0)"}

def fetch_and_parse(url: str) -> Dict[str, Any]:
    if Article is not None:
        try:
            art = Article(url); art.download(); art.parse()
            text = (art.text or '').strip(); title = (art.title or '').strip()
            authors = art.authors or []; published = None
            if art.publish_date: published = art.publish_date.isoformat()
            if text and len(text.split()) > 60:
                return {'title': title, 'authors': authors, 'text': text, 'published': published, 'top_image': getattr(art,'top_image',None)}
        except Exception:
            pass
    resp = requests.get(url, headers=HEADERS, timeout=15); resp.raise_for_status()
    doc = Document(resp.text); title = (doc.short_title() or '').strip()
    html = doc.summary(); soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script','style','noscript']): tag.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all('p')]
    text = "\n".join([p for p in paragraphs if p])
    published = None
    try:
        soup_full = BeautifulSoup(resp.text, 'lxml')
        meta = soup_full.find('meta', {'property':'article:published_time'}) or soup_full.find('meta', {'name':'date'})
        if meta and meta.get('content'): published = dateutil_parser.parse(meta['content']).isoformat()
    except Exception: pass
    return {'title': title, 'authors': [], 'text': text, 'published': published, 'top_image': None}
