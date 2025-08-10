
from typing import Dict, Any
from datetime import datetime
ZODIAC=[('Capricorn',(12,22),(1,19)),('Aquarius',(1,20),(2,18)),('Pisces',(2,19),(3,20)),
        ('Aries',(3,21),(4,19)),('Taurus',(4,20),(5,20)),('Gemini',(5,21),(6,20)),
        ('Cancer',(6,21),(7,22)),('Leo',(7,23),(8,22)),('Virgo',(8,23),(9,22)),
        ('Libra',(9,23),(10,22)),('Scorpio',(10,23),(11,21)),('Sagittarius',(11,22),(12,21))]
def approx_sun_sign(dt: datetime) -> str:
    m,d=dt.month,dt.day
    for sign,(sm,sd),(em,ed) in ZODIAC:
        if (m==sm and d>=sd) or (m==em and d<=ed) or (sm< m <em) or (sm>em and (m>sm or m<em)):
            return sign
    return 'Unknown'
def basic_astrology(dt: datetime) -> Dict[str, Any]: return {'sun_sign': approx_sun_sign(dt)}
