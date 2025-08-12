def test_index_page(client, init_database):
    """
    GIVEN Aplikacja Flask
    WHEN strona główna jest otwierana (GET)
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "Indo-Polish Badminton" in response.data.decode("utf-8")


def test_news_page(client, init_database):
    """
    GIVEN Aplikacja Flask
    WHEN strona /news jest otwierana (GET)
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    response = client.get("/news")
    assert response.status_code == 200
    assert "Wszystkie Posty" in response.data.decode("utf-8")


def test_contact_page(client):
    """
    GIVEN Aplikacja Flask
    WHEN strona /kontakt jest otwierana (GET)
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    response = client.get("/kontakt")
    assert response.status_code == 200
    assert "Skontakuj się z nami" in response.data.decode("utf-8")
