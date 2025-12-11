from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from ..extensions import db, bcrypt
from ..models import User
from .forms import RegisterForm, LoginForm
from ..crypto_utils import generate_rsa_keypair

auth_bp = Blueprint("auth", __name__)

# ========== HTML VIEWS ==========

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        team_name = form.team_name.data.strip()

        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email is already registered. Please login instead.", "warning")
            return redirect(url_for("auth.login"))

        # Hash password with bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        # Generate RSA keypair for this user
        public_pem, private_pem = generate_rsa_keypair(bits=2048)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            public_key=public_pem,
            private_key=private_pem,
            team_name=team_name,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. You can now login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=form.remember.data)
            flash("Login successful. Welcome back.", "success")

            next_page = request.args.get("next")
            return redirect(next_page or url_for("files.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ========== API ENDPOINTS (JSON) ==========

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    """
    JSON body:
    {
      "email": "...",
      "password": "...",
      "team_name": "RedTeam"
    }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    team_name = (data.get("team_name") or "").strip()

    if not email or not password or not team_name:
        return jsonify({"error": "Email, password, and team_name are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already registered."}), 400

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    public_pem, private_pem = generate_rsa_keypair(bits=2048)

    user = User(
        email=email,
        password_hash=password_hash,
        public_key=public_pem,
        private_key=private_pem,
        team_name=team_name,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully."}), 201


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """
    JSON body:
    {
      "email": "...",
      "password": "..."
    }
    Uses Flask-Login session cookies (not JWT) for simplicity.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({"message": "Login successful."}), 200

    return jsonify({"error": "Invalid credentials."}), 401
