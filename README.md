# Studien-Dashboard
Konsolenanwendung, die den Studienfortschritt im Bachelorstudium Cyber Security überwacht.
## Was das Programm zeigt
- Ziel 1: Studium in der Regelzeit (Soll- und Ist-ECTS, Prognose)
- Ziel 2: Notendurchschnitt (Wunschwert, Grenzwert, aktuelle Note)
- Ziel 3: Modulstatus und Erstversuche
- Module hinzufügen und Ergebnisse eintragen

## Voraussetzungen

- Python 3.13 oder neuer (entwickelt mit Python 3.13 unter Windows, zusätzlich getestet mit Python 3.14)
- Keine zusätzlichen Bibliotheken, nur die Standardbibliothek

## Starten
    python main.py

Das Programm liest die Studiendaten aus `daten/studiengang.json` und zeigt ein Menü. Mit `0` wird es beendet.
Änderungen über das Menü werden in `daten/studiengang.json` gespeichert.
Die JSON enthält meine momentanen Studiendaten(Stand: November 2026).

## Aufbau

| Datei | Aufgabe |
|---|---|
| `domain.py` | Fachklassen: Studiengang, Semester, Modul, Prüfungsleistung |
| `service.py` | Berechnung der Kennzahlen |
| `repository.py` | Laden und Speichern der JSON-Datei |
| `dto.py` | Datenpakete für die Anzeige |
| `view.py` | Ausgabe und Eingabe in der Konsole |
| `controller.py` | Ablauf und Menü |
| `app.py`, `main.py` | Zusammenbau und Start |
| `daten/` | Studiendaten als JSON |
| `tests/` | Testprogramme |

## Tests

    python tests/test_kennzahlen.py
    python tests/test_repository.py
