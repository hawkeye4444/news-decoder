
import json, os
from datetime import datetime, timezone
from typing import List, Dict, Any
import streamlit as st

from src.config import RSS_FEEDS, DEFAULT_LOOKBACK_DAYS, DEFAULT_MAX_ARTICLES, CALCULATORS
from src.ingest import fetch_feed_entries
from src.parse_article import fetch_and_parse
from src.nlp_extract import extract_5w, entities_for_gematria, nlp as ensure_spacy
from src.gematria import CALC_FUNCS
from src.match import compute_values, find_matches
from src.numerology import date_numerology
from src.patterns import load_archetypes, archetype_hits, score_ritual_signature
from src.astrology import basic_astrology

st.set_page_config(page_title="Daily Decode — News → Gematria → Patterns", page_icon="🔮", layout="wide")

def _inject_css():
    st.markdown(
        '''
        <style>
        .metric-card {border:1px solid #223041; padding:14px; border-radius:12px; background:#121820}
        .chip {display:inline-block; background:#1a2330; border:1px solid #223041; color:#9fb0c0; padding:2px 10px; margin:2px 6px 0 0; border-radius:999px; font-size:12px}
        .muted { color:#9fb0c0; }
        .article-card { border:1px solid #223041; border-radius:14px; padding:14px; background:#121820; margin-bottom:12px; }
        .fivew { display:grid; grid-template-columns: 80px 1fr; gap:6px; }
        a.article-link { text-decoration:none; color:#6ea8fe; }
        </style>
        ''',
        unsafe_allow_html=True
    )
_inject_css()

st.title("🔮 Daily Decode")
st.caption("Auto-sourced news → 5W’s → Gematria → Numerology → Patterns (plus optional astrology)")

st.sidebar.header("Settings")
lookback = st.sidebar.slider("Look back (days)", 1, 7, value=DEFAULT_LOOKBACK_DAYS)
max_articles = st.sidebar.slider("Max articles", 10, 100, value=DEFAULT_MAX_ARTICLES, step=10)
rss_edit = st.sidebar.text_area("RSS feeds (one per line)", "\n".join(RSS_FEEDS), height=180)

st.sidebar.header("Filters")
query = st.sidebar.text_input("Search (title/source/5W)", "")
only_matches = st.sidebar.checkbox("Only items with matches", value=False)
number_filter = st.sidebar.text_input("Exact match number (e.g., 33)", "")
min_score = st.sidebar.slider("Min ritual score", 0, 20, value=0)

st.sidebar.header("Output")
show_text = st.sidebar.checkbox("Show article text preview", value=False)

@st.cache_resource(show_spinner=False)
def ensure_model():
    try:
        ensure_spacy()
        return True
    except Exception:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        ensure_spacy()
        return True

@st.cache_data(show_spinner=True, ttl=60*60*3)
def run_decode(_feeds: List[str], days: int, max_n: int) -> List[Dict[str, Any]]:
    entries = fetch_feed_entries(lookback_days=days, rss_feeds=_feeds)[:max_n]
    arch = load_archetypes("database/archetypes.json")
    with open("database/phrases.json","r",encoding="utf-8") as f:
        base_phr = json.load(f)
    db_vals = {k: {name: func(k) for name, func in CALC_FUNCS.items()} for k in base_phr.keys()}
    results = []
    for e in entries:
        try:
            parsed = fetch_and_parse(e['link'])
        except Exception:
            continue
        title = parsed.get('title') or e['title']
        text = parsed.get('text') or ''
        published = parsed.get('published') or e.get('published')
        five_w = extract_5w(text, title=title, ref_date_iso=published)
        dt = datetime.now(timezone.utc)
        if published:
            try:
                from dateutil import parser as dateutil_parser
                dt = dateutil_parser.parse(published)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        phrases = entities_for_gematria(title, text)
        values_map = compute_values(phrases, CALCULATORS, CALC_FUNCS)
        matches = find_matches(values_map, db_vals)
        dnum = date_numerology(dt)
        arch_hits = archetype_hits((title + "\\n" + text[:5000]), arch)
        pat = score_ritual_signature(title, text, num_matches=len(matches), date_info=dnum)
        pat['archetype_hits'] = arch_hits
        astro = basic_astrology(dt)
        results.append({
            'title': title, 'link': e['link'], 'source': e.get('source'),
            'published': published, 'authors': parsed.get('authors'),
            'five_w': five_w, 'phrases': phrases, 'values': values_map,
            'matches': matches, 'numerology': dnum, 'patterns': pat, 'astrology': astro,
            'text': text[:2000]
        })
    return results

ensure_model()

feeds = [x.strip() for x in rss_edit.splitlines() if x.strip()]
run = st.button("🔁 Run fresh decode")
if run:
    st.cache_data.clear()
data = run_decode(feeds, lookback, max_articles)

total = len(data)
with_matches = sum(1 for d in data if d.get('matches'))
avg_score = round(sum(d['patterns']['score'] for d in data)/total, 2) if total else 0
col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<div class='metric-card'><h3>Articles</h3><div class='muted'>{total}</div></div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='metric-card'><h3>With matches</h3><div class='muted'>{with_matches}</div></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='metric-card'><h3>Avg ritual score</h3><div class='muted'>{avg_score}</div></div>", unsafe_allow_html=True)

def passes_filters(item):
    if min_score and item['patterns']['score'] < min_score:
        return False
    if only_matches and not item['matches']:
        return False
    if number_filter:
        if not any(str(m['value']) == str(number_filter) for m in item['matches']):
            return False
    if query:
        fw = item['five_w']
        hay = " ".join([
            item.get('title') or '', item.get('source') or '',
            *(fw.get('who') or []), *(fw.get('what') or []), *(fw.get('where') or []),
            fw.get('why') or ''
        ]).lower()
        if query.lower() not in hay:
            return False
    return True

filtered = [d for d in data if passes_filters(d)]
st.markdown(f"**Showing {len(filtered)} of {total}**")

for it in filtered:
    st.markdown("<div class='article-card'>", unsafe_allow_html=True)
    cols = st.columns([0.8, 0.2])
    with cols[0]:
        st.markdown(f"### {it['title']}")
        st.caption(f"{it.get('source') or '—'} • {it.get('published') or 'no date'}")
        fw = it['five_w']
        who = ', '.join(fw.get('who', [])) or '—'
        what = ', '.join(fw.get('what', [])) or '—'
        when = ', '.join(fw.get('when_parsed', []) or fw.get('when_mentions', [])) or '—'
        where = ', '.join(fw.get('where', [])) or '—'
        why = fw.get('why') or '—'
        st.markdown(f"<div class='fivew'><b>Who</b><div>{who}</div><b>What</b><div>{what}</div><b>When</b><div>{when}</div><b>Where</b><div>{where}</div><b>Why</b><div>{why}</div></div>", unsafe_allow_html=True)
    with cols[1]:
        chips = []
        pat = it['patterns']
        if pat.get('headline_symbolic_numbers'): chips.append(f"<span class='chip'>Headline nums: {', '.join(map(str,pat['headline_symbolic_numbers']))}</span>")
        chips.append(f"<span class='chip'>Score: {pat['score']}</span>")
        chips.append(f"<span class='chip'>Life path: {pat['life_path']}</span>")
        if pat.get('master_day'): chips.append("<span class='chip'>Master day</span>")
        if pat.get('archetype_hits'): chips.append(f"<span class='chip'>Archetypes: {', '.join(pat['archetype_hits'][:5])}{'…' if len(pat['archetype_hits'])>5 else ''}</span>")
        st.markdown("".join(chips), unsafe_allow_html=True)
    if it['matches']:
        st.markdown("**Gematria matches (top 10):**")
        st.table(it['matches'][:10])
    else:
        st.caption("No exact numeric matches.")
    if st.sidebar.checkbox("Show article text preview", key=f"txt_{hash(it['title'])}"):
        with st.expander("Article text (preview)"):
            st.write(it.get('text') or "—")
    st.markdown(f"<a class='article-link' href='{it.get('link')}' target='_blank'>Open original source ↗</a>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

if filtered:
    js = json.dumps(filtered, ensure_ascii=False, indent=2)
    st.download_button("⬇️ Download filtered JSON", js, file_name=f"decode-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json", mime="application/json")
