
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ---------------- USER TABLE ----------------

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # Hash and save password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Check entered password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------- QUIZ RESULT TABLE ----------------

class QuizResult(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    score = db.Column(
        db.Integer,
        nullable=False
    )

    total_questions = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
    db.DateTime,
    nullable=False,
    default=datetime.utcnow
)
