"""Main module for the Flask web application."""

# pylint: disable=import-error
import os
import sys
from pathlib import Path
import cv2
# pylint: disable=import-error
from dotenv import load_dotenv
from bson.objectid import ObjectId
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt

# Modifying the system path to ensure imports are found
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# pylint: disable=wrong-import-position,import-error
from machine_learning_client.app import detect_motion

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Setup Flask-Bcrypt
bcrypt = Bcrypt(app)

# MongoDB Atlas setup
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
db = client["SmartHomeSecurity"]
users_collection = db.users


def create_admin_user():
    """Ensure an admin user exists at startup."""
    admin_username = "admin"
    admin_password = "admin123"
    admin_exists = users_collection.find_one(
        {"username": admin_username, "is_admin": True}
    )

    if not admin_exists:
        hashed_password = bcrypt.generate_password_hash(admin_password).decode("utf-8")
        users_collection.insert_one(
            {"username": admin_username, "password": hashed_password, "is_admin": True}
        )
        print("Admin user created.")
    else:
        print("Admin user already exists.")


create_admin_user()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    """User class for Flask-Login integration."""

    def __init__(self, user_id, username, is_admin=False):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin

    @staticmethod
    def validate_login(password_hash, password):
        """Validate login credentials."""
        return bcrypt.check_password_hash(password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    return User(str(user["_id"]), user["username"], user.get("is_admin", False))


@app.route("/")
def home():
    """Render home page."""
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Render dashboard page for logged-in users."""
    users_list = None
    if current_user.is_admin:
        users_list = users_collection.find()
    return render_template(
        "dashboard.html", username=current_user.username, users_list=users_list
    )


@app.route("/start-motion-detection", methods=["POST"])
def start_motion_detection():
    """Starts motion detection and returns the detection result."""
    cap = cv2.VideoCapture(0)
    try:
        motion_detected, analysis_results = detect_motion(cap, db)
    finally:
        cap.release()
    return jsonify({"motion_detected": motion_detected, "analysis_results": analysis_results})


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate users and redirect to the dashboard."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_collection.find_one({"username": username})

        if user and User.validate_login(user["password"], password):
            user_obj = User(
                str(user["_id"]), user["username"], user.get("is_admin", False)
            )
            login_user(user_obj)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Handle logout functionality."""
    logout_user()
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    """Allow admin users to register new users."""
    if not current_user.is_admin:
        flash("Only admins can register new users.")
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one(
            {"username": username, "password": hashed_password, "is_admin": False}
        )

        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/delete_user/<user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    """Delete a user by ID."""
    if not current_user.is_admin:
        flash("Only admins can delete users.")
        return redirect(url_for("dashboard"))

    users_collection.delete_one({"_id": ObjectId(user_id)})
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
