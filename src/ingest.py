
import time, re, feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from .config import RSS_FEEDS, MIN_TITLE_LEN, DEFAULT_LOOKBACK_DAYS

def _normalize_url(u: str) -> str:
    if not u: return u
    return re.sub(r"[?&](utm_[^=]+|ocid|cmpid|ito|CMP|ref)=[^&]+", "", u)

def fetch_feed_entries(lookback_days: int = DEFAULT_LOOKBACK_DAYS, rss_feeds=None) -> List[Dict[str, Any]]:
    rss_feeds = rss_feeds or RSS_FEEDS
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    all_items, seen_links = [], set()
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for e in feed.entries:
            link = _normalize_url(getattr(e, 'link', '') or '')
            if not link or link in seen_links: continue
            title = getattr(e, 'title', '') or ''
            if len(title.strip()) < MIN_TITLE_LEN: continue
            published = None
            if getattr(e, 'published_parsed', None):
                published = datetime.fromtimestamp(time.mktime(e.published_parsed), tz=timezone.utc)
            elif getattr(e, 'updated_parsed', None):
                published = datetime.fromtimestamp(time.mktime(e.updated_parsed), tz=timezone.utc)
            if published and published < cutoff: continue
            all_items.append({
                'title': title.strip(),
                'link': link,
                'published': published.isoformat() if published else None,
                'source': getattr(feed.feed, 'title', None) or url,
            })
            seen_links.add(link)
    return all_items
