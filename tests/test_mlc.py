# tests/test_mlc.py

# import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime
from machine_learning_client.app import init_db, log_event, detect_motion

# Mocking environment variables
# @pytest.fixture(autouse=True)
# def mock_env_vars(monkeypatch):
#    monkeypatch.setenv("MONGO_URI", "mock_mongo_uri")


# Test for init_db
@patch("app.MongoClient")
def test_init_db(mock_mongo_client):
    db = init_db()
    mock_mongo_client.assert_called_with(
        "mock_mongo_uri", tls=True, tlsAllowInvalidCertificates=True
    )
    assert db.name == "SmartHomeSecurity"


# Test for log_event with timestamp check
@patch("app.datetime")
def test_log_event_with_timestamp(mock_datetime):
    # Mock datetime to return a fixed timestamp
    fixed_timestamp = datetime.datetime(2021, 1, 1, 12, 0, 0)
    mock_datetime.datetime.utcnow.return_value = fixed_timestamp

    # Create a mock MongoDB collection
    mock_collection = Mock()

    # Call log_event
    log_event(mock_collection, "MOTION_DETECTED")

    # Assert that insert_one was called once with the expected data
    mock_collection.insert_one.assert_called_once_with(
        {"type": "MOTION_DETECTED", "timestamp": fixed_timestamp}
    )


# Test for detect_motion
@patch("app.cv2.VideoCapture")
def test_detect_motion(mock_video_capture):
    # Setup mock for VideoCapture
    mock_video_capture.return_value.isOpened.return_value = True
    mock_video_capture.return_value.read.side_effect = [
        (True, "frame1"),
        (True, "frame2"),
        (False, None),
    ]

    # Setup mock for database
    mock_db = Mock()
    mock_events_collection = Mock()
    mock_db.__getitem__.return_value = mock_events_collection

    # Call the function
    detect_motion(mock_video_capture, mock_db)
