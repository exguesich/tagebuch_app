# tagebuch_app

# Tagebuch Anwendung

Dieses Repository enthält den Source Code einer Webapplikation für ein digitales Tagebuch, entwickelt mit Flask. Der Code ist kommentiert und für den Examinator stichprobenartig überprüfbar.

## Zugriffsdetails
- **Repository-URL:** https://github.com/exguesich/tagebuch_app
- **Zugriff:** Öffentlich lesbar > http://lab50.ifalabs.org/login

## Projektstruktur
tagebuch_app/

app.py
templates/

choose_action.html
create_entry.html
view_entries.html
edit_entry.html
add_category.html
login.html
register.html


uploads/
requirements.txt

## Beschreibung der Dateien
| Datei/Ordner | Beschreibung |
|----------|----------|
| app.py   | Hauptanwendungsdatei mit allen Flask-Routen und Datenbankmodellen  | 
| templates/  | HTML-Templates für die Benutzeroberfläche   |
| login.html | Anmeldeseite  | 
| register.html   | Registrierungsseite   |
|choose_action.html  | Hauptmenü nach dem Login | 
| create_entry.html | Formular für neue Tagebucheinträge |
| view_entries.html |Übersicht aller Tagebucheinträge  | 
| edit_entry.html | Bearbeitungsformular für Einträge |
| add_category.html |Formular für neue Kategorien | 
| requirements.txt | Ordner für hochgeladene Bilder  |
| uploads/ |Python-Abhängigkeiten |


## Setup-Anweisungen
1. Repository klonen
2. Virtual Environment erstellen: python -m venv venv
3. Environment aktivieren: source venv/bin/activate
4. Abhängigkeiten installieren: pip install -r requirements.txt
5. Datenbank konfigurieren in app.py
6. Anwendung starten: python app.py
