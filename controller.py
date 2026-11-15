"""Steuerung des Studien-Dashboards.
Der Controller verbindet Repository, Service und View. Er enthält keine Fachregeln und rechnet nicht selbst"""

from __future__ import annotations

from domain import Ergebnis, Modul, Pruefungsleistung
from dto import DashboardDatenDTO, ModulDatenDTO
from repository import StudiengangRepository
from service import KennzahlenService
from view import KonsolenView
from decimal import Decimal, InvalidOperation



class Controller:
    """Steuert den Ablauf des Dashboards.
    Attribute:
        repository: Lädt und speichert den Studiengang.
        service: Berechnet die Kennzahlen.
        view: Gibt Daten aus und liest Eingaben ein.
        studiengang: Der geladene Studiengang. """
    def __init__(
        self,
        repository: StudiengangRepository,
        service: KennzahlenService,
        view: KonsolenView,
    ) -> None:
        """Merkt sich die Bausteine und lädt den Studiengang.
        Args:
            repository: Lädt und speichert den Studiengang.
            service: Berechnet die Kennzahlen.
            view: Gibt Daten aus und liest Eingaben ein. """
        self.repository = repository
        self.service = service
        self.view = view
        self.studiengang = repository.lade()

        
    def _baueDashboardDaten(self) -> DashboardDatenDTO:
        """Holt die Kennzahlen beim Service und packt sie in ein DTO.
        Returns:
            Das DTO mit allen Werten für die Ansichten zu Ziel 1 und 2. """
        s = self.studiengang
        return DashboardDatenDTO(
            startdatum=s.startdatum,
            enddatum=s.enddatum,
            regelzeitInMonaten=s.regelzeitInMonaten,
            gesamtEcts=s.gesamtEcts,
            wunschwertNote=s.wunschwertNote,
            grenzwertNote=s.grenzwertNote,
            erreichteEcts=self.service.berechneErreichteEcts(s),
            sollEcts=self.service.berechneSollEcts(s),
            durchschnittsnote=self.service.berechneDurchschnittsnote(s),
            erstversuchsquote=self.service.berechneErstversuchsquote(s),
            prognostiziertesAbschlussdatum=self.service.berechnePrognose(s),
        )
 
 
    def _zuModulDaten(self, modul: Modul, semester: int | None) -> ModulDatenDTO:
        """Wandelt ein Modul in ein DTO für die Anzeige um.
        Args:
            modul: Das Modul, das angezeigt wird.
            semester: Semesternummer oder None bei Wahlpflichtmodulen.
            
        Returns:
            Das DTO mit Name, Semester, ECTS, Status und Note des Moduls."""
        note = None
        for leistung in modul.pruefungsleistungen:
            if leistung.ergebnis == Ergebnis.BESTANDEN:
                note = leistung.note
        return ModulDatenDTO(
            name=modul.name,
            semester=semester,
            ects=modul.ects,
            status=modul.status,
            note=note,
        )
        
        
    def _baueModulDaten(self) -> list[ModulDatenDTO]:
        """Baut die DTOs für alle Module in der Reihenfolge des Studienplans.
        Zuerst kommen die Module der Semester, danach die der Wahlpflichtgruppen.
        Returns:
            Liste der DTOs für die Modulliste."""
            
        ergebnis = []
        for semester in self.studiengang.semester:
            for modul in semester.module:
                ergebnis.append(self._zuModulDaten(modul, semester.nummer))
        for gruppe in self.studiengang.wahlpflichtgruppen:
            for modul in gruppe.module:
                ergebnis.append(self._zuModulDaten(modul, None))
        return ergebnis

        
    def zeigeRegelzeit(self) -> None:
        """Zeigt den Bildschirm zu Ziel 1 mit den aktuellen Werten"""
        self.view.zeigeRegelzeit(self._baueDashboardDaten())
 
 
    def zeigeNotenschnitt(self) -> None:
        """Zeigt den Bildschirm zu Ziel 2 mit den aktuellen Werten."""
        self.view.zeigeNotenschnitt(self._baueDashboardDaten())
 
 
    def zeigeModulstatus(self) -> None:
        """Zeigt den Bildschirm zu Ziel 3 mit der Modulliste."""
        self.view.zeigeModulstatus(
            self._baueDashboardDaten(), self._baueModulDaten()
        )
 
 
    def starte(self) -> None:
        """Zeigt das Hauptmenü und führt die Auswahl aus, bis 0 gewählt wird."""
        while True:
            self.view.zeigeMenue()
            auswahl = self.view.frageEingabe("Auswahl: ")
            if auswahl == "1":
                self.zeigeRegelzeit()
            elif auswahl == "2":
                self.zeigeNotenschnitt()
            elif auswahl == "3":
                self.zeigeModulstatus()
            elif auswahl == "4":
                self.fuegeModulHinzu()
            elif auswahl == "5":
                self.trageErgebnisEin()
            elif auswahl == "0":
                self.view.zeigeMeldung("Auf Wiedersehen.")
                break
            else:
                self.view.zeigeFehler(
                    "Ungültige Eingabe. Bitte eine Zahl von 0 bis 5 wählen."
                )
                
                
    def _frageZahl(self, frage: str) -> int:
        """Fragt nach einer ganzen Zahl.
        Args:
            frage: Der Text, der vor der Eingabe angezeigt wird.
        Returns:
            Die eingegebene Zahl.
        Raises:
            ValueError: Wenn die Eingabe keine ganze Zahl ist."""
        eingabe = self.view.frageEingabe(frage)
        try:
            return int(eingabe)
        except ValueError:
            raise ValueError(f"'{eingabe}' ist keine ganze Zahl.")
      
      
    def _findeModul(self, name: str) -> Modul:
        """Sucht ein Modul des Studiengangs anhand seines Namens.
        Args:
            name: Der Name des gesuchten Moduls.
        Returns:
            Das Modul mit diesem Namen.
        Raises:
            ValueError: Wenn es kein Modul mit diesem Namen gibt."""
        for modul in self.studiengang.alleModule():
            if modul.name == name:
                return modul
        raise ValueError(f"Das Modul '{name}' gibt es nicht.")
    
    
    def fuegeModulHinzu(self) -> None:
        """Fragt die Daten eines neuen Moduls ab und fügt es hinzu.
        Fehler der Eingabe oder der Domain werden als Meldung angezeigt.
        Nur bei Erfolg wird gespeichert."""
        try:
            name = self.view.frageEingabe("Name des Moduls: ")
            ects = self._frageZahl("ECTS: ")
            semester = self._frageZahl("Semesternummer: ")
                
            modul = Modul(name=name, ects=ects)
            self.studiengang.fuegeModulHinzu(semester, modul)
            self.repository.speichere(self.studiengang)
        except ValueError as fehler:
            self.view.zeigeFehler(str(fehler))
        except OSError as fehler:
            self.view.zeigeFehler(f"Speichern nicht möglich: {fehler}")
        else:
            self.view.zeigeMeldung(f"Modul '{name}' wurde hinzugefügt.")
      
      
    def _frageErgebnis(self) -> Ergebnis:
        """Fragt nach dem Ergebnis einer Prüfung.
        Returns:
            Das gewählte Ergebnis.
        Raises: 
            ValueError: Wenn die Eingabe keines der drei Ergebnisse ist."""
        eingabe = self.view.frageEingabe(
            "Ergebnis(bestanden / nicht_bestanden / anerkannt): "
        )
        erlaubt =(Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN, Ergebnis.ANERKANNT)
        for ergebnis in erlaubt:
            if eingabe == ergebnis.value:
                    return ergebnis
        raise ValueError(f"'{eingabe}' ist kein gültiges Ergebnis.")
  
  
    def _frageNote(self) -> Decimal:
        """Fragt nach einer note, Komma und Punkt sind erlaubt.
        Returns: 
            Die eingegebene Note.
        Raises: 
            ValueError: Wenn die Eingabe keine Zahl ist."""
        eingabe = self.view.frageEingabe("Note: ")
        try:
            return Decimal(eingabe.replace(",", "."))
        except InvalidOperation:
            raise ValueError(f"'{eingabe}' ist keine Note.")
   
   
    def trageErgebnisEin(self) -> None:
        """Fragt ein Prüfungsergebnis ab und trägt es bei einem Modul ein.
        Fehler der Eingabe oder der Domain werden als Meldung angezeigt.
        Nur bei Erfolg wird gespeichert:"""
        try:
            name = self.view.frageEingabe("Name des Moduls: ")
            modul = self._findeModul(name)
            versuch = self._frageZahl("Versuchsnummer: ")
            ergebnis = self._frageErgebnis()
            note = None
            if ergebnis in (Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN):
                note = self._frageNote()
            leistung = Pruefungsleistung(versuch, ergebnis, note)
            modul.fuegePruefungsleistungHinzu(leistung)
            self.repository.speichere(self.studiengang)
        except ValueError as fehler:
            self.view.zeigeFehler(str(fehler))
        except OSError as fehler:
            self.view.zeigeFehler(f"Speichern nicht möglich: {fehler}")
        else:
            self.view.zeigeMeldung(f"Ergebnis für '{name}' wurde eingetragen.")
        