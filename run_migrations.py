from flask_migrate import upgrade
from app import app, db

print("--- [MIGRATION SCRIPT] Rozpoczynam migrację bazy danych ---")

# app.app_context() zapewnia, że wszystkie rozszerzenia Flaska,
# w tym SQLAlchemy, są poprawnie załadowane.
with app.app_context():
    upgrade()

print("--- [MIGRATION SCRIPT] Migracja bazy danych zakończona pomyślnie ---")