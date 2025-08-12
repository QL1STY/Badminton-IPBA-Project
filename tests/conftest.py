import pytest
from app import app as flask_app, db
from app.models import User
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="module")
def app():
    """Tworzy instancję aplikacji Flask na potrzeby testów."""
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SERVER_NAME": "localhost",
        }
    )
    yield flask_app


@pytest.fixture(scope="module")
def client(app):
    """Tworzy klienta testowego dla aplikacji Flask."""
    return app.test_client()


@pytest.fixture(scope="module")
def runner(app):
    """Tworzy CLI runnera dla aplikacji Flask."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def init_database(app):
    """Inicjalizuje bazę danych przed każdym testem i czyści ją po teście."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def new_user(init_database, app):
    """Tworzy i zwraca standardowego użytkownika."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@user.com",
            password_hash=generate_password_hash("Password123!"),
            first_name="Test",
            last_name="User",
            email_verified=True,
        )
        db.session.add(user)
        db.session.commit()
        # Ponownie pobieramy użytkownika, aby upewnić się, że jest przywiązany do sesji
        user = User.query.filter_by(email="test@user.com").first()
        return user


@pytest.fixture(scope="function")
def new_admin(init_database, app):
    """Tworzy i zwraca użytkownika z uprawnieniami administratora."""
    with app.app_context():
        admin = User(
            username="adminuser",
            email="admin@user.com",
            password_hash=generate_password_hash("AdminPass123!"),
            first_name="Admin",
            last_name="User",
            is_admin=True,
            email_verified=True,
        )
        db.session.add(admin)
        db.session.commit()
        # Ponownie pobieramy użytkownika, aby upewnić się, że jest przywiązany do sesji
        admin = User.query.filter_by(email="admin@user.com").first()
        return admin
