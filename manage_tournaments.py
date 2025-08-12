# manage_tournaments.py

import random
from faker import Faker
from datetime import datetime, timedelta
from app import app, db
from app.models import Tournament

# Inicjalizacja Fakera
fake = Faker("pl_PL")

def get_random_banner():
    """Wybiera losowy baner z istniejących plików."""
    # Załóżmy, że banery turniejów są w tym samym folderze co posty
    # Możesz dostosować tę listę, jeśli masz dedykowane banery
    available_banners = [
        "default.png",
        "462f2ce34e3330b7.png",
        "2348e69900d19139.png",
        "8e374929eb6b7021.png",
        "4b9efb8cfd520b6a.png"
    ]
    return random.choice(available_banners)

def generate_tournaments(count=10):
    """Generuje określoną liczbę fałszywych turniejów."""
    with app.app_context():
        print(f"Generowanie {count} turniejów...")
        for i in range(count):
            title = f"{fake.word().capitalize()} Badminton Open {2025 + i}"
            description = "\n\n".join(fake.paragraphs(nb=random.randint(4, 8)))
            location = f"{fake.city()}, {fake.street_name()}"
            
            # Generowanie losowych dat
            start_date = datetime.now() + timedelta(days=random.randint(-60, 60))
            end_date = start_date + timedelta(days=random.randint(1, 3))
            
            max_players = random.choice([16, 32, 64])
            banner = get_random_banner()

            tournament = Tournament(
                title=title,
                description=description,
                banner_image=banner,
                location=location,
                start_date=start_date,
                end_date=end_date,
                max_players=max_players
            )
            db.session.add(tournament)
        
        db.session.commit()
        print(f"Pomyślnie dodano {count} nowych turniejów.")


def delete_all_tournaments():
    """Usuwa wszystkie turnieje z bazy danych."""
    with app.app_context():
        # Związane z turniejami rejestracje i zwycięzcy są usuwani kaskadowo,
        # więc wystarczy usunąć same turnieje.
        num_tournaments = Tournament.query.count()
        if num_tournaments == 0:
            print("Brak turniejów do usunięcia.")
            return

        print(f"Znaleziono {num_tournaments} turniejów. Czy na pewno chcesz je wszystkie usunąć? [t/n]")
        choice = input().lower()

        if choice == 't':
            Tournament.query.delete()
            db.session.commit()
            print("Wszystkie turnieje zostały usunięte.")
        else:
            print("Operacja anulowana.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Zarządzaj turniejami w bazie danych.")
    parser.add_argument('--generate', type=int, metavar='N', help='Wygeneruj N fałszywych turniejów.')
    parser.add_argument('--delete', action='store_true', help='Usuń wszystkie turnieje z bazy.')

    args = parser.parse_args()

    if args.generate:
        generate_tournaments(args.generate)
    elif args.delete:
        delete_all_tournaments()
    else:
        print("Użycie: python manage_tournaments.py [--generate N | --delete]")