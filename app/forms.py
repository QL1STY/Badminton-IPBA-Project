# app/forms.py

import re
from flask_wtf import FlaskForm
# This line is updated to include all necessary fields
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_babel import lazy_gettext as _l
from flask_babel import gettext as _
from profanity_check import predict
from app.models import User
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
import bleach

# --- Helper Functions ---

def bleach_clean_text(data):
    if data is None:
        return None
    allowed_tags = ['br', 'p', 'b', 'i', 'u', 'strong', 'em', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    return bleach.clean(data, tags=allowed_tags, strip=True)

def get_users():
    """Funkcja pomocnicza do pobierania użytkowników do formularza."""
    return User.query

# --- Validators ---

def validate_username_profanity(form, field):
    username_text = field.data.lower()
    if predict([username_text])[0] == 1:
        raise ValidationError(_l('Nazwa użytkownika zawiera niedozwolone słowa.'))

def validate_password_strength(form, field):
    password = field.data
    errors = []
    if not (4 <= len(password) <= 24):
        errors.append(_l('Hasło musi mieć od 4 do 24 znaków.'))
    if not re.search(r'[a-z]', password):
        errors.append(_l('Musi zawierać małą literę.'))
    if not re.search(r'[A-Z]', password):
        errors.append(_l('Musi zawierać dużą literę.'))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append(_l('Musi zawierać znak specjalny.'))
    if errors:
        raise ValidationError(' '.join([str(error) for error in errors]))

# --- Form Classes ---

class AddWinnerForm(FlaskForm):
    """Formularz do dodawania zwycięzcy do turnieju."""
    placing = IntegerField(_l('Miejsce'), validators=[DataRequired()])
    # Używamy QuerySelectField, aby stworzyć listę rozwijaną z użytkownikami
    user = QuerySelectField(_l('Użytkownik'), query_factory=get_users, get_label='username', allow_blank=False)
    submit = SubmitField(_l('Dodaj zwycięzcę'))
    
class RegistrationForm(FlaskForm):
    first_name = StringField(_l('Imię'), filters=[bleach_clean_text], validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField(_l('Nazwisko'), filters=[bleach_clean_text], validators=[DataRequired(), Length(min=2, max=30)])
    username = StringField(_l('Nazwa użytkownika'),
                           filters=[bleach_clean_text],
                           validators=[DataRequired(), Length(min=2, max=20), validate_username_profanity])
    email = StringField(_l('Email'),
                        filters=[bleach_clean_text],
                        validators=[DataRequired(), Email(message=_l("Niepoprawny format adresu email."))])
    password = PasswordField(_l('Hasło'), validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(_l('Potwierdź hasło'),
                                     validators=[DataRequired(), EqualTo('password', message=_l('Hasła muszą być identyczne.') )])
    submit = SubmitField(_l('Zarejestruj się'))
    

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_l('Ta nazwa użytkownika jest już zajęta. Proszę wybrać inną.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_l('Ten adres email jest już zajęty. Proszę wybrać inny.'))

class LoginForm(FlaskForm):
    login_identifier = StringField(_l('Nazwa użytkownika lub Email'),
                                   validators=[DataRequired()])
    password = PasswordField(_l('Hasło'), validators=[DataRequired()])
    remember = BooleanField(_l('Zapamiętaj mnie'))
    submit = SubmitField(_l('Zaloguj się'))

class PostForm(FlaskForm):
    title = StringField(_l('Tytuł'), filters=[bleach_clean_text], validators=[DataRequired()])
    content = TextAreaField(_l('Treść'), filters=[bleach_clean_text], validators=[DataRequired()])
    picture = FileField(_l('Zdjęcie nagłówkowe (baner)'), validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField(_l('Opublikuj'))

class ContactForm(FlaskForm):
    name = StringField(_l('Twoje Imię'), filters=[bleach_clean_text], validators=[DataRequired()])
    email = StringField(_l('Twój Email'), filters=[bleach_clean_text], validators=[DataRequired(), Email()])
    subject = StringField(_l('Temat'), filters=[bleach_clean_text], validators=[DataRequired()])
    message = TextAreaField(_l('Wiadomość'), filters=[bleach_clean_text], validators=[DataRequired()])
    submit = SubmitField(_l('Wyślij'))

class RequestResetForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Poproś o reset hasła'))

    def validate_email(self, email):
        # This validation reveals whether an email is registered, which can be a security risk (user enumeration).
        # It's better to remove this validator and handle the logic in the view.
        # Always show a generic message like "If an account with this email exists, a password reset link has been sent."
        pass

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Nowe hasło'), validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(_l('Potwierdź nowe hasło'), validators=[DataRequired(), EqualTo('password', message=_l('Hasła muszą być identyczne.'))])
    submit = SubmitField(_l('Zresetuj hasło'))

class UpdateAccountForm(FlaskForm):
    first_name = StringField(_l('Imię'), 
                            validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField(_l('Nazwisko'), 
                            validators=[DataRequired(), Length(min=2, max=30)])
    username = StringField(_l('Nazwa użytkownika'),
                            validators=[DataRequired(), Length(min=2, max=20), validate_username_profanity])
    submit_details = SubmitField(_l('Zaktualizuj dane'))

    def __init__(self, original_username, *args, **kwargs):
        super(UpdateAccountForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            if User.query.filter_by(username=username.data).first():
                raise ValidationError(_l('Ta nazwa użytkownika jest już zajęta. Proszę wybrać inną.'))

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_l('Stare hasło'), validators=[DataRequired()])
    new_password = PasswordField(_l('Nowe hasło'), 
                                 validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(_l('Potwierdź nowe hasło'), 
                                     validators=[DataRequired(), EqualTo('new_password', message=_l('Hasła muszą być identyczne.'))])
    submit_password = SubmitField(_l('Zmień hasło'))

# --- FORMULARZ DLA TURNIEJÓW ---
class TournamentForm(FlaskForm):
    title = StringField(_l('Tytuł turnieju'), filters=[bleach_clean_text], validators=[DataRequired(), Length(max=120)])
    description = TextAreaField(_l('Opis turnieju'), filters=[bleach_clean_text], validators=[DataRequired()])
    banner_image = FileField(_l('Baner turnieju'), validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    location = StringField(_l('Lokalizacja'), filters=[bleach_clean_text], validators=[DataRequired(), Length(max=100)])
    start_date = DateField(_l('Data rozpoczęcia'), format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField(_l('Data zakończenia (opcjonalnie)'), format='%Y-%m-%d', validators=[DataRequired()])
    max_players = IntegerField(_l('Maksymalna liczba graczy'), validators=[DataRequired()])
    submit = SubmitField(_l('Zapisz turniej'))

class DeleteForm(FlaskForm):
    submit = SubmitField(_l('Usuń'))

class ConfirmPasswordForm(FlaskForm):
    password = PasswordField(_l('Hasło administratora'), validators=[DataRequired()])
    submit = SubmitField(_l('Potwierdź operację'))
    