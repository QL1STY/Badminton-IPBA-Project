# app/models.py

from datetime import datetime, timedelta
from app import db, login_manager, s
from flask_login import UserMixin
from itsdangerous import SignatureExpired, BadTimeSignature

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    username_last_changed = db.Column(db.DateTime, nullable=True)
    
    # Nowa relacja do zapisów na turnieje
    registrations = db.relationship('TournamentRegistration', backref='player', lazy='dynamic', cascade="all, delete-orphan")

    def generate_token(self, salt):
        return s.dumps(self.email, salt=salt)

    @staticmethod
    def verify_token(token, salt, expiration=3600):
        try:
            email = s.loads(token, salt=salt, max_age=expiration)
        except (SignatureExpired, BadTimeSignature):
            return None
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def can_change_username(self):
        if not self.username_last_changed:
            return True
        next_change_date = self.username_last_changed + timedelta(days=14)
        return datetime.utcnow() >= next_change_date

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

# --- NOWE MODELE DLA TURNIEJÓW ---

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    banner_image = db.Column(db.String(20), nullable=False, default='default.png')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    max_players = db.Column(db.Integer, nullable=False)
    # NOWE POLE: Lokalizacja
    location = db.Column(db.String(100), nullable=True)
    
    registrations = db.relationship('TournamentRegistration', backref='tournament', lazy='dynamic', cascade="all, delete-orphan")
    # NOWA RELACJA: Zwycięzcy
    winners = db.relationship('TournamentWinner', backref='tournament', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"Tournament('{self.title}', '{self.start_date}')"

class TournamentRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Registration('{self.player.username}' to '{self.tournament.title}')"
    
class TournamentWinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placing = db.Column(db.Integer, nullable=False)  # 1 dla 1. miejsca, 2 dla 2., itd.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    
    user = db.relationship('User')

    def __repr__(self):
        return f"Winner(Place: {self.placing}, User: '{self.user.username}', Tournament: '{self.tournament.title}')"
