"""Konsolenansicht des Studien-Dashboards.
Die View gibt Werte aus und liest Eingaben ein. Sie enthält keine Berechnungen und keine Fachregeln."""

from __future__ import annotations

from datetime import date

from decimal import Decimal

from dto import DashboardDatenDTO, ModulDatenDTO


class KonsolenView:
    """Gibt das Dashboard in der Konsole aus und liest Eingaben ein."""
    BALKENBREITE = 20
    SKALENBREITE = 50
    NOTE_MIN = Decimal("1.0")
    NOTE_MAX = Decimal("3.0")
    # \u2500 = Linie, \u252c = Markierung auf der Linie, \u25b2 = Pfeil
    LINIE = "\u2500"
    MARKE = "\u252c"
    PFEIL = "\u25b2"
    
    def _zahl(self, wert: Decimal | None, stellen: int) -> str:
        """Formatiert eine Zahl mit Komma als Dezimaltrenner."""
        if wert is None:
            return "-"
        return f"{wert:.{stellen}f}".replace(".", ",")
        
    def _balken(self, wert: Decimal | int, maximum: Decimal | int) -> str:
        """Zeichnet einen Fortschrittsbalken aus Kästchen."""
        anteil = Decimal(wert) / Decimal(maximum)
        gefuellt = round(anteil * self.BALKENBREITE)
        gefuellt = max(0, min(self.BALKENBREITE, gefuellt))
        #\u2588 = volles Kästchen, \u2591 = helles Kästchen
        return "\u2588" * gefuellt + "\u2591" * (self.BALKENBREITE - gefuellt)
        
    def _datum(self, datum: date | None) -> str:
        """Formatiert ein Datum als Tag.Monat.Jahr."""
        if datum is None:
            return "-"
        return datum.strftime("%d.%m.%Y")
        
    def zeigeRegelzeit(self, dto: DashboardDatenDTO) -> None:
        differenz = Decimal(dto.erreichteEcts) - dto.sollEcts
        differenzText = f"{differenz:+.1f}".replace(".", ",")
        status = "im Plan" if differenz >= 0 else "hinter dem Plan"
        
        abschluss = "-"
        if dto.prognostiziertesAbschlussdatum is not None:
            abschluss = dto.prognostiziertesAbschlussdatum.strftime("%m/%Y")
            
        soll = self._balken(dto.sollEcts, dto.gesamtEcts)
        ist = self._balken(dto.erreichteEcts, dto.gesamtEcts)
        
        print()
        print("=== ZIEL 1: Studium in der Regelzeit ===")
        print(f"Studienstart:   {self._datum(dto.startdatum)}")
        print(
            f"Geplantes Ende: {self._datum(dto.enddatum)} "
            f"(Regelzeit: {dto.regelzeitInMonaten} Monate)"
        )
        print()
        print(
            f"ECTS Soll [{soll}] "
            f"{self._zahl(Decimal(dto.sollEcts), 1)} / {dto.gesamtEcts}"
        )
        print(
            f"ECTS Ist  [{ist}] "
            f"{self._zahl(Decimal(dto.erreichteEcts), 1)} / {dto.gesamtEcts}"
        )
        print(f"Differenz: {differenzText} ECTS -> {status}")
        print(f"Voraussichtlicher Abschluss: {abschluss}")
        
    def _position(self, note: Decimal) -> int:
        """Berechnet, an welcher Stelle der Skala eine Note steht."""
        anteil = (note - self.NOTE_MIN) / (self.NOTE_MAX - self.NOTE_MIN)
        position = round(anteil * (self.SKALENBREITE - 1))
        return max(0, min(self.SKALENBREITE - 1, position))
        
    def _setzeText(self, zeile: list[str], start: int, text: str) -> None:
        """Schreibt einen Text ab einer Stelle in eine Zeile aus Zeichen
        
        Args:
            zeile: Liste mit einem Zeichen pro Eintrag.
            start: Stelle, an der der Text beginnt.
            text: Der Text, der eingetragen wird.
            """
        for i, zeichen in enumerate(text):
            if start + i < len(zeile):
                zeile[start + i] = zeichen
    def zeigeNotenschnitt(self, dto: DashboardDatenDTO) -> None:
        """Zeigt den Bildschirm "Ziel 2: Notendurchschnitt".
        Args:
            dto: Die fertig berechneten Werte für das Dashboard."""
        print()
        print("=== ZIEL 2: Notendurchschnitt ===")
        note = dto.durchschnittsnote
        if note is None:
            print("Noch keine benotete Prüfungsleistung vorhanden.")
            return
        wunschPos = self._position(dto.wunschwertNote)
        grenzPos = self._position(dto.grenzwertNote)
        notePos = self._position(note)
        
        breite = self.SKALENBREITE + 20
        beschriftung = [" "] * breite
        self._setzeText(
            beschriftung, wunschPos,
            f"Wunsch {self._zahl(dto.wunschwertNote, 1)}",
        )
        self._setzeText(
            beschriftung, grenzPos,
            f"Grenze {self._zahl(dto.grenzwertNote, 1)}",
        )
        
        skala = [self.LINIE] * self.SKALENBREITE
        skala[wunschPos] = self.MARKE
        skala[grenzPos] = self.MARKE
        
        pfeil = [" "] * breite
        self._setzeText(
            pfeil, notePos, f"{self.PFEIL} aktuell: {self._zahl(note, 2)}"
        )
        
        print("     " + "".join(beschriftung).rstrip())
        print("1,0  " + "".join(skala) + " 3,0")
        print("     " + "".join(pfeil).rstrip())
        print()
        
        abstandWunsch = note - dto.wunschwertNote
        abstandGrenze = dto.grenzwertNote - note
        wunschHinweis = "(erreicht)" if abstandWunsch <= 0 else ""
        grenzHinweis = "(Puffer)" if abstandGrenze >= 0 else "(überschritten)"
        print(
            f"Abstand zum Wunschwert: {self._zahl(abs(abstandWunsch), 2)} "
            f"{wunschHinweis}".rstrip()
        )
        print(
            f"Abstand zum Grenzwert:  {self._zahl(abs(abstandGrenze), 2)} "
            f"{grenzHinweis}"
        )
    
    def _kuerze(self, text: str, laenge: int) -> str:
        """Kürzt einen Text auf eine maximale Länge.
        Args:
            text: Der Text, der gekürzt wird.
            laenge: Die höchste erlaubte Länge.
            
        Returns: Der Text, bei Bedarf mit "Auslassungszeichen" am Ende gekürzt."""
        if len(text) <= laenge:
            return text
        return text[: laenge - 1] + "\u2026"
    
    def zeigeModulstatus(
        self, dto: DashboardDatenDTO, module: list[ModulDatenDTO]
    ) -> None:
        """Zeigt den Bildschirm "Ziel 3: Modulstatus und Erstversuche".
        Die Module werden in der übergebenen Reihenfolge ausgegeben.
        Bei jedem Wechsel des Semesters kommt eine Überschrift.
        
        Args:
            dto: Die fertig berechneten Werte für das Dashboard.
            module: Die Anzeigedaten aller Module."""
        print()
        print("=== ZIEL 3: Modulstatus und Erstversuche ===")
        quote = "-"
        if dto.erstversuchsquote is not None:
            quote = f"{self._zahl(dto.erstversuchsquote, 1)} %"
        print(f"Erstversuchsquote: {quote}")
        print()
        print(f"{'Modul':<46}{'ECTS':>4}  {'Status':<17}{'Note':>4}")
        
        letzteUeberschrift = ""
        for modul in module:
            if modul.semester is None:
                ueberschrift = "Wahlpflicht"
            else:
                ueberschrift = f"Semester {modul.semester}"
            if ueberschrift != letzteUeberschrift:
                print()
                print(ueberschrift)
                letzteUeberschrift = ueberschrift
            
            name = self._kuerze(modul.name, 45)
            status = modul.status.value.replace("_", " ")
            note = self._zahl(modul.note, 1)
            print(f"{name:<46}{modul.ects:>4}  {status:<17}{note:>4}")
            
    def zeigeMenue(self) -> None:
        """Zeigt das Hauptmenü des Dashboards."""
        print()
        print("=== STUDIEN-DASHBOARD ===")
        print("[1] Ziel 1: Regelzeit")
        print("[2] Ziel 2: Notendurchschnitt")
        print("[3] Ziel 3: Modulstatus")
        print("[4] Modul hinzufügen")
        print("[5] Ergebnis eintragen")
        print("[0] Beenden")
    
    def frageEingabe(self, frage: str) -> str:
        """Stellt eine Frage und liest die Antwort ein.
        Args:
            frage: Der Text, der vor der Eingabe angezeigt wird.
        Returns:
            Die Eingabe ohne Leerzeichen am Anfang und Ende."""
        return input(frage).strip()
    
    def zeigeMeldung(self, text: str) -> None:
        """Zeigt eine normale Meldung an"""
        print(text)
    
    def zeigeFehler(self, text: str) -> None:
        """Zeigt eine Fehlermeldung an."""
        print(f"Fehler: {text}")
        