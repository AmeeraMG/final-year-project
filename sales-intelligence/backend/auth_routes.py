"""
auth_routes.py
──────────────
Flask routes for user registration and login.
User data is stored in a simple JSON file (college project).
"""

from flask import Blueprint, request, jsonify, session
import json
import os
import re
import hashlib

auth_bp = Blueprint("auth", __name__)

# Simple file-based storage for college project
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash for password storage"""
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_phone(phone: str) -> bool:
    """Validate Indian phone number format +91XXXXXXXXXX"""
    pattern = r"^\+91[6-9]\d{9}$"
    return bool(re.match(pattern, phone))


# ── POST /register ────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Check all required fields are present
    required_fields = ["name", "phone", "email", "password", "shop_name", "location"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "message": f"Field '{field}' is required."}), 400

    phone = data["phone"].strip()
    email = data["email"].strip()
    name  = data["name"].strip()

    # Validate phone number format
    if not _validate_phone(phone):
        return jsonify({
            "success": False,
            "message": "Please enter a valid Indian phone number starting with +91"
        }), 400

    # Simple email format check
    if "@" not in email or "." not in email:
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    users = _load_users()

    # Check if phone number already registered
    if phone in users:
        return jsonify({"success": False, "message": "This phone number is already registered."}), 409

    # Save new user
    users[phone] = {
        "name"      : name,
        "phone"     : phone,
        "email"     : email,
        "password"  : _hash_password(data["password"]),
        "shop_name" : data["shop_name"].strip(),
        "location"  : data["location"].strip(),
    }
    _save_users(users)

    return jsonify({"success": True, "message": "Account created successfully! Please login."}), 201


# ── POST /login ───────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    phone    = data.get("phone", "").strip()
    password = data.get("password", "")

    # Validate phone format
    if not _validate_phone(phone):
        return jsonify({
            "success": False,
            "message": "Please enter a valid Indian phone number starting with +91"
        }), 400

    users = _load_users()

    # Check if user exists
    if phone not in users:
        return jsonify({"success": False, "message": "Phone number not registered."}), 404

    user = users[phone]

    # Verify password
    if user["password"] != _hash_password(password):
        return jsonify({"success": False, "message": "Incorrect password."}), 401

    # Store user info in session
    session["phone"]     = phone
    session["name"]      = user["name"]
    session["shop_name"] = user["shop_name"]
    session["logged_in"] = True

    return jsonify({
        "success"  : True,
        "message"  : "Login successful!",
        "user": {
            "name"      : user["name"],
            "phone"     : user["phone"],
            "email"     : user["email"],
            "shop_name" : user["shop_name"],
            "location"  : user["location"],
        }
    }), 200


# ── GET /profile ──────────────────────────────────────────────────────────────

@auth_bp.route("/profile", methods=["GET"])
def profile():
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Please login first."}), 401

    phone = session.get("phone")
    users = _load_users()

    if phone not in users:
        return jsonify({"success": False, "message": "User not found."}), 404

    user = users[phone]
    # Return profile without password
    return jsonify({
        "success": True,
        "user": {
            "name"      : user["name"],
            "phone"     : user["phone"],
            "email"     : user["email"],
            "shop_name" : user["shop_name"],
            "location"  : user["location"],
        }
    }), 200


# ── POST /logout ──────────────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."}), 200
