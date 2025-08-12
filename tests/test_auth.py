def test_registration_page(client):
    """
    GIVEN Aplikacja Flask
    WHEN strona /rejestracja jest otwierana (GET)
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    response = client.get("/rejestracja")
    assert response.status_code == 200
    assert "Stwórz swoje konto" in response.data.decode("utf-8")


def test_valid_registration(client, init_database):
    """
    GIVEN Aplikacja Flask
    WHEN nowy użytkownik jest rejestrowany (POST) z poprawnymi danymi
    THEN sprawdź, czy następuje przekierowanie na stronę logowania
    """
    response = client.post(
        "/rejestracja",
        data=dict(
            first_name="Jan",
            last_name="Kowalski",
            username="jankowalski",
            email="jan.kowalski@test.pl",
            password="Password123!",
            confirm_password="Password123!",
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Logowanie" in response.data.decode("utf-8")
    assert "Konto zostało utworzone!" in response.data.decode("utf-8")


def test_login_page(client):
    """
    GIVEN Aplikacja Flask
    WHEN strona /logowanie jest otwierana (GET)
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    response = client.get("/logowanie")
    assert response.status_code == 200
    assert "Zaloguj się do swojego konta" in response.data.decode("utf-8")


def test_valid_login_logout(client, new_user):
    """
    GIVEN Aplikacja Flask i zarejestrowany użytkownik
    WHEN użytkownik loguje się z poprawnymi danymi, a następnie wylogowuje
    THEN sprawdź, czy logowanie i wylogowanie kończą się sukcesem
    """
    # Test logowania
    response = client.post(
        "/logowanie",
        data=dict(login_identifier="testuser", password="Password123!"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Zalogowano pomyślnie!" in response.data.decode("utf-8")
    assert "Wyloguj" in response.data.decode("utf-8")

    # Test wylogowania
    response = client.get("/wyloguj", follow_redirects=True)
    assert response.status_code == 200
    assert "Zaloguj się" in response.data.decode("utf-8")
