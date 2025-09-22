
## Source Code

### `app.py`
from flask import Flask, render_template, request, redirect, url_for, flash  # Flask-Zeug importieren
from flask_sqlalchemy import SQLAlchemy  # Datenbank-Kram
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # Login-Features
from werkzeug.security import generate_password_hash, check_password_hash  # Passwörter verschlüsseln
from werkzeug.utils import secure_filename  # Dateien sicher hochladen
from datetime import datetime  # Datum und Zeit
import os  # Dateien und Ordner verwalten

# Flask App starten
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein_geheimer_schluessel'  # TODO: Besseren Key machen für echte App!
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tagebuch_user:dein_db_passwort@localhost/tagebuch_db'  # MySQL-Verbindung
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Macht die App schneller
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')  # Wo Bilder gespeichert werden
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ordner erstellen falls er nicht existiert

# Datenbank Setup
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Wo soll man hingeschickt werden wenn nicht eingeloggt

# Tabellen definieren
class User(db.Model, UserMixin):  # User-Tabelle
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Category(db.Model):  # Kategorien wie "Uni", "Privat", etc.
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    entries = db.relationship('Entry', backref='category')  # Verbindung zu den Einträgen

class Entry(db.Model):  # Die eigentlichen Tagebucheinträge
    __tablename__ = 'entry'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255))
    user = db.relationship('User', backref='entries')  # Wem gehört der Eintrag

# Login-System initialisieren
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Datenbank erstellen falls sie noch nicht da ist
from sqlalchemy import inspect
with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table('user'):
        db.create_all()
        print("Datenbanktabellen erstellt.")  # Zum debuggen
    else:
        print("Datenbanktabellen existieren bereits.")

# Standard-Kategorien hinzufügen
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

# Website-Routen
@app.route('/')
def index():
    return redirect(url_for('login'))  # Direkt zum Login

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)  # Passwort verschlüsseln - wichtig!
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        # flash('Registrierung erfolgreich!')  # Hab ich auskommentiert, nervt sonst
        return redirect(url_for('login'))
    return render_template('register.html')  # Registrierungsseite anzeigen

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        print(f"Login-Versuch: Email={email}, Password={password}")  # Debug-Output
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User gefunden: {user.username}, Hash={user.password_hash}")
            if check_password_hash(user.password_hash, password):
                login_user(user)
                # flash('Login erfolgreich!')  # Auch auskommentiert
                return redirect(url_for('choose_action'))
            else:
                print("Passwortprüfung fehlgeschlagen")
        else:
            print("Kein User gefunden")
        # flash('Falsche Anmeldedaten!')  # Nervige Flash-Messages deaktiviert
    return render_template('login.html')  # Login-Seite zeigen

@app.route('/choose_action')
@login_required
def choose_action():
    return render_template('choose_action.html')  # Hauptmenü nach Login

@app.route('/view_entries')
@login_required
def view_entries():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    return render_template('view_entries.html', entries=entries)  # Alle meine Einträge

@app.route('/create_entry', methods=['GET', 'POST'])
@login_required
def create_entry():
    categories = Category.query.all()
    if request.method == 'POST':
        print("Formulardaten:", request.form)  # Debug um zu sehen was ankommt
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
                filename = secure_filename(image.filename)  # Böse Dateinamen verhindern
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
            print("Allgemeiner Fehler:", e)  # Falls was anderes schiefgeht
            return render_template('create_entry.html', categories=categories, error=f"Fehler: {str(e)}")
    return render_template('create_entry.html', categories=categories)  # Neuen Eintrag erstellen

@app.route('/edit_entry/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_entry(id):
    entry = Entry.query.get_or_404(id)  # Eintrag holen oder 404 wenn nicht da
    if entry.user_id != current_user.id:
        flash('Nicht berechtigt!')  # Andere können meine Einträge nicht bearbeiten
        return redirect(url_for('view_entries'))
    categories = Category.query.all()
    if request.method == 'POST':
        print("Edit-Formulardaten:", request.form)  # Debug für Bearbeitung
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
    return render_template('edit_entry.html', entry=entry, categories=categories)  # Eintrag bearbeiten

@app.route('/delete_entry/<int:id>', methods=['POST'])
@login_required
def delete_entry(id):
    entry = Entry.query.get_or_404(id)
    if entry.user_id != current_user.id:
        flash('Nicht berechtigt!')
        return redirect(url_for('view_entries'))
    db.session.delete(entry)
    db.session.commit()
    flash('Eintrag erfolgreich gelöscht!')  # Hier lass ich die Message mal drin
    return redirect(url_for('view_entries'))  # Zurück zur Übersicht

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
            flash('Kategorie erfolgreich hinzugefügt!')  # Feedback ist schon ok hier
        else:
            flash('Name und Beschreibung sind erforderlich!')
        return redirect(url_for('create_entry'))  # Zurück zum Erstellen
    return render_template('add_category.html')  # Neue Kategorie anlegen

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))  # Ausloggen und zurück zum Login

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Server starten für lokales Testen
