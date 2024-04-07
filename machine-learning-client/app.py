"""
detect motion using a camera and OpenCV, and log the motion events into a MongoDB database.
"""

import os
import datetime
import cv2
from pymongo import MongoClient

# Constantspip show opencv-pytho should be named in uppercase
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "SmartHomeSecurity"
EVENTS_COLLECTION = "events"

# Setup MongoDB connection
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client[DATABASE_NAME]
events_collection = db[EVENTS_COLLECTION]

# Initialize camera
cap = cv2.VideoCapture(0)

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
        cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame1, f"Status: {'Movement'}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 3)
    
    if MOTION_DETECTED:  # Changed to uppercase
        # Log the event to MongoDB
        event = {
            "type": "motion_detected",
            "timestamp": datetime.datetime.utcnow()
        }
        events_collection.insert_one(event)

    cv2.imshow("feed", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(40) == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
