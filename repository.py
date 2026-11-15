"""Persistenzschicht des Studien-Dashboards.
Die Datei enthält die abstrakte Schnittstelle StudiengangRepository und die JSON-Implementierung JsonStudiengangRepository."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from pathlib import Path

from domain import (
    Ergebnis,
    Modul, 
    Pruefungsleistung,
    Semester,
    Studiengang,
    Studienart,
    Wahlpflichtgruppe,
)


class StudiengangRepository(ABC):
    """Schnittstelle für das Laden und Speichern eines Studiengangs.
    Die Klasse legt nur fest, welche Methoden ein Repository haben muss.
    Wie die Daten gespeichert werden, entscheiden die Unterklassen."""

    
    @abstractmethod
    def lade(self) -> Studiengang:
        """Lädt den Studiengang aus dem Speicher und gibt ihn zurück"""
 
 
    @abstractmethod 
    def speichere(self, studiengang: Studiengang) -> None:
        """Schreibt den übergebenen Studiengang in den Speicher."""


class JsonStudiengangRepository(StudiengangRepository):
    """Speichert und lädt den Studiengang aus einer JSON-Datei.
    
    Attribute: 
        dateipfad: Pfad der JSON-Datei, mit der gearbeitet wird."""

        
    def __init__(self, dateipfad: str) -> None:
        """Merkt sich den Pfad der JSON-Datei.
        Args:
            dateipfad: Pfad zur Datei, zum Beispiel "daten/studiengang.json"."""
        self.dateipfad = Path(dateipfad)

    
    def lade(self) -> Studiengang:
        """Lädt den Studiengang aus der JSON-Datei.
        Die Module werden einmal angelegt. Semester und Wahlpflichtgruppen verwenden danach dieselben Objekte.
        Returns:
            Der fertig aufgebaute Studiengang.
        OSError:
            Datei fehlt.
        ValueError:
            kaputte JSON oder unbekannte Module.
        KeyError:
            fehlender Eintrag."""
        with open(self.dateipfad, encoding="utf-8") as datei:
            daten = json.load(datei)
        
        module = self._baueModule(daten["module"])
        self._verknuepfeVoraussetzungen(daten["module"], module)
        
        semester = [
            Semester(
                nummer=eintrag["nummer"],
                module=self._holeModule(eintrag["module"], module),
            )
            for eintrag in daten["semester"]
        ]
        gruppen = [
            Wahlpflichtgruppe(
                name=eintrag["name"],
                maximaleEcts=eintrag["maximaleEcts"],
                module=self._holeModule(eintrag["module"], module),
            )
            for eintrag in daten["wahlpflichtgruppen"]
        ]
        
        kopf = daten["studiengang"]
        return Studiengang(
            name=kopf["name"],
            art=Studienart(kopf["art"]),
            startdatum=date.fromisoformat(kopf["startdatum"]),
            gesamtEcts=kopf["gesamtEcts"],
            wunschwertNote=Decimal(kopf["wunschwertNote"]),
            grenzwertNote=Decimal(kopf["grenzwertNote"]),
            semester=semester,
            wahlpflichtgruppen=gruppen,
        )
            
        
    def speichere(self, studiengang: Studiengang) -> None:
        """Schreibt den Studiengang in die JSON-Datei
        Jedes Modul wird einmal in der Liste "module" gespeichert.
        Semester und Wahlpflichtgruppen enthalten nur die Modulnamen.
        Args:
            studiengang: Der Studiengang, der gespeichert wird.
        Raises:
            OSError: Wenn die Datei nicht geschrieben werden kann."""
        daten = {
            "studiengang": {
                "name": studiengang.name,
                "art": studiengang.art.value,
                "startdatum": studiengang.startdatum.isoformat(),
                "gesamtEcts": studiengang.gesamtEcts,
                "wunschwertNote": str(studiengang.wunschwertNote),
                "grenzwertNote": str(studiengang.grenzwertNote),
            },
            "module": [
                self._modulZuDaten(modul)
                for modul in studiengang.alleModule()
            ],
            "semester": [
                {
                    "nummer": semester.nummer,
                    "module": [modul.name for modul in semester.module],
                }
                for semester in studiengang.semester
            ],
            "wahlpflichtgruppen": [
                {
                    "name": gruppe.name,
                    "maximaleEcts": gruppe.maximaleEcts,
                    "module": [modul.name for modul in gruppe.module],
                }
                for gruppe in studiengang.wahlpflichtgruppen
            ],
        }
        with open(self.dateipfad, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=2)
 
 
    def _baueLeistung(self, daten:dict) -> Pruefungsleistung:
        """Baut aus einem JSON-Eintrag eine Prüfungsleistung.
        Args:
            daten: Wörterbuch mit versuchsnummer, ergebnis und note.
        Returns:
            Die fertige Prüfungsleistung. Fehlt die Note oder ist sie null, bleibt sie None."""
        note = daten.get("note")
        if note is not None:
            note = Decimal(note)
        return Pruefungsleistung(
            versuchsnummer=daten["versuchsnummer"],
            ergebnis=Ergebnis(daten["ergebnis"]),
            note=note,
        )
 
 
    def _baueModule(self, modulDaten: list[dict]) -> dict[str, Modul]:
        """Legt alle Module an, zunächst ohne Voraussetzungen.
        Args:
            modulDaten: Die Liste "module" aus der JSON-Datei.
        Returns:
            Wörterbuch, das jedem Modulnamen sein Modul-Objekt zuordnet."""
        module = {}
        for eintrag in modulDaten:
            leistungen = [
                self._baueLeistung(leistung)
            for leistung in eintrag["pruefungsleistungen"]
            ]
            module[eintrag["name"]] = Modul(
                name=eintrag["name"], 
                ects=eintrag["ects"],
                eingebucht=eintrag["eingebucht"],
                pruefungsleistungen=leistungen,
            )
        return module
 
 
    def _verknuepfeVoraussetzungen(
        self, modulDaten: list[dict], module: dict[str, Modul]
    ) -> None:
        """Trägt bei jedem Modul die Voraussetzungen als Objekte ein.
        Args:
            modulDaten: Die Liste "module" aus der JSON-Datei.
            module: Wörterbuch von Modulname zu Modul-Objekt.
        Raises:
            ValueError: Wenn eine Voraussetzung nicht als Modul existiert."""
    
        for eintrag in modulDaten:
            modul = module[eintrag["name"]]
            for name in eintrag ["voraussetzung"]:
                if name not in module:
                    raise ValueError(
                        f"Unbekannte Voraussetzung '{name}' "
                        f"bei Modul '{modul.name}'."
                    ) 
                modul.voraussetzung.append(module[name])
               
               
    def _holeModule(
        self, namen: list[str], module: dict[str, Modul]
    ) -> list[Modul]:
        """Holt zu einer Liste von Modulnamen die passenden Module.
        Args:
            namen: Modulnamen, wie sie in der JSON-Datei stehen.
            module: Wörterbuch von Modulnamen zu Modul-Objekt.
        Returns:
            Liste der Modul-Objekte in der Reihenfolge der Namen.
        Raises:
            ValueError: Wenn ein Name nicht in der Modulliste steht."""
        ergebnis = []
        for name in namen:
            if name not in module:
                raise ValueError(f"Unbekanntes Modul '{name}' in der Datei.")
            ergebnis.append(module[name])
        return ergebnis
     
     
    def _leistungZuDaten(self, leistung: Pruefungsleistung) -> dict:
        """Wandelt eine Prüfungsleistung in ein Wörterbuch für JSON um.
        Args:
            leistung: Die Prüfungsleistung, die gespeichert wird.
        Returns:
            Wörterbuch mit versuchsnummer, ergebnis und note. Eine fehlende Note wird zu None und damit zu null in der Datei"""
        note = None
        if leistung.note is not None:
            note = str(leistung.note)
        return {
            "versuchsnummer": leistung.versuchsnummer,
            "ergebnis": leistung.ergebnis.value,
            "note": note,
        }
    
    
    def _modulZuDaten(self, modul: Modul) -> dict:
        """Wandelt ein Modul in ein Wörterbuch für JSON um.
        Voraussetzungen werden nur mit ihrem Namen gespeichert.
        Args:
            modul: Das Modul, das gespeichert wird
        Returns:
            Wörterbuch mit allen Angaben zum Modul."""
        return {
            "name": modul.name,
            "ects": modul.ects,
            "eingebucht": modul.eingebucht,
            "voraussetzung": [v.name for v in modul.voraussetzung], 
            "pruefungsleistungen": [
                self._leistungZuDaten(leistung)
                for leistung in modul.pruefungsleistungen
            ],
        }
        