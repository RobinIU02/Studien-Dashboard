"""Testet den KennzahlenService mit einem kleinen Beispiel-Studiengang."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date
from decimal import Decimal

from domain import Ergebnis, Modul, Pruefungsleistung, Semester, Studiengang, Studienart
from service import KennzahlenService


def baue_studiengang():
    """Erzeugt einen Studiengang mit drei Modulen für die Tests."""
    a = Modul("Grundlagen", 5)
    b = Modul("Aufbau", 5, voraussetzung=[a])
    c = Modul("Projekt", 5)
    a.pruefungsleistungen.append(Pruefungsleistung(1, Ergebnis.BESTANDEN, Decimal("2.0")))
    b.pruefungsleistungen.append(Pruefungsleistung(1, Ergebnis.NICHT_BESTANDEN, Decimal("5.0")))
    b.pruefungsleistungen.append(Pruefungsleistung(2, Ergebnis.BESTANDEN, Decimal("3.0")))
    c.pruefungsleistungen.append(Pruefungsleistung(1, Ergebnis.ANERKANNT))
    s = Studiengang("Test", Studienart.VOLLZEIT, date(2026, 2, 16), 180,
                    Decimal("2.0"), Decimal("2.7"), [Semester(1), Semester(2)])
    s.fuegeModulHinzu(1, a)
    s.fuegeModulHinzu(1, b)
    s.fuegeModulHinzu(2, c)
    return s


service = KennzahlenService()
studiengang = baue_studiengang()

print("Erreichte ECTS:", service.berechneErreichteEcts(studiengang))
print("Durchschnittsnote:", service.berechneDurchschnittsnote(studiengang))

STICHTAG = date(2026, 11, 12)
print("Erstversuchsquote:", service.berechneErstversuchsquote(studiengang))
print("Soll-ECTS:", service.berechneSollEcts(studiengang, STICHTAG))
print("Prognose:", service.berechnePrognose(studiengang, STICHTAG))

leer = Studiengang("Leer", Studienart.VOLLZEIT, date(2026, 2, 16), 180,
                   Decimal("2.0"), Decimal("2.7"))
print("Ohne Daten:", service.berechneDurchschnittsnote(leer),
      service.berechneErstversuchsquote(leer), service.berechnePrognose(leer, STICHTAG))