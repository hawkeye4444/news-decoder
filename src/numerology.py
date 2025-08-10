
from typing import Dict, Any
from datetime import datetime

def digit_sum(n: int) -> int: return sum(int(d) for d in str(n))

def reduce_to_root(n: int) -> int:
    while n > 9 and n not in (11,22,33):
        n = digit_sum(n)
    return n

def date_numerology(dt: datetime) -> Dict[str, Any]:
    y,m,d = dt.year, dt.month, dt.day
    full = int(f"{y:04d}{m:02d}{d:02d}")
    return {
        'year_sum': digit_sum(y),
        'month_sum': digit_sum(m),
        'day_sum': digit_sum(d),
        'ymd_sum': digit_sum(full),
        'life_path': reduce_to_root(digit_sum(y)+digit_sum(m)+digit_sum(d)),
        'master_day': d in (11,22),
        'is_palindrome_date': str(full)==str(full)[::-1],
    }
