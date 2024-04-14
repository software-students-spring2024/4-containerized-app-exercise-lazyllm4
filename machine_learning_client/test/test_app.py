""" Module for testing app.py in the machine_learning_client folder. """

import pytest
from unittest.mock import patch, MagicMock
from machine_learning_client.app import init_db, detect_motion, perform_facial_recognition

class Tests:
    """ Class for testing the functionalities in app.py """

    def test_sanity_check(self):
        """ Sanity check to ensure testing framework functions correctly. """
        assert True  # Basic test to check the setup

    @patch('machine_learning_client.app.MongoClient')
    def test_init_db(self, mock_mongo_client):
        """ Test the initialization of the database connection. """
        mock_mongo_client.return_value.__getitem__.return_value = MagicMock()
        db = init_db()
        assert db is not None, "Database initialization failed."

    @patch('machine_learning_client.app.cv2.VideoCapture')
    def test_detect_motion(self, mock_video_capture):
        """ Test motion detection functionality. """
        mock_video_capture.return_value.read.return_value = (True, MagicMock())
        motion_detected = detect_motion(mock_video_capture.return_value)
        assert motion_detected is not None, "Motion detection failed."

    @patch('machine_learning_client.app.DeepFace.verify')
    def test_perform_facial_recognition(self, mock_deepface):
        """ Test facial recognition functionality. """
        mock_deepface.return_value = {'verified': True}
        recognition_result = perform_facial_recognition('image_path', 'user_collection')
        assert recognition_result == True, "Facial recognition failed or not verified."


