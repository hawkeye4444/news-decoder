import argparse, json, os
from pathlib import Path
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser

from .ingest import fetch_feed_entries
from .parse_article import fetch_and_parse
from .nlp_extract import extract_5w, entities_for_gematria
from .gematria import CALC_FUNCS
from .match import compute_values, find_matches
from .numerology import date_numerology
from .patterns import load_archetypes, archetype_hits, score_ritual_signature
from .astrology import basic_astrology

def write_json(items, outdir: str) -> str:
    p = Path(outdir) / f"report-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    return str(p)

def write_markdown(items, outdir: str) -> str:
    p = Path(outdir) / f"report-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.md"
    parts = ["# Daily Decode Report\n"]
    for it in items:
        parts.append(f"## {it['title']}")
        parts.append(f"Source: {it.get('source')} — Published: {it.get('published')}\nLink: {it.get('link')}\n")
        fw = it["five_w"]
        parts.append("**5W Summary**:")
        parts.append(f"- Who: {', '.join(fw.get('who', []))}")
        parts.append(f"- What: {', '.join(fw.get('what', []))}")
        parts.append(f"- When: {', '.join(fw.get('when_parsed', []) or fw.get('when_mentions', []))}")
        parts.append(f"- Where: {', '.join(fw.get('where', []))}")
        parts.append(f"- Why: {fw.get('why') or '—'}\n")
        parts.append("**Gematria Matches (top 10)**:")
        if it["matches"]:
            for m in it["matches"][:10]:
                parts.append(f"- '{m['phrase']}' ↔ '{m['db_phrase']}' via {m['calculator']} = **{m['value']}**")
        else:
            parts.append("- (no exact numeric matches)")
        pat = it["patterns"]
        parts.append("\n**Patterns**:")
        parts.append(f"- Score: {pat['score']} | Headline nums: {pat['headline_symbolic_numbers']} | Life path: {pat['life_path']} | Master day: {pat['master_day']}")
        if it.get("astrology"):
            parts.append(f"- Astrology (approx): Sun sign on date: {it['astrology'].get('sun_sign')}")
        parts.append("\n---\n")
    p.write_text("\n".join(parts))
    return str(p)

def run(days: int, max_articles: int, outdir: str, db_path: str, archetypes_path: str):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    entries = fetch_feed_entries(lookback_days=days)[:max_articles]

    # load built-in phrase DB and compute values on the fly
    base_phr = json.loads(Path(db_path).read_text(encoding="utf-8"))
    db_vals = {k: {name: func(k) for name, func in CALC_FUNCS.items()} for k in base_phr.keys()}
    arch = load_archetypes(archetypes_path)

    results = []
    for e in entries:
        try:
            parsed = fetch_and_parse(e["link"])
        except Exception:
            continue
        title = parsed.get("title") or e["title"]
        text = parsed.get("text") or ""
        published = parsed.get("published") or e.get("published")
        five_w = extract_5w(text, title=title, ref_date_iso=published)

        # choose a date to analyze
        dt = datetime.now(timezone.utc)
        if published:
            try:
                dt = dateutil_parser.parse(published)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

        phrases = entities_for_gematria(title, text)
        values_map = compute_values(phrases, ["english_ordinal","full_reduction","reverse_ordinal","reverse_reduction","sumerian"], CALC_FUNCS)
        matches = find_matches(values_map, db_vals)

        dnum = date_numerology(dt)
        arch_hits = archetype_hits(title + "\n" + text[:5000], arch)
        pat = score_ritual_signature(title, text, num_matches=len(matches), date_info=dnum)
        pat["archetype_hits"] = arch_hits
        astro = basic_astrology(dt)

        results.append({
            "title": title, "link": e["link"], "source": e.get("source"),
            "published": published, "authors": parsed.get("authors"),
            "five_w": five_w, "phrases": phrases, "values": values_map,
            "matches": matches, "numerology": dnum, "patterns": pat, "astrology": astro
        })

    jpath = write_json(results, outdir)
    mpath = write_markdown(results, outdir)
    print("Wrote:", jpath, mpath)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--max_articles", type=int, default=40)
    ap.add_argument("--out", type=str, default="docs")
    ap.add_argument("--db", type=str, default="database/phrases.json")
    ap.add_argument("--archetypes", type=str, default="database/archetypes.json")
    args = ap.parse_args()
    run(args.days, args.max_articles, args.out, args.db, args.archetypes)
