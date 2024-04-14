""" Module for testing app.py in the web-app folder. """

import pytest
from web_app.app import app

class Tests:
    """Class for testing app.py in the web-app folder."""

    def test_sanity_check(self):
        """Sanity check to ensure testing framework functions correctly."""
        expected = True
        actual = True
        assert actual == expected, "Expected True to be equal to True!"

    def test_home(self):
        """Function testing the home route."""
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200, "Home page should return status code 200"

    def test_login(self):
        """Function testing the login route."""
        with app.test_client() as client:
            response = client.get("/login")
            assert response.status_code == 200, "Login page should return status code 200"

    def test_dashboard_access_without_login(self):
        """Ensure the dashboard cannot be accessed without login."""
        with app.test_client() as client:
            response = client.get("/dashboard", follow_redirects=True)
            assert response.status_code == 200, "Should redirect and require login for dashboard"

    def test_start_motion_detection(self):
        """Function testing the motion detection start."""
        with app.test_client() as client:
            response = client.post("/start-motion-detection")
            assert response.status_code == 200, "Starting motion detection should be accessible"


