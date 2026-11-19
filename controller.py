"""Steuerung des Studien-Dashboards.
Der Controller verbindet Repository, Service und View. Er enthält keine Fachregeln und rechnet nicht selbst."""

from __future__ import annotations
from decimal import Decimal, InvalidOperation

from domain import Ergebnis, Modul, Pruefungsleistung, Modulstatus
from dto import DashboardDatenDTO, ModulDatenDTO
from repository import StudiengangRepository
from service import KennzahlenService
from view import KonsolenView


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
        """Zeigt den Bildschirm zu Ziel 1 mit den aktuellen Werten."""
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
                
                
    def _zuZahl(self, text: str) -> int:
        """Wandelt einen Text in eine ganze Zahl um.
        Raises:
            ValueError: Wenn der Text keine ganze Zahl ist."""
        try:
            return int(text)
        except ValueError:
            raise ValueError(f"'{text}' ist keine ganze Zahl.")
    
    
    def _zuNeuemNamen(self, text: str) -> str:
        """Prüft, dass es noch kein Modul mit diesem Namen gibt.
        Raises:
            ValueError: Wenn der Name schon vergeben ist."""
        for modul in self.studiengang.alleModule():
            if modul.name == text:
                raise ValueError(f"Das Modul '{text}' gibt es schon.")
        return text
        
    
    def _zuEcts(self, text: str, name: str) -> int:
        """Wandelt einen Text in ECTS um und prüft sie mit der Domain.
        Raises:
            ValueError: Wenn der Text keine ganze Zahl ist oder die ECTS nicht größer als 0 sind."""
        ects = self._zuZahl(text)
        Modul(name=name, ects=ects)
        return ects
        
    
    def _zuSemester(self, text: str) -> int:
        """Wandelt einen Text in eine Semesternummer um und prüft, ob es das Semester gibt.
        Raises:
            ValueError: Wenn der Text keine ganze Zahl ist oder das Semester fehlt."""
        nummer = self._zuZahl(text)
        for semester in self.studiengang.semester:
            if semester.nummer == nummer:
                return nummer
        raise ValueError(f"Das Semester {nummer} gibt es nicht.")
 
      
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
        
        
    def _frageSolange(self, frage: str, wandleUm):
        """Stellt eine Frage, bis die Eingabe gültig ist.
        Bei einem Fehler wird die Meldung angezeigt und neu gefragt.
        Eine leere Eingabe bricht ab.
        Args:
            frage: Der Text, der vor der Eingabe angezeigt wird.
            wandleUm: Funktion, die den Text in den gewünschten Wert umwandelt und bei ungültiger Eingabe einen ValueError auslöst.
        Returns:
            Der umgewandelte Wert oder None, wenn abgebrochen wurde."""
        while True:
            eingabe = self.view.frageEingabe(frage)
            if eingabe == "":
                return None
            try:
                return wandleUm(eingabe)
            except ValueError as fehler:
                self.view.zeigeFehler(str(fehler))
    
    
    def fuegeModulHinzu(self) -> None:
        """Fragt die Daten eines neuen Moduls ab und fügt es hinzu.
        Falsche Eingaben werden sofort gemeldet und neu abgefragt.
        Eine leere Eingabe bricht ab. Gespeichert wird nur bei Erfolg."""
        self.view.zeigeMeldung("(Leere Eingabe = Abbrechen)")
        name = self._frageSolange("Name des Moduls: ", self._zuNeuemNamen)
        if name is None:
            return
        ects = self._frageSolange("ECTS: ", lambda text: self._zuEcts(text, name))
        if ects is None:
            return
        semester = self._frageSolange("Semesternummer: ", self._zuSemester)
        if semester is None:
            return
        try:
            self.studiengang.fuegeModulHinzu(semester, Modul(name=name, ects=ects))
            self.repository.speichere(self.studiengang)
        except ValueError as fehler:
            self.view.zeigeFehler(str(fehler))
        except OSError as fehler:
            self.view.zeigeFehler(f"Speichern nicht möglich: {fehler}")
        else:
            self.view.zeigeMeldung(f"Modul '{name}' wurde hinzugefügt.")
      
      
    def _zuErgebnis(self, text: str) -> Ergebnis:
        """Wandelt einen Text in ein Ergebnis um.
        Raises:
            ValueError: Wenn der Text keines der drei Ergebnisse ist."""
        erlaubt = (Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN, Ergebnis.ANERKANNT)
        for ergebnis in erlaubt:
            if text == ergebnis.value:
                return ergebnis
        raise ValueError(f"'{text}' ist kein gültiges Ergebnis.")
        
        
    def _zuNote(self, text: str, versuch: int, ergebnis: Ergebnis) -> Decimal:
        """Wandelt einen Text in eine Note um und prüft sie mit der Domain.
        Raises:
            ValueError: Wenn der Text keine Zahl ist oder die Note nicht zum Ergebnis passt."""
        try:
            note = Decimal(text.replace(",", "."))
        except InvalidOperation:
            raise ValueError(f"'{text}' ist keine Note.")
        Pruefungsleistung(versuch, ergebnis, note)
        return note
   
   
    def trageErgebnisEin(self) -> None:
        """Fragt ein Prüfungsergebnis ab und trägt es bei einem Modul ein.
        Falsche Eingaben werden sofort gemeldet und neu abgefragt.
        Eine leere Eingabe bricht ab. Gespeichert wird nur bei Erfolg."""
        self.view.zeigeMeldung("(Leere Eingabe = Abbrechen)")
        modul = self._frageSolange("Name des Moduls: ", self._findeModul)
        if modul is None:
            return
        if modul.status == Modulstatus.ABGESCHLOSSEN:
            self.view.zeigeFehler(f"Das Modul {modul.name} ist bereits abgeschlossen.")
            return
        ergebnis = self._frageSolange(
            "Ergebnis (bestanden / nicht_bestanden / anerkannt): ", self._zuErgebnis
        )
        if ergebnis is None:
            return
        versuch = modul.naechsteVersuchsnummer
        note = None
        if ergebnis in (Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN):
            note = self._frageSolange(
                "Note: ", lambda text: self._zuNote(text, versuch, ergebnis)
            )
            if note is None:
                return
        try:
            modul.fuegePruefungsleistungHinzu(Pruefungsleistung(versuch, ergebnis, note))
            self.repository.speichere(self.studiengang)
        except ValueError as fehler:
            self.view.zeigeFehler(str(fehler))
        except OSError as fehler:
            self.view.zeigeFehler(f"Speichern nicht möglich: {fehler}")
        else:
            self.view.zeigeMeldung(f"Ergebnis für '{modul.name}' wurde eingetragen.")
        