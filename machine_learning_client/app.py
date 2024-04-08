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
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    while cap.isOpened():
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        MOTION_DETECTED = False  # Changed to uppercase

        for contour in contours:
            if cv2.contourArea(contour) < 900:
                continue
            MOTION_DETECTED = True  # Changed to uppercase
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame1,
                f"Status: {'Movement'}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3,
            )

        if MOTION_DETECTED:  # Changed to uppercase
            log_event(events_collection, "MOTION_DETECTED")

        frame1 = frame2
        ret, frame2 = cap.read()

        if cv2.waitKey(40) == 27:
            break


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
