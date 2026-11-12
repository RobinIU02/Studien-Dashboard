"""Der Kennzahlenservice berechnet die Kennzahlen des Dashboards aus den Daten eines Studiengangs."""
from __future__ import annotations

import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from domain import Ergebnis, Modulstatus, Studiengang, addiereMonate

TAGE_PRO_MONAT = Decimal("30.4375")


class KennzahlenService:
    """Berechnet die Kennzahlen eines Studiengangs, ohne Daten zu speichern oder anzuzeigen."""
    
    def berechneErreichteEcts(self, studiengang: Studiengang) -> int:
        """Summe der ECTS aller abgeschlossenen module (bestanden oder anerkannt)."""        
        summe = 0
        for modul in studiengang.alleModule():
            if modul.status == Modulstatus.ABGESCHLOSSEN:
                summe += modul.ects
        return summe
    
    def berechneDurchschnittsnote(self, studiengang: Studiengang) -> Decimal | None:
        """Einfacher Durchschnitt der Noten aller bestandenen Module, auf zwei Stellen gerundet"""
        noten = []
        for modul in studiengang.alleModule():
            for leistung in modul.pruefungsleistungen:
                if leistung.ergebnis == Ergebnis.BESTANDEN:
                    noten.append(leistung.note)
                    
        if not noten:
            return None
        
        durchschnitt = sum(noten) / len(noten)
        return durchschnitt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
    def berechneErstversuchsquote(self, studiengang: Studiengang) -> Decimal | None:
        """Anteil der Module, die im ersten Versuch bestanden wurden, an allen geprüften Modulen in Prozent. Ohne geprüfte Module: None."""
        geprueft = 0
        im_erstversuch = 0
        for modul in studiengang.alleModule():
            ist_geprueft = False
            for leistung in modul.pruefungsleistungen:
                if leistung.ergebnis in (Ergebnis.BESTANDEN, Ergebnis.NICHT_BESTANDEN):
                    ist_geprueft = True
                if leistung.versuchsnummer == 1 and leistung.ergebnis == Ergebnis.BESTANDEN:
                    im_erstversuch += 1
            if ist_geprueft:
                geprueft += 1

        if geprueft == 0:
            return None

        quote = Decimal(im_erstversuch) * 100 / geprueft
        return quote.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        
    def _vergangeneMonate(self, studiengang: Studiengang, stichtag: date) -> decimal:
        """Monate seit Studienbeginn bis zum Stichtag als Dezimalzahl."""
        tage = (stichtag - studiengang.startdatum).days
        if tage < 0:
            tage = 0
        return Decimal(tage) / TAGE_PRO_MONAT
    
    def berechneSollEcts(self, studiengang: Studiengang, stichtag: date | None = None) -> Decimal:
        """Soll-ECTS zum Stichtag (Standard: heute): Gesamt-ECTS mal vergangene Monate durch Regelzeit, höchstens die Gesamt-ECTS."""
        if stichtag is None:
            stichtag = date.today()
        monate = self._vergangeneMonate(studiengang, stichtag)
        soll = Decimal(studiengang.gesamtEcts) * monate / studiengang.regelzeitInMonaten
        if soll > studiengang.gesamtEcts:
            soll = Decimal(studiengang.gesamtEcts)
        return soll.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    
    def berechnePrognose(self, studiengang: Studiengang, stichtag: date | None = None) -> date | None:
        """Voraussichtliches Abschlussdatum bei bisherigem Tempo. Ohne erreichte ECTS oder vergangene Zeit: None."""
        if stichtag is None:
            stichtag = date.today()
        erreichte = self.berechneErreichteEcts(studiengang)
        monate = self._vergangeneMonate(studiengang, stichtag)
        if erreichte == 0 or monate == 0:
            return None
        gesamtmonate = monate * studiengang.gesamtEcts / erreichte
        return addiereMonate(studiengang.startdatum, math.ceil(gesamtmonate))