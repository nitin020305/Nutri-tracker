from app import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile (filled after signup)
    name          = db.Column(db.String(100), nullable=True)
    age           = db.Column(db.Integer, nullable=True)
    gender        = db.Column(db.String(10), nullable=True)
    height_cm     = db.Column(db.Float, nullable=True)
    weight_kg     = db.Column(db.Float, nullable=True)
    activity_level= db.Column(db.String(20), default="moderate")

    goal              = db.Column(db.String(20), default="maintain")
    target_weight_kg  = db.Column(db.Float, nullable=True)
    target_days       = db.Column(db.Integer, nullable=True)
    profile_complete  = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    food_logs = db.relationship("FoodLog", backref="user", lazy=True, cascade="all, delete-orphan")

    # ── password helpers ──────────────────────────────────────────────────
    def set_password(self, plain: str):
        self.password_hash = bcrypt.hashpw(
            plain.encode(), bcrypt.gensalt()
        ).decode()

    def check_password(self, plain: str) -> bool:
        return bcrypt.checkpw(plain.encode(), self.password_hash.encode())

    def to_dict(self):
        return {
            "id":               self.id,
            "email":            self.email,
            "name":             self.name,
            "age":              self.age,
            "gender":           self.gender,
            "height_cm":        self.height_cm,
            "weight_kg":        self.weight_kg,
            "activity_level":   self.activity_level,
            "goal":             self.goal,
            "target_weight_kg": self.target_weight_kg,
            "target_days":      self.target_days,
            "profile_complete": self.profile_complete,
            "created_at":       self.created_at.isoformat(),
        }
