"""Fachklassen und Enumerationen des Studien-Dashboards."""
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from dataclasses import dataclass, field

import calendar
from datetime import date


class Studienart(Enum):
    """Die möglichen Studienarten. Sie bestimmen die Regelstudienzeit."""
    VOLLZEIT = "vollzeit"
    TEILZEIT_1 = "teilzeit_1"
    TEILZEIT_2 = "teilzeit_2"


class Modulstatus(Enum):
    """Der Status eines Moduls im Studienverlauf."""
    NICHT_EINGEBUCHT = "nicht_eingebucht"
    EINGEBUCHT = "eingebucht"
    ABGESCHLOSSEN = "abgeschlossen"
    GESPERRT = "gesperrt"


class Ergebnis(Enum):
    """Das Ergebnis einer Prüfungsleistung."""
    BESTANDEN = "bestanden"
    NICHT_BESTANDEN = "nicht_bestanden"
    OFFEN = "offen"
    ANERKANNT = "anerkannt"
    ZUR_PRUEFUNG_ANGEMELDET = "zur_pruefung_angemeldet"


@dataclass
class Pruefungsleistung:
    """Klasse für Pruefungsleistung. Die Note und das Ergebnis müssen zusammenpassen."""
    versuchsnummer: int
    ergebnis: Ergebnis
    note: Decimal | None = None

    def __post_init__(self) -> None:
        """Prüft nach dem Anlegen, ob Versuchsnummer, Ergebnis und Note zusammenpassen.
        Raises:
            ValueError: Wenn die Versuchsnummer kleiner als 1 ist, eine Note fehlt oder nicht zum Ergebnis passt.
            TypeError: Wenn die Note kein Decimal ist."""
        if self.versuchsnummer < 1:
            raise ValueError("Die Versuchsnummer muss mindestens 1 sein.")
        hat_note = self.ergebnis in (Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN)
    
        if not hat_note:
            if self.note is not None:
                raise ValueError("Bei diesem Ergebnis darf es keine Note geben.")
            return
        
        if not isinstance(self.note, Decimal):
            raise TypeError("Die Note muss als Decimal angegeben werden.")
        
        if self.ergebnis == Ergebnis.BESTANDEN:
            if not Decimal("1.0") <=self.note <= Decimal("4.0"):
                raise ValueError("Bestanden gilt nur für die Noten von 1,0 bis 4,0.")
        else:
            if not Decimal("4.1") <= self.note <= Decimal("5.0"):
                raise ValueError("Nicht bestanden gilt nur für die Noten von 4,1 bis 5,0.")


@dataclass(eq=False)
class Modul:
    """Ein Modul des Studienplans. Der Status wird aus Voraussetzungen und Prüfungsleistungen berechnet."""
    name: str
    ects: int
    eingebucht: bool = False
    voraussetzung: list[Modul] = field(default_factory=list)
    pruefungsleistungen: list[Pruefungsleistung] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Prüft, dass Name und ECTS des Moduls gültig sind.
        Raises: 
            ValueError: Wenn der Name leer ist oder die ECTS nicht größer als 0 sind. """
        if not self.name.strip():
            raise ValueError("Der Modulname darf nicht leer sein.")
        if self.ects <= 0:
            raise ValueError("Die ECTS müssen größer als 0 sein.")

            
    @property        
    def status(self) -> Modulstatus:
        """Berechneter Status des Moduls, abhängig von Prüfungsleistungen, Voraussetzungen und Buchung."""
        for leistung in self.pruefungsleistungen:
            if leistung.ergebnis in (Ergebnis.BESTANDEN, Ergebnis.ANERKANNT):
                return Modulstatus.ABGESCHLOSSEN
        for voraussetzung in self.voraussetzung:
            if voraussetzung.status != Modulstatus.ABGESCHLOSSEN:
                return Modulstatus.GESPERRT
        if self.eingebucht:
            return Modulstatus.EINGEBUCHT
        
        return Modulstatus.NICHT_EINGEBUCHT
 
 
    def buche(self) -> None:
        """Bucht das Modul ein. Fehlt eine Voraussetzung, wird ein Fehler ausgelöst.""" 
        if self.status == Modulstatus.ABGESCHLOSSEN:
            raise ValueError(f"Das Modul {self.name} ist bereits abgeschlossen.")
            
        fehlende = []
        for voraussetzung in self.voraussetzung:
            if voraussetzung.status != Modulstatus.ABGESCHLOSSEN:
                fehlende.append(voraussetzung.name)
                
        if fehlende:
            raise ValueError("Voraussetzung fehlt: " + ", ".join(fehlende))
        
        self.eingebucht = True

        
    def fuegePruefungsleistungHinzu(self, leistung: Pruefungsleistung) -> None:
        """Trägt eine Prüfungsleistung ein und bucht das Modul dabei nötigenfalls ein.
        Die Versuchsnummer muss die nächste in der Reihenfolge sein.
        Raises:
            ValueError: Wenn das Modul schon abgeschlossen ist, die Versuchsnummer nicht passt oder eine Vorraussetzung fehlt."""
        if self.status == Modulstatus.ABGESCHLOSSEN:
            raise ValueError(f"Das Modul {self.name} ist bereits abgeschlossen.")
        erwartet = self.naechsteVersuchsnummer
        if leistung.versuchsnummer != erwartet:
            raise ValueError(
                f"Bei {self.name} ist Versuch {erwartet} an der Reihe, "
                f"nicht Versuch {leistung.versuchsnummer}."
            )
        if not self.eingebucht:
            self.buche()
        self.pruefungsleistungen.append(leistung)
    
    @property
    def naechsteVersuchsnummer(self) -> int:
        """Nummer des nächsten Versuchs: Anzahl der bisherigen Leistungen plus 1."""
        return len(self.pruefungsleistungen) + 1


@dataclass(eq=False)
class Semester:
    """Ein Semester des Studienplans mit den Modulen, die darin vorgesehen sind."""
    nummer: int
    module: list[Modul] = field(default_factory=list)
 
 
@dataclass(eq=False)
class Wahlpflichtgruppe:
    """Eine Gruppe von Wahlpflichtmodulen mit einer Obergrenze an ECTS."""
    name: str
    maximaleEcts: int
    module: list[Modul] = field(default_factory=list)


REGELZEIT_IN_MONATEN = {
    Studienart.VOLLZEIT: 36,
    Studienart.TEILZEIT_1: 48, 
    Studienart.TEILZEIT_2: 72,
}

def addiereMonate(datum: date, monate: int) -> date:
    """Addiert Monate zu einem Datum. Gibt es den Tag im Zielmonat nicht wird der letzte Tag des Monats genommen."""
    gesamt = datum.month - 1 + monate
    jahr = datum.year + gesamt // 12
    monat = gesamt % 12 + 1
    letzter_tag = calendar.monthrange(jahr, monat)[1]
    return date(jahr, monat, min(datum.day, letzter_tag))
  
  
@dataclass(eq=False)
class Studiengang:
    """Der Studiengang mit Startdatum, Studienart, Gesamt-ECTS und Notenzielen. Er enthält die Semester und Wahlpflichtgruppen."""
    name: str
    art: Studienart
    startdatum: date
    gesamtEcts: int
    wunschwertNote: Decimal
    grenzwertNote: Decimal
    semester: list[Semester] = field(default_factory=list)
    wahlpflichtgruppen: list[Wahlpflichtgruppe] = field(default_factory=list)

    
    @property
    def regelzeitInMonaten(self) -> int:
        """Regelstudienzeit in Monaten, abhängig von der Studienart."""
        return REGELZEIT_IN_MONATEN[self.art]
            
    @property
    def enddatum(self) -> date:
        """Berechnetes Enddatum: Startdatum plus Regelzeit in Monaten."""
        return addiereMonate(self.startdatum, self.regelzeitInMonaten)
 
 
    def alleModule(self) -> list[Modul]:
        """Gibt alle Module des Studiengangs in einer Liste zurück.
        Zuerst kommen die Module der Semester, danach die Module der
        Wahlpflichtgruppen. Ein Modul steht entweder in einem Semester
        oder in einer Gruppe, nie in beiden.

        Returns:
            Liste aller Module des Studiengangs.
        """
        module = []
        for semester in self.semester:
            module.extend(semester.module)
        for gruppe in self.wahlpflichtgruppen:
            module.extend(gruppe.module)
        return module

        
    def fuegeModulHinzu(self, semesternummer: int, modul: Modul) -> None:
        """Fügt ein Modul in ein Semester hinzu. Ein Modul gibt es nur einmal, sonst wird ein Fehler ausgegeben."""
        for vorhanden in self.alleModule():
            if vorhanden is modul or vorhanden.name == modul.name:
                raise ValueError(f"Das Modul {modul.name} gibt es schon.")
        
        for semester in self.semester:
            if semester.nummer == semesternummer:
                semester.module.append(modul)
                return
        raise ValueError(f"Das Semester {semesternummer} gibt es nicht.")
        