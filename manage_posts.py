# manage_posts.py

import random
from faker import Faker
from app import app, db
from app.models import User, Post

# Inicjalizacja Fakera z polskimi danymi
fake = Faker("pl_PL")

def generate_posts(count=10):
    """Generuje określoną liczbę fałszywych postów."""
    with app.app_context():
        # Sprawdź, czy istnieje jakikolwiek użytkownik, który może być autorem
        author = User.query.first()
        if not author:
            print("Błąd: Nie znaleziono żadnego użytkownika w bazie danych. Stwórz najpierw użytkownika.")
            return

        print(f"Generowanie {count} postów...")
        for i in range(count):
            title = fake.sentence(nb_words=6)
            # Generowanie od 3 do 7 paragrafów losowego tekstu
            content = "\n\n".join(fake.paragraphs(nb=random.randint(3, 7)))
            
            post = Post(title=title, content=content, author=author)
            db.session.add(post)
        
        db.session.commit()
        print(f"Pomyślnie dodano {count} nowych postów.")


def delete_all_posts():
    """Usuwa wszystkie posty z bazy danych."""
    with app.app_context():
        num_posts = Post.query.count()
        if num_posts == 0:
            print("Brak postów do usunięcia.")
            return

        print(f"Znaleziono {num_posts} postów. Czy na pewno chcesz je wszystkie usunąć? [t/n]")
        choice = input().lower()

        if choice == 't':
            Post.query.delete()
            db.session.commit()
            print("Wszystkie posty zostały usunięte.")
        else:
            print("Operacja anulowana.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Zarządzaj postami w bazie danych.")
    parser.add_argument('--generate', type=int, metavar='N', help='Wygeneruj N fałszywych postów.')
    parser.add_argument('--delete', action='store_true', help='Usuń wszystkie posty z bazy.')

    args = parser.parse_args()

    if args.generate:
        generate_posts(args.generate)
    elif args.delete:
        delete_all_posts()
    else:
        print("Użycie: python manage_posts.py [--generate N | --delete]")