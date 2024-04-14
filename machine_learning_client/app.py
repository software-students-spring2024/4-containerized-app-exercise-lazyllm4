"""Detect motion using a camera and OpenCV, and facial recognition and log the motion events into a MongoDB database."""

import os
import datetime
from time import sleep
import cv2
from pymongo import MongoClient
import socket
from dotenv import load_dotenv
# from deepface import DeepFace

# MONGO_URI = os.getenv("MONGO_URI")
# Load environmental variables from .env file
load_dotenv()
# Now you can access the environmental variables using os.getenv()
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "Motion-Detector"
EVENTS_COLLECTION = "events"
USERS_COLLECTION = "users" 
CAMERA_INDEX = 0


# Setup MongoDB connection
def init_db():
    print(MONGO_URI)
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client[DATABASE_NAME]

# Assume that sensor_details is a dictionary with sensor info
sensor_details = {
    "camera_index": CAMERA_INDEX,
    "camera_location": "Laptop",
}

# # Capture motion detection event
# def detect_motion(cap, db):
#     events_collection = db[EVENTS_COLLECTION]
#     motion_detected = False
#     analysis_results = {}
#     # Grab a few frames from the camera to allow it to adjust to brightness
#     for _ in range(5):
#         cap.read()
#     # Now read the first frame to compare against
#     ret, frame1 = cap.read()
#     for _ in range(10):  # Check 10 frames for motion
#         ret, frame2 = cap.read()
#         if not ret:
#             break
#         # Calculate the absolute difference between frames
#         diff = cv2.absdiff(frame1, frame2)
#         gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
#         blur = cv2.GaussianBlur(gray, (5, 5), 0)
#         _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
#         dilated = cv2.dilate(thresh, None, iterations=2)
#         contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         # Iterate over all contours found and see if any are of significant size
#         for contour in contours:
#             if cv2.contourArea(contour) > 500:
#                 motion_detected = True
#                 analysis_results = {
#                     "contour_area": cv2.contourArea(contour),
#                     "contour_location": cv2.boundingRect(contour),
#                 }
#                 # Optionally log the event to the database
#                 log_event(events_collection, 'MOTION_DETECTED', analysis_results, sensor_details)
#                 break  # Exit if motion is detected
#         if motion_detected:
#             # Capture the frame that caused motion detection
#             _, detected_frame = cap.read()
#             cv2.imwrite('detected_frame.jpg', detected_frame)

#             # Perform facial recognition
#             recognition_results = perform_facial_recognition('detected_frame.jpg', db[USERS_COLLECTION])

#             # Log the motion detection event along with recognition results
#             log_event(events_collection, 'MOTION_DETECTED', analysis_results, sensor_details, recognition_results)

#             break  # Exit if motion is detected

#         frame1 = frame2  # Update frame1 to the new latest frame

#     return motion_detected, analysis_results, recognition_results


def detect_motion(cap, db):
    events_collection = db[EVENTS_COLLECTION]
    motion_detected = False
    analysis_results = {}
    for _ in range(5):
        cap.read()  # Allow camera to adjust
    ret, frame1 = cap.read()
    if not ret:
        return False, {"error": "Camera read error"}, None  # Early exit if camera fails

    for _ in range(20):
        ret, frame2 = cap.read()
        if not ret:
            break
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 500:
                motion_detected = True
                analysis_results = {
                    "contour_area": cv2.contourArea(contour),
                    "contour_location": cv2.boundingRect(contour),
                }
                log_event(events_collection, 'MOTION_DETECTED', analysis_results, sensor_details)
                _, detected_frame = cap.read()
                cv2.imwrite('detected_frame.jpg', detected_frame)
                recognition_results = True
                # recognition_results = perform_facial_recognition('detected_frame.jpg', db[USERS_COLLECTION])
                log_event(events_collection, 'MOTION_DETECTED', analysis_results, sensor_details, recognition_results)
                return True, analysis_results, recognition_results

        frame1 = frame2  # Update the reference frame

    if not motion_detected:
        log_event(events_collection, 'NO_MOTION_DETECTED', {}, sensor_details, False)
        return False, {"message": "No significant motion detected"}, None

    return False, {"error": "Uncertain if motion occurred"}, None



# def register_user(db, username, photo_path):
#     users_collection = db[USERS_COLLECTION]
#     user_data = {
#         "username": username,
#         "photo_path": photo_path,  # Store path to user's photo
#         "registered_on": datetime.datetime.utcnow(),
#     }
#     users_collection.insert_one(user_data)

# def authenticate_user(db, photo_path):
#     """Authenticate user by comparing a captured photo with registered user's photos."""
#     users_collection = db[USERS_COLLECTION]
#     result = {"success": False, "username": None}
    
#     for user in users_collection.find():
#         verification_result = DeepFace.verify(img1_path=photo_path, img2_path=user["photo_path"])
#         if verification_result["verified"]:
#             result = {"success": True, "username": user["username"]}
#             break  # User verified

#     return result


# Perform facial recognition
def perform_facial_recognition(captured_image_path, users_collection):
    for user in users_collection.find():
        user_photo_path = user.get("photo_path")
        if user_photo_path:
            # You might need to adjust this code if photo_path is a URL or requires additional handling
            try:
                result = DeepFace.verify(captured_image_path, user_photo_path, enforce_detection=False)
                if result["verified"]:
                    # If a user is recognized, return the result
                    return True
            except Exception as e:
                print(f"Error during facial recognition for {user['username']}: {e}")
    return False

# Log events to MongoDB
def log_event(collection, event_type, analysis_results, sensor_details, recognition_results=False):
    event = {
        "type": event_type,
        "timestamp": datetime.datetime.utcnow(),
        "machine_name": socket.gethostname(),
        "analysis_results": analysis_results,
        "sensor_details": sensor_details,
        "recognition_results": recognition_results,
    }
    print(event)
    collection.insert_one(event)


# Check if this script is being run directly
if __name__ == "__main__":
    db = init_db()
    cap = cv2.VideoCapture(CAMERA_INDEX)
    # find and load camera
    while True:
        try:
            detect_motion(cap, db)
            sleep(1)
        except KeyboardInterrupt:
            cap.release()
            cv2.destroyAllWindows()
            exit(0)
