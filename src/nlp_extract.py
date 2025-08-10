
from typing import Dict, Any, List
import re, dateparser
from collections import Counter
import spacy
from .config import WHY_MARKERS

_NLP=None
def nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load('en_core_web_sm')
    return _NLP

def top_entities(doc, labels: List[str], k: int = 5) -> List[str]:
    items = [ent.text.strip() for ent in doc.ents if ent.label_ in labels and len(ent.text.strip())>1]
    counts = Counter(items)
    return [t for t,_ in counts.most_common(k)]

def extract_5w(text: str, title: str = '', ref_date_iso: str = None) -> Dict[str, Any]:
    d = nlp()(text if len(text) < 200000 else text[:200000])
    who = top_entities(d, ['PERSON','ORG'], k=5)
    where = top_entities(d, ['GPE','LOC'], k=5)
    when = top_entities(d, ['DATE','TIME'], k=5)

    what=[]
    if title:
        td = nlp()(title)
        what = [t.text for t in td if t.pos_ in ('NOUN','PROPN') and len(t.text)>2]
    if not what and list(d.sents):
        s0 = list(d.sents)[0].text
        sd = nlp()(s0)
        what = [t.text for t in sd if t.pos_ in ('NOUN','PROPN') and len(t.text)>2]

    why=None
    for s in list(d.sents)[:3]:
        s_low = s.text.lower()
        if any(f" {m} " in f" {s_low} " for m in WHY_MARKERS):
            why = s.text.strip(); break

    parsed_dates=[]
    for frag in when[:5]:
        dt = dateparser.parse(frag, settings={'RELATIVE_BASE': None})
        if dt: parsed_dates.append(dt.isoformat())

    return {'who': who, 'what': list(dict.fromkeys(what))[:6], 'when_mentions': when,
            'when_parsed': parsed_dates, 'where': where, 'why': why}

def entities_for_gematria(title: str, text: str) -> List[str]:
    d = nlp()(title + "\n" + text[:4000])
    keep = {'PERSON','ORG','GPE','EVENT','WORK_OF_ART','LAW','PRODUCT'}
    cand = [ent.text.strip() for ent in d.ents if ent.label_ in keep and len(ent.text.strip())>2]
    seen=set(); out=[]
    for c in cand:
        key = re.sub(r"\s+"," ", c.lower())
        if key not in seen: seen.add(key); out.append(c)
    td = nlp()(title)
    nouns=[t.text for t in td if t.pos_ in ('NOUN','PROPN') and len(t.text)>2]
    for n in nouns:
        if n.lower() not in seen: out.append(n)
    return out[:20]
