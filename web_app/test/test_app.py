import unittest
from unittest.mock import patch, MagicMock, ANY
import sys
import os

# Adjust the Python path to include the directory above 'test' so it can find 'app.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_testing import TestCase
from werkzeug.security import generate_password_hash
from app import app, bcrypt, create_admin_user, login, register, delete_user

class Test(TestCase):
    def create_app(self):
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        # Setup for each test
        self.db_patch = patch('pymongo.MongoClient')
        self.s3_patch = patch('boto3.client')
        self.deepface_patch = patch('deepface.DeepFace.verify', return_value={'verified': True})

        # Start patches
        self.mock_db = self.db_patch.start()
        self.mock_s3 = self.s3_patch.start()
        self.mock_deepface = self.deepface_patch.start()

        # Mock behaviors
        self.mock_db_client = MagicMock()
        self.mock_db.return_value = self.mock_db_client
        self.mock_db_client.__getitem__.return_value = MagicMock()
        self.mock_s3_client = MagicMock()
        self.mock_s3.return_value = self.mock_s3_client

    def tearDown(self):
        # Stop all patches
        patch.stopall()


    def test_user_login(self):
        # Assuming the user needs to be set up first
        self.mock_db_client['SmartHomeSecurity']['users'].find_one.return_value = {
            'username': 'testuser',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8')
        }
        with self.client:
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_user_registration(self):
        # Assuming no user exists initially
        self.mock_db_client['SmartHomeSecurity']['users'].find_one.return_value = None
        with self.client:
            response = self.client.post('/register', data={
                'username': 'testuser',
                'password': 'password123',
                'admin': False
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_delete_user(self):
        # Setup admin context if needed
        with self.client:
            response = self.client.post('/delete_user/user_id', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
