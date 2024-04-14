
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_testing import TestCase
from werkzeug.security import generate_password_hash
from app import app, bcrypt, create_admin_user, login, register, delete_user

class Test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        # Setup for each test
        self.db_patch = patch('pymongo.MongoClient')
        self.s3_patch = patch('boto3.client')
        self.deepface_patch = patch('deepface.DeepFace.verify')

        # Start patches
        self.mock_db = self.db_patch.start()
        self.mock_s3 = self.s3_patch.start()
        self.mock_deepface = self.deepface_patch.start()

        # Mock behaviors
        self.mock_db.return_value.__getitem__.return_value = MagicMock()
        self.mock_s3.return_value.upload_fileobj = MagicMock()
        self.mock_deepface.return_value = {'verified': True}

    def tearDown(self):
        # Stop all patches
        patch.stopall()

    def test_create_admin_user(self):
        # Test ensuring admin user is created correctly
        with self.client:
            response = create_admin_user()
            self.mock_db['SmartHomeSecurity']['users'].insert_one.assert_called()

    def test_user_registration(self):
        # Test user registration flow
        with self.client:
            response = self.client.post('/register', data=dict(
                username='testuser',
                password='password123',
                admin=False
            ))
            self.assertEqual(response.status_code, 302)  # Assuming redirection after successful registration

    def test_user_login(self):
        # Test user login
        with self.client:
            response = self.client.post('/login', data=dict(
                username='testuser',
                password='password123'
            ))
            self.assertEqual(response.status_code, 200)

    def test_delete_user(self):
        # Test user deletion by admin
        with self.client:
            response = self.client.post('/delete_user/user_id')
            self.assertEqual(response.status_code, 302)  # Assuming redirection

if __name__ == '__main__':
    unittest.main()
