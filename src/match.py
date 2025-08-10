
from typing import Dict, Any, List

def compute_values(phrases: List[str], calculators: List[str], calcs) -> Dict[str, Dict[str, int]]:
    out={}
    for p in phrases:
        out[p]={}
        for calc in calculators:
            out[p][calc]=calcs[calc](p)
    return out

def find_matches(values_map: Dict[str, Dict[str, int]], db_values: Dict[str, Dict[str, int]]) -> List[Dict[str, Any]]:
    matches=[]
    for phrase, vals in values_map.items():
        for db_phrase, dbv in db_values.items():
            for calc, num in vals.items():
                if num in dbv.values():
                    matches.append({'phrase': phrase, 'db_phrase': db_phrase, 'calculator': calc, 'value': num})
    return matches
