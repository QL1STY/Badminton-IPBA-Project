def test_admin_dashboard_access_denied_for_user(client, new_user):
    """
    GIVEN Aplikacja Flask i zalogowany zwykły użytkownik
    WHEN użytkownik próbuje uzyskać dostęp do panelu admina
    THEN sprawdź, czy otrzymuje błąd 403 (Forbidden)
    """
    client.post(
        "/logowanie",
        data=dict(login_identifier="test@user.com", password="Password123!"),
    )
    response = client.get("/admin/dashboard")
    assert response.status_code == 403


def test_admin_dashboard_access_for_admin(client, new_admin):
    """
    GIVEN Aplikacja Flask i zalogowany administrator
    WHEN administrator uzyskuje dostęp do panelu admina
    THEN sprawdź, czy odpowiedź serwera ma status 200
    """
    client.post(
        "/logowanie",
        data=dict(login_identifier="admin@user.com", password="AdminPass123!"),
    )
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Panel Administratora" in response.data.decode("utf-8")


def test_admin_can_manage_users(client, new_admin, new_user):
    """
    GIVEN Aplikacja Flask, zalogowany administrator i istniejący użytkownik
    WHEN administrator otwiera stronę zarządzania użytkownikami
    THEN sprawdź, czy widzi na liście istniejącego użytkownika
    """
    client.post(
        "/logowanie",
        data=dict(login_identifier="admin@user.com", password="AdminPass123!"),
    )
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert bytes(new_user.username, "utf-8") in response.data
