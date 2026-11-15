"""Zusammenbau des Studien-Dashboards.
Hier werden Repository, Service, View und Controller erzeugt und verbunden. Nur an dieser Stelle steht fest, dass JSON verwendet wird"""

from __future__ import annotations

from pathlib import Path

from controller import Controller
from repository import JsonStudiengangRepository
from service import KennzahlenService
from view import KonsolenView


class DashboardApp:
    """Setzt die Bausteine des Dashboards zusammen und startet es.
    Attribute:
        dateipfad: Pfad der JSON-Datei mit den Studiendaten."""
        
    def __init__(self) -> None:
        """Legt den Pfad der Datendatei fest.
        Der Pfad hängt vom Ort dieser Datei ab. Das Programm läuft dadurch auch dann, wenn es aus einem anderen Ordner gestartet wird."""
        ordner = Path(__file__).resolve().parent
        self.dateipfad = str(ordner / "daten" / "studiengang.json")
    
    def starte(self) -> None:
        """Erzeugt alle Bausteine und startet das Hauptmenü.
        Kann die Datendatei nicht gelesen werden, erscheint eine Fehlermeldung und das Programm endet."""
        view = KonsolenView()
        try:
            controller = Controller(
                JsonStudiengangRepository(self.dateipfad),
                KennzahlenService(),
                view,
            )
        except (OSError, ValueError, KeyError) as fehler:
            view.zeigeFehler(f"Die Daten konnten nicht geladen werden: {fehler}")
            return
        controller.starte()
