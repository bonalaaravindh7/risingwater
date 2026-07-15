from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


def _utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Nullable: accounts created via Google sign-in have no local password.
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    predictions = db.relationship(
        "Prediction",
        backref="user",
        lazy="dynamic",
        order_by="Prediction.created_at.desc()",
        cascade="all, delete-orphan",
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Model inputs, kept exactly as submitted so history is a faithful record.
    temp = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    cloud_cover = db.Column(db.Float, nullable=False)
    annual = db.Column(db.Float, nullable=False)
    jan_feb = db.Column(db.Float, nullable=False)
    mar_may = db.Column(db.Float, nullable=False)
    jun_sep = db.Column(db.Float, nullable=False)
    oct_dec = db.Column(db.Float, nullable=False)
    avg_june = db.Column(db.Float, nullable=False)
    sub = db.Column(db.Float, nullable=False)

    # Model output.
    flood_predicted = db.Column(db.Boolean, nullable=False)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Prediction {self.id} user={self.user_id} flood={self.flood_predicted}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
