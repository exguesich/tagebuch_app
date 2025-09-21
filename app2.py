
## Source Code

### `app.py`
```python
from flask import Flask, render_template, request, redirect, url_for, flash  # Flask-Basis für Webentwicklung
from flask_sqlalchemy import SQLAlchemy  # Für Datenbankinteraktionen
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # Für Benutzerverwaltung
from werkzeug.security import generate_password_hash, check_password_hash  # Für sichere Passwortverarbeitung
from werkzeug.utils import secure_filename  # Für sichere Datei-Namen
from datetime import datetime  # Für Datumsverarbeitung
import os  # Für Dateisystemoperationen

# Initialisiere Flask-Anwendung
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein_geheimer_schluessel'  # Muss durch einen sicheren Schlüssel ersetzt werden (sicherheitskritisch)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tagebuch_user:dein_db_passwort@localhost/tagebuch_db'  # DB-Konfiguration
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Deaktiviert Tracking für Performance
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')  # Ordner für hochgeladene Bilder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Erstellt Upload-Ordner, falls nicht vorhanden

# Datenbank und Login-Manager initialisieren
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Standard-Login-Seite

# Modelle für Datenbank
class User(db.Model, UserMixin):  # Benutzermodell mit Flask-Login-Unterstützung
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Category(db.Model):  # Kategorienmodell
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    entries = db.relationship('Entry', backref='category')  # Beziehung zu Einträgen

class Entry(db.Model):  # Eintragsmodell
    __tablename__ = 'entry'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255))
    user = db.relationship('User', backref='entries')  # Beziehung zu Benutzer

# Benutzer-Loader für Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Datenbank initialisieren
from sqlalchemy import inspect
with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table('user'):
        db.create_all()
        print("Datenbanktabellen erstellt.")  # Debugging-Ausgabe
    else:
        print("Datenbanktabellen existieren bereits.")

# Initiale Kategorien hinzufügen
with app.app_context():
    if Category.query.count() == 0:
        categories = [
            ('Persönlich', 'Persönliche Einträge'),
            ('Arbeit', 'Arbeitsbezogene Einträge'),
            ('Reisen', 'Reiseerlebnisse'),
            ('Gedanken', 'Allgemeine Gedanken'),
            ('Erinnerungen', 'Erinnerungen')
        ]
        for name, desc in categories:
            cat = Category(name=name, description=desc)
            db.session.add(cat)
        db.session.commit()

# Routen
@app.route('/')
def index():
    return redirect(url_for('login'))  # Umleitung zur Login-Seite

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)  # Passwort sichern
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        # flash('Registrierung erfolgreich!')  # Optional, aktuell deaktiviert
        return redirect(url_for('login'))
    return render_template('register.html')  # Registrierungsformular anzeigen

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        print(f"Login-Versuch: Email={email}, Password={password}")  # Debugging
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User gefunden: {user.username}, Hash={user.password_hash}")
            if check_password_hash(user.password_hash, password):
                login_user(user)
                # flash('Login erfolgreich!')  # Deaktiviert, um keine Nachrichten anzuzeigen
                return redirect(url_for('choose_action'))
            else:
                print("Passwortprüfung fehlgeschlagen")
        else:
            print("Kein User gefunden")
        # flash('Falsche Anmeldedaten!')  # Deaktiviert
    return render_template('login.html')  # Login-Formular anzeigen

@app.route('/choose_action')
@login_required
def choose_action():
    return render_template('choose_action.html')  # Auswahlseite anzeigen

@app.route('/view_entries')
@login_required
def view_entries():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    return render_template('view_entries.html', entries=entries)  # Alle Einträge anzeigen

@app.route('/create_entry', methods=['GET', 'POST'])
@login_required
def create_entry():
    categories = Category.query.all()
    if request.method == 'POST':
        print("Formulardaten:", request.form)  # Debugging
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        mood = request.form.get('mood', '').strip()
        date_str = request.form.get('date', '')
        category_id = request.form.get('category')
        if not (title and content and date_str and category_id):
            print("Fehlende Pflichtfelder:", {k: v for k, v in request.form.items() if not v})
            return render_template('create_entry.html', categories=categories, error="Bitte fülle alle Pflichtfelder aus!")
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            image = request.files.get('image')
            image_path = None
            if image and image.filename:
                filename = secure_filename(image.filename)  # Sicherer Dateiname
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
            new_entry = Entry(title=title, content=content, mood=mood, date=date, category_id=category_id, user_id=current_user.id, image_path=image_path)
            db.session.add(new_entry)
            db.session.commit()
            print("Eintrag erfolgreich erstellt:", title)
            return redirect(url_for('view_entries'))
        except ValueError as e:
            print("Datumsfehler:", e)
            return render_template('create_entry.html', categories=categories, error="Ungültiges Datumsformat!")
        except Exception as e:
            print("Allgemeiner Fehler:", e)
            return render_template('create_entry.html', categories=categories, error=f"Fehler: {str(e)}")
    return render_template('create_entry.html', categories=categories)  # Erstellungsformular anzeigen

@app.route('/edit_entry/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_entry(id):
    entry = Entry.query.get_or_404(id)  # Hole Eintrag oder 404, wenn nicht gefunden
    if entry.user_id != current_user.id:
        flash('Nicht berechtigt!')  # Sicherheit: Nur Eigentümer kann bearbeiten
        return redirect(url_for('view_entries'))
    categories = Category.query.all()
    if request.method == 'POST':
        print("Edit-Formulardaten:", request.form)  # Debugging
        title = request.form.get('title', entry.title).strip()
        content = request.form.get('content', entry.content).strip()
        mood = request.form.get('mood', entry.mood).strip()
        date_str = request.form.get('date', entry.date.strftime('%Y-%m-%d'))
        category_id = request.form.get('category', str(entry.category_id))
        if not (title and content and date_str and category_id):
            print("Fehlende Pflichtfelder:", {k: v for k, v in request.form.items() if not v})
            return render_template('edit_entry.html', entry=entry, categories=categories, error="Bitte fülle alle Pflichtfelder aus!")
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            image = request.files.get('image')
            if image and image.filename:
                filename = secure_filename(image.filename)
                entry.image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(entry.image_path)
            entry.title = title
            entry.content = content
            entry.mood = mood
            entry.date = date
            entry.category_id = category_id
            db.session.commit()
            print("Eintrag erfolgreich bearbeitet:", title)
            return redirect(url_for('view_entries'))
        except ValueError as e:
            print("Datumsfehler:", e)
            return render_template('edit_entry.html', entry=entry, categories=categories, error="Ungültiges Datumsformat!")
        except Exception as e:
            print("Allgemeiner Fehler:", e)
            return render_template('edit_entry.html', entry=entry, categories=categories, error=f"Fehler: {str(e)}")
    return render_template('edit_entry.html', entry=entry, categories=categories)  # Bearbeitungsformular anzeigen

@app.route('/delete_entry/<int:id>', methods=['POST'])
@login_required
def delete_entry(id):
    entry = Entry.query.get_or_404(id)
    if entry.user_id != current_user.id:
        flash('Nicht berechtigt!')
        return redirect(url_for('view_entries'))
    db.session.delete(entry)
    db.session.commit()
    flash('Eintrag erfolgreich gelöscht!')  # Optional, kann deaktiviert werden
    return redirect(url_for('view_entries'))  # Zurück zu allen Einträgen

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if name and description:
            new_category = Category(name=name, description=description)
            db.session.add(new_category)
            db.session.commit()
            flash('Kategorie erfolgreich hinzugefügt!')  # Optional, kann deaktiviert werden
        else:
            flash('Name und Beschreibung sind erforderlich!')
        return redirect(url_for('create_entry'))  # Zurück zur Erstellungsseite
    return render_template('add_category.html')  # Kategorie-Formular anzeigen

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))  # Logout und Umleitung

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Lokaler Server für Entwicklung
