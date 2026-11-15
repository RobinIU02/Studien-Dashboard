"""Prüft, ob JsonStudiengangRepository die Studiendaten richtig lädt und beim Speichern unverändert wieder herausgibt.
Start: python tests/test_repository.py"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repository import JsonStudiengangRepository
from service import KennzahlenService

DATEI = Path(__file__).resolve().parent.parent /"daten" / "studiengang.json"

studiengang = JsonStudiengangRepository(str(DATEI)).lade()
service = KennzahlenService()

print("Module:", len(studiengang.alleModule()))
print("Erreichte ECTS:", service.berechneErreichteEcts(studiengang))
print("Durchschnittsnote:", service.berechneDurchschnittsnote(studiengang))

with tempfile.TemporaryDirectory() as ordner:
    kopie = Path(ordner) / "kopie.json"
    JsonStudiengangRepository(str(kopie)).speichere(studiengang)
    original = json.loads(DATEI.read_text(encoding="utf-8"))
    neu = json.loads(kopie.read_text(encoding="utf-8"))
    print("Speichern und Laden ergibt dasselbe:", original == neu)