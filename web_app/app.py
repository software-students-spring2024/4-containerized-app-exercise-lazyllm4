"""Main module for the Flask web application."""

# pylint: disable=import-error
import os
import sys
from pathlib import Path
import datetime
import cv2
# pylint: disable=import-error
from dotenv import load_dotenv
from bson.objectid import ObjectId
from bson.binary import Binary
from pymongo import MongoClient
import base64
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
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
import boto3
from deepface import DeepFace
from dotenv import load_dotenv
import time
# Modifying the system path to ensure imports are found
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_STORAGE_PATH = os.path.join(BASE_DIR, 'user_images')

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
db2 = client["Motion-Detector"]
users_collection = db["users"]

# AWS S3 setup
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# S3 bucket name
BUCKET_NAME = 'lazyllm4'


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


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
# def dashboard():
#     """Render dashboard page for logged-in users."""
#     users_list = None
#     if current_user.is_admin:
#         users_list = users_collection.find()
#     return render_template(
#         "dashboard.html", username=current_user.username, users_list=users_list
#     )
def dashboard():
    users_list = None
    if current_user.is_admin:
        users_list = users_collection.find()
    return render_template("dashboard.html", username=current_user.username, users_list=users_list)



@app.route("/start-motion-detection", methods=["POST"])
def start_motion_detection():
    """Starts motion detection and returns the detection result."""



    cap = cv2.VideoCapture(0)
    try:
        motion_detected, analysis_results, _ = detect_motion(cap, db)
    finally:
        cap.release()
    return jsonify({"motion_detected": motion_detected, "analysis_results": analysis_results})

def detection_r():
    events_collection = db2.events
    
    # Fetch recent documents
    documents = events_collection.find({"type": "MOTION_DETECTED"}).sort("timestamp", -1).limit(5)
    # Check if any document has recognition_results as True
    current_time = datetime.datetime.now()
    for document in documents:
        document_time = document['timestamp']
        time_difference = current_time - document_time
        if time_difference.total_seconds() < 10:
            return True
    return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Find user in the database
        user = users_collection.find_one({"username": username})

        # Check if the user was found
        if not user:
            flash("No account found with this username.", "error")
            return redirect(url_for("login"))

        # Verify password
        if not bcrypt.check_password_hash(user.get("password", ""), password):
            #flash("Password is incorrect.", "error")
            return redirect(url_for("login"), message = "Password is incorrect.")
        cap = cv2.VideoCapture(0)
        detect_motion(cap,db)
        if detection_r():
            print("Motion detected")
            flash("Motion Detected")
        else:
            flash("No motion detected. Please ensure your presence in front of the camera.", "error")
            return redirect(url_for("login"))
        # # Perform motion detection
        # motion_response = start_motion_detection()
        # motion_data = motion_response.get_json()

        # # Check motion detection result
        # if not motion_data["motion_detected"]:
        #     flash("No motion detected. Please ensure your presence in front of the camera.", "error")
        #     return redirect(url_for("login"))
        # else : 
        #     print("Motion detecteddd")
        #     flash("Motion Detected")

         
    


        # If the user is an admin, bypass photo verification and log them in
        if user.get("is_admin"):
            user_obj = User(str(user["_id"]), user["username"], user.get("is_admin"))
            login_user(user_obj)
            flash("Admin login successful.")
            return redirect(url_for("dashboard"))

        # For non-admin users, perform facial recognition
        photo_data = request.form.get("photo")
        if photo_data:
            # Decode the photo data from Base64
            header, encoded = photo_data.split(",", 1)
            photo_binary = base64.b64decode(encoded)
            image = Image.open(BytesIO(photo_binary))

            # Save the photo temporarily for comparison
            temp_photo_path = os.path.join("/tmp", secure_filename(f"login_attempt_{username}.jpg"))
            image.save(temp_photo_path)

            # Fetch the stored reference photo path
            db_photo_path = user.get("photo_path")
            if not db_photo_path:
                flash("Reference photo for facial recognition not found.", "error")
                return redirect(url_for("login"))

            # Perform facial recognition check
            try:
                verification_result = DeepFace.verify(temp_photo_path, db_photo_path, enforce_detection=False)
                os.remove(temp_photo_path)  # Clean up the temporary photo

                # Check the verification result
                if not verification_result["verified"]:
                    #flash("Facial recognition failed. Access denied.", "error")
                    return redirect(url_for("login"), message = "Facial recognition failed. Access denied.")

            except Exception as e:
                os.remove(temp_photo_path)  # Clean up the temporary photo
                flash(f"Facial recognition error: {str(e)}", "error")
                return redirect(url_for("login"))

            # If facial recognition passes, log in the user
            user_obj = User(str(user["_id"]), user["username"], user.get("is_admin", False))
            login_user(user_obj)
            flash("Login successful.")
            return redirect(url_for("dashboard"))

        else:
            flash("Photo capture is required for login.", "error")
            return redirect(url_for("login"))

    # Render the login template if the method is not POST
    return render_template("login.html")




@app.route("/logout")
@login_required
def logout():
    """Handle logout functionality."""
    logout_user()
    return redirect(url_for("home"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')  # Admin or User
        is_admin = True if role == 'admin' else False
        photo_data = request.form.get('photo')  # Optional, based on role
        print(request.form)


        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_document = {
            "username": username,
            "password": hashed_password,
            "is_admin": is_admin,
            "registered_on": datetime.datetime.utcnow()
        }


        # Debug: Print out what is received
        print(f"Received registration request for: {username}, Role: {role}, Is Admin: {is_admin}")

        if not is_admin:  # Handle photo for regular users only
            if photo_data:
                try:
                    header, encoded = photo_data.split(",", 1)
                    photo_binary = base64.b64decode(encoded)
                    image = Image.open(BytesIO(photo_binary))

                    buffer = BytesIO()
                    image.save(buffer, format="JPEG")
                    buffer.seek(0)
                    photo_filename = secure_filename(f"{username}_{datetime.datetime.utcnow().isoformat()}.jpg")
                    s3_client.upload_fileobj(
                        buffer,
                        BUCKET_NAME,
                        photo_filename,
                        ExtraArgs={
                            "ContentType": "image/jpeg",
                            "ACL": "public-read"
                        }
                    )
                    file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{photo_filename}"
                    user_document["photo_path"] = file_url
                except Exception as e:
                    flash(f'Error processing photo: {e}', 'error')
                    return render_template('register.html')
            else:
                flash('Photo capture is required for user registration.', 'error')
                return render_template('register.html')

        users_collection.insert_one(user_document)
        flash('Registration successful.')
        return redirect(url_for('login'))

    return render_template('register.html')

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
