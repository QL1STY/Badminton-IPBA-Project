import os
from dotenv import load_dotenv
import click
from flask.cli import with_appcontext

# Wczytuje zmienne z pliku .env
load_dotenv()

from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, _, format_datetime
from flask_mail import Mail
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer

# --- Konfiguracja aplikacji ---
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["TINYMCE_API_KEY"] = os.environ.get("TINYMCE_API_KEY")
app.config["MAIL_RECIPIENT"] = os.environ.get("MAIL_RECIPIENT")
# --- Konfiguracja bazy danych ---
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
        "postgres://", "postgresql://", 1
    )
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "site.db"
    )
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- Konfiguracja Maila (z poprawką) ---
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() in [
    "true",
    "on",
    "1",
]
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"] or None
app.config["MAIL_RECIENT"] = os.environ.get("MAIL_RECIPIENT")

# --- Konfiguracja paginacji ---
app.config["POSTS_PER_PAGE"] = 9
app.config["IMAGES_PER_PAGE"] = 8

# --- Konfiguracja Języków ---
app.config["LANGUAGES"] = {"pl": "Polski", "en": "English"}
babel = Babel(app)
s = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def get_locale():
    return session.get("language", "pl")


babel.init_app(app, locale_selector=get_locale)

# --- Inicjalizacja rozszerzeń ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_message = _(
    "Proszę się zalogować, aby uzyskać dostęp do tej strony."
)
login_manager.login_view = "logowanie"

# Udostępnij format_datetime w szablonach Jinja
app.jinja_env.globals["format_datetime"] = format_datetime

# --- WAŻNE: Importy tras i modeli MUSZĄ BYĆ PONIŻEJ ---
# To rozwiązuje problem cyklicznego importu
from app import routes, models


# --- Komenda CLI do ustawiania pierwszego admina ---
@app.cli.command("init-admin")
@with_appcontext
def init_admin_command():
    """Nadaje uprawnienia administratora użytkownikowi z ADMIN_EMAIL."""
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        user = models.User.query.filter_by(email=admin_email).first()
        if user:
            if not user.is_admin:
                user.is_admin = True
                db.session.commit()
                click.echo(
                    f"Nadano uprawnienia administratora użytkownikowi: {admin_email}"
                )
            else:
                click.echo(f"Użytkownik {admin_email} już jest administratorem.")
        else:
            click.echo(f"Nie znaleziono użytkownika z adresem e-mail: {admin_email}")
    else:
        click.echo("Zmienna środowiskowa ADMIN_EMAIL nie jest ustawiona.")
