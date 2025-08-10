
from typing import Dict, Any, List
import re, json
from .config import SYMBOLIC_NUMBERS

def load_archetypes(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def headline_number_hits(title: str) -> List[int]:
    nums = [int(x) for x in re.findall(r"\b\d+\b", title)]
    return [n for n in nums if n in SYMBOLIC_NUMBERS]

def archetype_hits(text: str, archetypes: List[str]) -> List[str]:
    t = text.lower()
    hits=[]
    for w in archetypes:
        if len(w)<3: continue
        if re.search(rf"\b{re.escape(w.lower())}\b", t):
            hits.append(w)
    seen=set(); out=[]
    for h in hits:
        if h not in seen: out.append(h); seen.add(h)
    return out[:20]

def score_ritual_signature(title: str, text: str, num_matches: int, date_info: Dict[str, Any]) -> Dict[str, Any]:
    n_hits = len(headline_number_hits(title))
    lp = date_info.get('life_path', 0)
    master = 1 if date_info.get('master_day') else 0
    score = n_hits*2 + num_matches + master + (1 if lp in (7,9,11,22) else 0)
    return {'score': score, 'headline_symbolic_numbers': headline_number_hits(title),
            'life_path': lp, 'master_day': bool(master)}
