from app.models import Post
from werkzeug.security import check_password_hash


def test_new_user(new_user):
    """
    GIVEN model User
    WHEN tworzony jest nowy użytkownik
    THEN sprawdź, czy pola username, email i hasło są poprawnie zdefiniowane
    """
    assert new_user.username == "testuser"
    assert new_user.email == "test@user.com"
    assert check_password_hash(new_user.password_hash, "Password123!")
    assert not new_user.is_admin


def test_new_admin(new_admin):
    """
    GIVEN model User
    WHEN tworzony jest nowy administrator
    THEN sprawdź, czy pole is_admin jest ustawione na True
    """
    assert new_admin.username == "adminuser"
    assert new_admin.is_admin


def test_new_post(new_user, init_database):
    """
    GIVEN model Post
    WHEN tworzony jest nowy post
    THEN sprawdź, czy pola tytuł, treść i autor są poprawnie zdefiniowane
    """
    post = Post(title="Testowy Post", content="To jest treść testowa.", author=new_user)
    init_database.session.add(post)
    init_database.session.commit()
    assert post.title == "Testowy Post"
    assert post.author.username == "testuser"
