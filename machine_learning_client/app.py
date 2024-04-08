"""Detect motion using a camera and OpenCV, and log the motion events into a MongoDB database."""

import os
import datetime
import cv2
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "SmartHomeSecurity"
EVENTS_COLLECTION = "events"
CAMERA_INDEX = 0


# Setup MongoDB connection
def init_db():
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client[DATABASE_NAME]


# Capture motion detection event
def detect_motion(cap, db):
    events_collection = db[EVENTS_COLLECTION]
    motion_detected = False
    # Grab a few frames from the camera to allow it to adjust to brightness
    for _ in range(5):
        cap.read()
    # Now read the first frame to compare against
    ret, frame1 = cap.read()
    for _ in range(10):  # Check 10 frames for motion
        ret, frame2 = cap.read()
        if not ret:
            break
        # Calculate the absolute difference between frames
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Iterate over all contours found and see if any are of significant size
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                motion_detected = True
                # Optionally log the event to the database
                log_event(events_collection, 'MOTION_DETECTED')
                break  # Exit if motion is detected
        if motion_detected:
            break  # If motion is detected, no need to process further frames
        frame1 = frame2  # Update frame1 to the new latest frame
    return motion_detected


# Log events to MongoDB
def log_event(collection, event_type):
    event = {"type": event_type, "timestamp": datetime.datetime.utcnow()}
    collection.insert_one(event)


# Check if this script is being run directly
if __name__ == "__main__":
    db = init_db()
    cap = cv2.VideoCapture(CAMERA_INDEX)
    try:
        detect_motion(cap, db)
    finally:
        cap.release()
        cv2.destroyAllWindows()
