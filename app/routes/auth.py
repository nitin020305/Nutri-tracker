from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.user import User
from datetime import timedelta
import re

auth_bp = Blueprint("auth", __name__)

# Simple email validator
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# ── REGISTER ─────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Step 1: Create account with email + password only.
    Profile details (height, weight, goal …) are saved separately via PUT /api/user/profile.

    Body: { email, password, name }
    """
    data = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name     = (data.get("name") or "").strip()

    # Validation
    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "Valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id),
                                        expires_delta=timedelta(days=7))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Account created successfully",
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          user.to_dict(),
        "profile_complete": user.profile_complete,
    }), 201


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Body: { email, password }
    Returns JWT access + refresh tokens.
    """
    data     = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token  = create_access_token(identity=str(user.id),
                                        expires_delta=timedelta(days=7))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":          "Login successful",
        "access_token":     access_token,
        "refresh_token":    refresh_token,
        "user":             user.to_dict(),
        "profile_complete": user.profile_complete,
    })


# ── REFRESH TOKEN ─────────────────────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Use refresh token to get a new access token."""
    uid          = get_jwt_identity()
    access_token = create_access_token(identity=uid, expires_delta=timedelta(days=7))
    return jsonify({"access_token": access_token})


# ── ME (current user) ─────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return current authenticated user's profile."""
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    from app.services.prediction import calculate_bmr, calculate_tdee, get_calorie_target
    stats = {}
    if user.profile_complete:
        bmr  = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
        tdee = calculate_tdee(bmr, user.activity_level)
        stats = {
            "bmr":            round(bmr, 1),
            "tdee":           round(tdee, 1),
            "calorie_target": round(get_calorie_target(tdee, user.goal), 1),
        }
    return jsonify({"user": user.to_dict(), "stats": stats})


# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Body: { current_password, new_password }"""
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    data = request.get_json() or {}

    if not user.check_password(data.get("current_password", "")):
        return jsonify({"error": "Current password is incorrect"}), 401
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"})


# ── DELETE ACCOUNT ────────────────────────────────────────────────────────────
@auth_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """Permanently delete account and all food logs."""
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account deleted"})
