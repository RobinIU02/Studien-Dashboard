"""Prüft die Python-Umgebung.
Gibt die Python-Version und das heutige Datum aus.
Start: python tests/test_umgebung.py"""


import sys
from datetime import date

print(sys.version, date.today())