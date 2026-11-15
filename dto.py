"""Datentransferobjekte (DTOs) für die Anzeige im Dashboard.
Die DTOs bündeln fertige Werte für die View. Sie enthalten keine Berechnungen und keine Fachregeln."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from domain import Modulstatus


@dataclass(frozen=True)
class ModulDatenDTO:
    """Anzeigedaten eines einzelnen Moduls."""
    name: str
    semester: int | None
    ects: int
    status: Modulstatus
    note: Decimal | None
   
   
@dataclass(frozen=True)
class DashboardDatenDTO:
    """Anzeigedaten für die Übersicht des Studienfortschritts. Optionale Werte sind None, wenn sie noch nicht berechenbar sind."""
    startdatum: date
    enddatum: date
    regelzeitInMonaten: int
    gesamtEcts: int
    wunschwertNote: Decimal
    grenzwertNote: Decimal
    erreichteEcts: int
    sollEcts: Decimal
    durchschnittsnote: Decimal | None
    erstversuchsquote: Decimal | None
    prognostiziertesAbschlussdatum: date | None
    