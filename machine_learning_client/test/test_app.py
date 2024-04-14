import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import cv2
import numpy as np
from pymongo import MongoClient
from deepface import DeepFace
from dotenv import load_dotenv
# Adjust the Python path to find the app module
current_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(current_directory) 
sys.path.insert(0, parent_directory)  # Adds it to sys.path
from app import init_db, detect_motion, perform_facial_recognition, log_event

load_dotenv()
# Now you can access the environmental variables using os.getenv()
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "Motion-Detector"
EVENTS_COLLECTION = "events"
USERS_COLLECTION = "users" 
CAMERA_INDEX = 0
class Test(unittest.TestCase):
    def setUp(self):
        # Setup for each test
        self.db_patch = patch('pymongo.MongoClient')
        self.cv2_patch = patch('cv2.VideoCapture')
        self.deepface_patch = patch('deepface.DeepFace.verify')

        # Start patches
        self.mock_db = self.db_patch.start()
        self.mock_cv2 = self.cv2_patch.start()
        self.mock_deepface = self.deepface_patch.start()

        # Mock behaviors
        self.mock_db.return_value.__getitem__.return_value = MagicMock()
        self.mock_cv2.return_value.isOpened.return_value = True
        self.mock_cv2.return_value.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))  # A dummy black image
        self.mock_deepface.return_value = {'verified': True}

    def tearDown(self):
        # Stop all patches
        patch.stopall()


    def test_detect_motion(self):
        # Mock setup
        db = MagicMock()
        cap = cv2.VideoCapture(0)
        detect_motion(cap, db)
        db[EVENTS_COLLECTION].insert_one.assert_called()

    def test_log_event(self):
        # Test event logging to MongoDB
        collection = MagicMock()
        log_event(collection, 'motion_detected', {}, {})
        collection.insert_one.assert_called()

if __name__ == '__main__':
    unittest.main()
