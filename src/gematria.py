
import re
A2Z = {chr(i+65): i+1 for i in range(26)}
Z2A = {chr(i+65): 26-i for i in range(26)}

def _letters(s: str) -> str:
    return re.sub(r"[^A-Za-z]", "", s).upper()

def english_ordinal(s: str) -> int:
    t = _letters(s); return sum(A2Z.get(ch, 0) for ch in t)

def full_reduction(s: str) -> int:
    t = _letters(s); total = 0
    for ch in t:
        n = A2Z.get(ch, 0)
        if n: total += ((n - 1) % 9) + 1
    return total

def reverse_ordinal(s: str) -> int:
    t = _letters(s); return sum(Z2A.get(ch, 0) for ch in t)

def reverse_reduction(s: str) -> int:
    t = _letters(s); total = 0
    for ch in t:
        n = Z2A.get(ch, 0)
        if n: total += ((n - 1) % 9) + 1
    return total

def sumerian(s: str) -> int:
    return english_ordinal(s) * 6

CALC_FUNCS = {
    'english_ordinal': english_ordinal,
    'full_reduction': full_reduction,
    'reverse_ordinal': reverse_ordinal,
    'reverse_reduction': reverse_reduction,
    'sumerian': sumerian,
}
