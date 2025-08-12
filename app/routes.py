# app/routes.py

import magic
from functools import wraps
from math import ceil
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session,
    abort,
    request,
    Response,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
from flask_babel import _
from app import app, db, mail
from app.forms import (
    RegistrationForm,
    LoginForm,
    PostForm,
    ContactForm,
    RequestResetForm,
    ResetPasswordForm,
    UpdateAccountForm,
    ChangePasswordForm,
    DeleteAccountForm,
)
from app.models import User, Post
import os
from PIL import Image
import secrets
from flask_mail import Message
from datetime import datetime, timedelta
from sqlalchemy import asc
import bleach
import json
from app.forms import TournamentForm
from app.models import Tournament, TournamentRegistration
from app.forms import AddWinnerForm
from app.models import TournamentWinner
from app.forms import DeleteForm
from app.forms import ConfirmPasswordForm


# --- Funkcja do wysyłania emaili ---
def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


# --- DEKORATOR DO SPRAWDZANIA UPRAWNIEŃ ADMINA ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


# --- FUNKCJA DO ZAPISYWANIA OBRAZKÓW ---
def save_picture(form_picture):
    file_header = form_picture.stream.read(2048)
    form_picture.stream.seek(0)

    mime_type = magic.from_buffer(file_header, mime=True)
    allowed_mimetypes = ["image/jpeg", "image/png"]

    if mime_type not in allowed_mimetypes:
        return None

    # --- 2. Kontynuacja zapisu pliku ---
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)

    f_ext = ".jpg" if mime_type == "image/jpeg" else ".png"

    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/post_pics", picture_fn)

    output_size = (1200, 675)
    try:
        i = Image.open(form_picture.stream)
        i.thumbnail(output_size)
        i.save(picture_path)
    except Exception as e:
        app.logger.error(f"Błąd podczas zapisywania obrazu: {e}")
        return None

    return picture_fn


# --- GŁÓWNE WIDOKI APLIKACJI ---


@app.route("/")
@app.route("/index")
def index():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(3).all()
    today = datetime.utcnow().date()
    upcoming_tournaments = (
        Tournament.query.filter(Tournament.start_date >= today)
        .order_by(Tournament.start_date.asc())
        .limit(3)
        .all()
    )
    past_tournaments = (
        Tournament.query.filter(Tournament.start_date < today)
        .order_by(Tournament.start_date.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "index.html",
        title=_("Strona Główna"),
        posts=posts,
        upcoming_tournaments=upcoming_tournaments,
        past_tournaments=past_tournaments,
        asc=asc,
    )


@app.route("/rejestracja", methods=["GET", "POST"])
def rejestracja():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email_verified=False,
        )
        db.session.add(user)
        db.session.commit()

        token = user.generate_token(salt="email-confirm-salt")
        confirm_url = url_for("verify_email", token=token, _external=True)
        html = render_template("email/verify_email.html", confirm_url=confirm_url)
        send_email(
            "Potwierdź swój adres email",
            [user.email],
            "Potwierdź swój adres email",
            html,
        )

        flash(
            _(
                "Konto zostało utworzone! Link weryfikacyjny został wysłany na Twój email."
            ),
            "success",
        )
        return redirect(url_for("logowanie"))
    return render_template("register.html", title=_("Rejestracja"), form=form)


@app.route("/verify_email/<token>")
def verify_email(token):
    user = User.verify_token(token, salt="email-confirm-salt")
    if user:
        if user.email_verified:
            flash(_("Twoje konto jest już zweryfikowane."), "info")
        else:
            user.email_verified = True
            db.session.commit()
            flash(
                _(
                    "Twój email został pomyślnie zweryfikowany! Możesz się teraz zalogować."
                ),
                "success",
            )
    else:
        flash(_("Link weryfikacyjny jest nieprawidłowy lub wygasł."), "danger")
    return redirect(url_for("logowanie"))


@app.route("/logowanie", methods=["GET", "POST"])
def logowanie():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = (
            User.query.filter_by(email=form.login_identifier.data).first()
            or User.query.filter_by(username=form.login_identifier.data).first()
        )

        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.email_verified:
                flash(
                    _(
                        "Twoje konto nie zostało jeszcze zweryfikowane. Sprawdź swoją skrzynkę mailową."
                    ),
                    "warning",
                )
                return redirect(url_for("logowanie"))

            login_user(user, remember=form.remember.data)
            flash(_("Zalogowano pomyślnie!"), "success")
            return redirect(url_for("index"))
        else:
            flash(_("Logowanie nie powiodło się. Sprawdź dane i hasło."), "danger")
    return render_template("login.html", title=_("Logowanie"), form=form)


@app.route("/reset_hasla", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_token(salt="password-reset-salt")
            reset_url = url_for("reset_token", token=token, _external=True)
            html = render_template("email/reset_password.html", reset_url=reset_url)
            send_email("Resetowanie hasła", [user.email], "Resetowanie hasła", html)
        flash(
            _(
                "Jeśli konto istnieje, instrukcje resetowania hasła zostały wysłane na email."
            ),
            "info",
        )
        return redirect(url_for("logowanie"))
    return render_template("reset_request.html", title=_("Reset Hasła"), form=form)


@app.route("/reset_hasla/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    user = User.verify_token(token, salt="password-reset-salt")
    if user is None:
        flash(_("Link do resetowania hasła jest nieprawidłowy lub wygasł."), "warning")
        return redirect(url_for("reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password_hash = hashed_password
        db.session.commit()
        flash(
            _("Twoje hasło zostało zaktualizowane! Możesz się teraz zalogować."),
            "success",
        )
        return redirect(url_for("logowanie"))
    return render_template("reset_token.html", title=_("Reset Hasła"), form=form)


@app.route("/wyloguj")
def wyloguj():
    logout_user()
    return redirect(url_for("index"))


@app.route("/news")
def news():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"]
    )
    return render_template("news.html", title=_("News"), posts=posts)


@app.route("/sponsorzy")
def sponsorzy():
    return render_template("sponsors.html", title=_("Sponsorzy i Dofinansowanie"))


@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    form = ContactForm()
    if current_user.is_authenticated and request.method == "GET":
        form.name.data = f"{current_user.first_name} {current_user.last_name}"
        form.email.data = current_user.email

    if form.validate_on_submit():
        try:
            msg = Message(
                subject=form.subject.data,
                sender=app.config["MAIL_USERNAME"],
                recipients=[app.config["MAIL_RECIPIENT"]],
            )

            msg.body = f"""
            Wiadomość od: {form.name.data} ({form.email.data})
            ---
            {form.message.data}
            """

            mail.send(msg)

            flash(_("Twoja wiadomość została wysłana! Dziękujemy."), "success")
            return redirect(url_for("kontakt"))
        except Exception as e:
            # Zmieniono z print() na app.logger.error() dla lepszego logowania
            app.logger.error(f"Błąd wysyłania maila: {e}")
            flash(
                _(
                    "Wystąpił błąd podczas wysyłania wiadomości. Spróbuj ponownie później."
                ),
                "danger",
            )

    return render_template("contact.html", title=_("Kontakt"), form=form)


@app.route("/regulamin")
def regulamin():
    return render_template("regulations.html", title=_("Regulamin"))


@app.route("/change_language/<lang>")
def change_language(lang):
    if lang in app.config["LANGUAGES"]:
        session["language"] = lang
    return redirect(request.referrer or url_for("index"))


@app.route("/post/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        image_filename = "default.png"
        if form.picture.data:
            saved_filename = save_picture(form.picture.data)
            if saved_filename:
                image_filename = saved_filename
            else:
                flash(
                    _(
                        "Przesłany plik nie jest prawidłowym obrazem (dozwolone formaty: JPG, PNG)."
                    ),
                    "danger",
                )
                return render_template(
                    "create_post.html", title=_("Nowy Post"), form=form
                )

        cleaned_content = bleach.clean(
            form.content.data,
            tags=["p", "br", "b", "i", "u", "strong", "em", "a"],
            attributes={"a": ["href", "title"]},
        )

        post = Post(
            title=form.title.data,
            content=cleaned_content,
            author=current_user,
            image_file=image_filename,
        )
        db.session.add(post)
        db.session.commit()
        flash(_("Twój post został opublikowany!"), "success")
        return redirect(url_for("news"))
    return render_template("create_post.html", title=_("Nowy Post"), form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    delete_form = DeleteForm()
    return render_template(
        "post.html", title=post.title, post=post, delete_form=delete_form
    )


@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
@admin_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            saved_filename = save_picture(form.picture.data)
            if saved_filename:
                post.image_file = saved_filename
            else:
                flash(
                    _(
                        "Przesłany plik nie jest prawidłowym obrazem (dozwolone formaty: JPG, PNG)."
                    ),
                    "danger",
                )
                return render_template(
                    "create_post.html", title=_("Edytuj Post"), form=form
                )
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash(_("Post został zaktualizowany!"), "success")
        return redirect(url_for("post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title=_("Edytuj Post"), form=form)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash(_("Twój post został usunięty."), "success")
    return redirect(url_for("index"))


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    update_form = UpdateAccountForm(original_username=current_user.username)
    password_form = ChangePasswordForm()

    days_left = None
    if current_user.username_last_changed and not current_user.can_change_username():
        next_change_date = current_user.username_last_changed + timedelta(days=14)
        time_remaining = next_change_date - datetime.utcnow()
        days_left = ceil(time_remaining.total_seconds() / (24 * 3600))

    if update_form.validate_on_submit() and update_form.submit_details.data:
        if current_user.username != update_form.username.data:
            if current_user.can_change_username():
                current_user.username = update_form.username.data
                current_user.username_last_changed = datetime.utcnow()
            else:
                flash(
                    _("Nazwę użytkownika można zmieniać tylko raz na 14 dni."),
                    "warning",
                )
                return redirect(url_for("profil"))

        current_user.first_name = update_form.first_name.data
        current_user.last_name = update_form.last_name.data

        db.session.commit()
        flash(_("Twoje dane zostały zaktualizowane!"), "success")
        return redirect(url_for("profil"))

    if password_form.validate_on_submit() and password_form.submit_password.data:
        if check_password_hash(
            current_user.password_hash, password_form.old_password.data
        ):
            current_user.password_hash = generate_password_hash(
                password_form.new_password.data
            )
            db.session.commit()
            flash(_("Twoje hasło zostało zmienione!"), "success")
            return redirect(url_for("profil"))
        else:
            flash(_("Stare hasło jest nieprawidłowe."), "danger")

    if request.method == "GET":
        update_form.first_name.data = current_user.first_name
        update_form.last_name.data = current_user.last_name
        update_form.username.data = current_user.username

    return render_template(
        "profile.html",
        title=_("Profil Użytkownika"),
        update_form=update_form,
        password_form=password_form,
        days_left=days_left,
    )

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    
    if request.method == 'GET':
        # Generowanie i wysyłka kodu
        code = str(secrets.randbelow(1000000)).zfill(6)
        session['delete_code'] = code
        session['delete_code_timestamp'] = datetime.utcnow().timestamp()
        
        html = render_template("email/delete_account_code.html", code=code)
        send_email(
            "Kod potwierdzający usunięcie konta",
            [current_user.email],
            f"Twój kod potwierdzający to: {code}",
            html
        )
        flash(_("Wysłaliśmy kod potwierdzający na Twój adres e-mail. Kod jest ważny przez 10 minut."), "info")

    if form.validate_on_submit():
        # Sprawdzenie, czy kod nie wygasł (10 minut)
        if 'delete_code_timestamp' not in session or \
           datetime.utcnow().timestamp() - session['delete_code_timestamp'] > 600:
            flash(_("Kod potwierdzający wygasł. Poproś o nowy."), "danger")
            session.pop('delete_code', None)
            session.pop('delete_code_timestamp', None)
            return redirect(url_for('delete_account'))

        # Sprawdzenie hasła i kodu
        if check_password_hash(current_user.password_hash, form.password.data) and \
           session.get('delete_code') == form.confirmation_code.data:
            
            user_to_delete = User.query.get(current_user.id)
            
            logout_user()
            
            Post.query.filter_by(author=user_to_delete).delete()
            TournamentRegistration.query.filter_by(player=user_to_delete).delete()
            TournamentWinner.query.filter_by(user_id=user_to_delete.id).delete()

            db.session.delete(user_to_delete)
            db.session.commit()
            
            flash(_("Twoje konto zostało trwale usunięte."), "success")
            return redirect(url_for('index'))
        else:
            flash(_("Nieprawidłowe hasło lub kod potwierdzający."), "danger")
    
    return render_template('delete_account.html', title=_("Usuń Konto"), form=form)


@app.route("/tournaments")
def tournaments():
    page = request.args.get("page", 1, type=int)
    today = datetime.utcnow().date()

    # ZMIANA: Pobieramy wszystkie nadchodzące turnieje do jednej, wspólnej listy.
    upcoming_tournaments = (
        Tournament.query.filter(Tournament.start_date >= today)
        .order_by(Tournament.start_date.asc())
        .all()
    )

    # Przeszłe turnieje z paginacją (bez zmian)
    past_tournaments = (
        Tournament.query.filter(Tournament.start_date < today)
        .order_by(Tournament.start_date.desc())
        .paginate(page=page, per_page=app.config["POSTS_PER_PAGE"])
    )

    return render_template(
        "tournaments.html",
        title=_("Turnieje"),
        upcoming_tournaments=upcoming_tournaments,
        past_tournaments=past_tournaments,
        asc=asc,
    )


@app.route("/tournament/<int:tournament_id>")
def tournament_details(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    registrations = tournament.registrations.all()
    return render_template(
        "tournament_details.html",
        title=tournament.title,
        tournament=tournament,
        registrations=registrations,
        datetime=datetime.utcnow(),
        asc=asc,
    )


@app.route("/tournament/<int:tournament_id>/register", methods=["POST"])
@login_required
def register_for_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.start_date < datetime.utcnow():
        flash(_("Nie można zapisać się na turniej, który już się rozpoczął."), "danger")
        return redirect(url_for("tournament_details", tournament_id=tournament.id))

    if tournament.registrations.count() >= tournament.max_players:
        flash(_("Lista uczestników jest już pełna!"), "danger")
        return redirect(url_for("tournament_details", tournament_id=tournament.id))

    registration = TournamentRegistration(player=current_user, tournament=tournament)
    db.session.add(registration)
    db.session.commit()
    flash(_("Zostałeś pomyślnie zapisany na turniej!"), "success")
    return redirect(url_for("tournament_details", tournament_id=tournament.id))


@app.route("/tournament/<int:tournament_id>/unregister", methods=["POST"])
@login_required
def unregister_from_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.start_date < datetime.utcnow():
        flash(_("Nie można wypisać się z turnieju, który już się rozpoczął."), "danger")
        return redirect(url_for("tournament_details", tournament_id=tournament.id))

    registration = TournamentRegistration.query.filter_by(
        user_id=current_user.id, tournament_id=tournament_id
    ).first_or_404()
    db.session.delete(registration)
    db.session.commit()
    flash(_("Zostałeś wypisany z turnieju."), "success")
    return redirect(url_for("tournament_details", tournament_id=tournament.id))


@app.errorhandler(404)
def error_404(error):
    return render_template("errors/404.html", title=_("Nie znaleziono strony")), 404


@app.errorhandler(403)
def error_403(error):
    return render_template("errors/403.html", title=_("Brak dostępu")), 403


@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    user_count = User.query.count()
    post_count = Post.query.count()
    tournament_count = Tournament.query.count()
    return render_template(
        "admin/dashboard.html",
        title=_("Panel Administratora"),
        user_count=user_count,
        post_count=post_count,
        tournament_count=tournament_count,
    )


@app.route("/admin/users")
@login_required
@admin_required
def admin_manage_users():
    users = User.query.order_by(User.is_admin.desc(), User.id).all()
    delete_form = DeleteForm()
    return render_template(
        "admin/manage_users.html",
        title=_("Zarządzaj Użytkownikami"),
        users=users,
        delete_form=delete_form,
    )


@app.route("/admin/user/<int:user_id>/toggle_admin_confirm", methods=["GET", "POST"])
@login_required
@admin_required
def admin_toggle_admin_confirm(user_id):
    user_to_modify = User.query.get_or_404(user_id)
    if user_to_modify.id == current_user.id:
        flash(_("Nie możesz zmieniać własnych uprawnień w ten sposób."), "danger")
        return redirect(url_for("admin_manage_users"))

    form = ConfirmPasswordForm()
    action = _("nadania") if not user_to_modify.is_admin else _("odebrania")

    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.password.data):
            user_to_modify.is_admin = not user_to_modify.is_admin
            db.session.commit()
            status = _("nadano") if user_to_modify.is_admin else _("odebrano")
            flash(
                _(
                    "Pomyślnie %(status)s uprawnienia administratora użytkownikowi %(username)s.",
                    status=status,
                    username=user_to_modify.username,
                ),
                "success",
            )
            return redirect(url_for("admin_manage_users"))
        else:
            flash(_("Nieprawidłowe hasło. Operacja anulowana."), "danger")
            return redirect(url_for("admin_manage_users"))

    return render_template(
        "admin/confirm_admin_toggle.html",
        title=_("Potwierdź operację"),
        form=form,
        user_to_modify=user_to_modify,
        action=action,
    )


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    form = DeleteForm()
    user_to_delete = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        if user_to_delete.id == current_user.id:
            flash(
                _("Nie możesz usunąć własnego konta z panelu administratora."), "danger"
            )
            return redirect(url_for("admin_manage_users"))
        Post.query.filter_by(author=user_to_delete).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(
            _(
                "Użytkownik %(username)s i wszystkie jego posty zostały usunięte.",
                username=user_to_delete.username,
            ),
            "success",
        )
    else:
        flash(_("Nieprawidłowy formularz usuwania."), "danger")
    return redirect(url_for("admin_manage_users"))


@app.route("/admin/posts")
@login_required
@admin_required
def admin_manage_posts():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    delete_form = DeleteForm()
    return render_template(
        "admin/manage_posts.html",
        title=_("Zarządzaj Postami"),
        posts=posts,
        delete_form=delete_form,
    )


@app.route("/admin/post/<int:post_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_post(post_id):
    form = DeleteForm()
    from app.models import Post

    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        db.session.delete(post)
        db.session.commit()
        flash(_("Post został usunięty."), "success")
    else:
        flash(_("Nieprawidłowy formularz usuwania."), "danger")
    return redirect(url_for("admin_manage_posts"))


@app.route("/admin/tournament/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        banner_filename = "default.png"
        if form.banner_image.data:
            saved_filename = save_picture(form.banner_image.data)
            if saved_filename:
                banner_filename = saved_filename
            else:
                flash(
                    _(
                        "Przesłany plik nie jest prawidłowym obrazem (dozwolone formaty: JPG, PNG)."
                    ),
                    "danger",
                )
                return render_template(
                    "create_tournament.html", title=_("Nowy Turniej"), form=form
                )

        tournament = Tournament(
            title=form.title.data,
            description=form.description.data,
            banner_image=banner_filename,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            max_players=form.max_players.data,
        )
        db.session.add(tournament)
        db.session.commit()
        flash(_("Turniej został pomyślnie utworzony!"), "success")
        return redirect(url_for("tournaments"))
    return render_template("create_tournament.html", title=_("Nowy Turniej"), form=form)


@app.route(
    "/admin/tournament/<int:tournament_id>/delete_registration/<int:user_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_registration(tournament_id, user_id):
    registration = TournamentRegistration.query.filter_by(
        user_id=user_id, tournament_id=tournament_id
    ).first_or_404()
    db.session.delete(registration)
    db.session.commit()
    flash(_("Zapis użytkownika został usunięty."), "success")
    return redirect(url_for("tournament_details", tournament_id=tournament_id))


@app.route("/tournament/<int:tournament_id>/registrations.json")
@login_required
@admin_required
def tournament_registrations_json(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    registrations = []
    for reg in tournament.registrations:
        registrations.append(
            {
                "username": reg.player.username,
                "first_name": reg.player.first_name,
                "last_name": reg.player.last_name,
                "tournament_id": tournament.id,
                "tournament_title": tournament.title,
                "tournament_start_date": tournament.start_date.strftime("%Y-%m-%d"),
                "registration_date": reg.registration_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "paid": False,
            }
        )
    json_data = json.dumps(registrations, ensure_ascii=False, indent=2)
    filename = f"tournament_{tournament.id}_registrations.json"
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route("/admin/tournaments")
@login_required
@admin_required
def admin_manage_tournaments():
    tournaments = Tournament.query.order_by(Tournament.start_date.desc()).all()
    delete_form = DeleteForm()
    return render_template(
        "admin/manage_tournaments.html",
        title=_("Zarządzaj Turniejami"),
        tournaments=tournaments,
        delete_form=delete_form,
    )


@app.route("/admin/tournament/<int:tournament_id>/update", methods=["GET", "POST"])
@login_required
@admin_required
def admin_update_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    form = TournamentForm()
    if form.validate_on_submit():
        if form.banner_image.data:
            saved_filename = save_picture(form.banner_image.data)
            if saved_filename:
                tournament.banner_image = saved_filename
            else:
                flash(
                    _(
                        "Przesłany plik nie jest prawidłowym obrazem (dozwolone formaty: JPG, PNG)."
                    ),
                    "danger",
                )
                return render_template(
                    "create_tournament.html", title=_("Edytuj Turniej"), form=form
                )

        tournament.title = form.title.data
        tournament.description = form.description.data
        tournament.location = form.location.data
        tournament.start_date = form.start_date.data
        tournament.end_date = form.end_date.data
        tournament.max_players = form.max_players.data
        db.session.commit()
        flash(_("Turniej został zaktualizowany!"), "success")
        return redirect(url_for("admin_manage_tournaments"))
    elif request.method == "GET":
        form.title.data = tournament.title
        form.description.data = tournament.description
        form.location.data = tournament.location
        form.start_date.data = tournament.start_date
        form.end_date.data = tournament.end_date
        form.max_players.data = tournament.max_players
    return render_template(
        "create_tournament.html", title=_("Edytuj Turniej"), form=form
    )


@app.route("/admin/tournament/<int:tournament_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_tournament(tournament_id):
    form = DeleteForm()
    if form.validate_on_submit():
        tournament = Tournament.query.get_or_404(tournament_id)
        db.session.delete(tournament)
        db.session.commit()
        flash(_("Turniej został usunięty."), "success")
    else:
        flash(_("Nieprawidłowy formularz usuwania."), "danger")
    return redirect(url_for("admin_manage_tournaments"))


@app.route(
    "/admin/tournament/<int:tournament_id>/manage_winners", methods=["GET", "POST"]
)
@login_required
@admin_required
def admin_manage_winners(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    form = AddWinnerForm()

    if form.validate_on_submit():
        winner = TournamentWinner(
            placing=form.placing.data,
            user_id=form.user.data.id,
            tournament_id=tournament.id,
        )
        db.session.add(winner)
        db.session.commit()
        flash(_("Zwycięzca został dodany!"), "success")
        return redirect(url_for("admin_manage_winners", tournament_id=tournament.id))

    winners = tournament.winners.order_by(TournamentWinner.placing.asc()).all()
    return render_template(
        "admin/manage_winners.html",
        title=_("Zarządzaj Zwycięzcami"),
        form=form,
        tournament=tournament,
        winners=winners,
    )


@app.route("/admin/winner/<int:winner_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_winner(winner_id):
    winner = TournamentWinner.query.get_or_404(winner_id)
    tournament_id = winner.tournament_id
    db.session.delete(winner)
    db.session.commit()
    flash(_("Wpis o zwycięzcy został usunięty."), "success")
    return redirect(url_for("admin_manage_winners", tournament_id=tournament_id))
