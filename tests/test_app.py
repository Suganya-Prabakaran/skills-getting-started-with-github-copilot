"""
Unit tests for the Mergington High School API
Using AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture providing a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Fixture to reset activities to initial state before each test"""
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and regional tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 2,
            "participants": []
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(initial_state)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(initial_state)


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities(client):
    """
    Arrange: Initialized activities in fixture
    Act: Make GET request to /activities
    Assert: Response contains all activities with correct structure
    """
    # Arrange
    expected_activities = ["Chess Club", "Programming Class", "Basketball Team"]
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert all(activity in data for activity in expected_activities)


def test_get_activities_contains_required_fields(client):
    """
    Arrange: Initialized activities in fixture
    Act: Make GET request to /activities
    Assert: Each activity has required fields (description, schedule, max_participants, participants)
    """
    # Arrange
    required_fields = ["description", "schedule", "max_participants", "participants"]
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    for activity_name, activity_data in data.items():
        for field in required_fields:
            assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"


def test_get_activities_participants_are_lists(client):
    """
    Arrange: Initialized activities in fixture with participants lists
    Act: Make GET request to /activities
    Assert: Participants field is a list for all activities
    """
    # Arrange
    # No setup needed beyond fixture
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    for activity_name, activity_data in data.items():
        assert isinstance(activity_data["participants"], list), \
            f"Participants for '{activity_name}' is not a list"


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_happy_path_adds_participant(client):
    """
    Arrange: Basketball Team with empty spots, new email
    Act: POST signup request for Basketball Team
    Assert: Participant is added and success message returned
    """
    # Arrange
    activity = "Basketball Team"
    email = "alice@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in activities[activity]["participants"]


def test_signup_invalid_activity_returns_404(client):
    """
    Arrange: Non-existent activity name
    Act: POST signup request with invalid activity
    Assert: Returns 404 with appropriate error message
    """
    # Arrange
    invalid_activity = "Nonexistent Club"
    email = "alice@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{invalid_activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_signup_duplicate_participant_returns_400(client):
    """
    Arrange: Email already registered for Chess Club
    Act: POST signup request with duplicate email
    Assert: Returns 400 with duplicate signup message
    """
    # Arrange
    activity = "Chess Club"
    duplicate_email = "michael@mergington.edu"  # Already in Chess Club
    
    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": duplicate_email}
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Already signed up" in data["detail"]


def test_signup_response_contains_message(client):
    """
    Arrange: New participant signup
    Act: POST signup request
    Assert: Response contains success message with participant and activity names
    """
    # Arrange
    activity = "Basketball Team"
    email = "bob@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert activity in data["message"]
    assert email in data["message"]


def test_signup_increases_participant_count(client):
    """
    Arrange: Basketball Team with 0 participants
    Act: POST signup request
    Assert: Participant count increases by 1
    """
    # Arrange
    activity = "Basketball Team"
    email = "charlie@mergington.edu"
    initial_count = len(activities[activity]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert len(activities[activity]["participants"]) == initial_count + 1


# ============================================================================
# DELETE /activities/{activity_name}/signup Tests
# ============================================================================

def test_delete_happy_path_removes_participant(client):
    """
    Arrange: Chess Club with registered participant
    Act: DELETE signup request for registered participant
    Assert: Participant is removed and success message returned
    """
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"  # Already in Chess Club
    initial_count = len(activities[activity]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email not in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == initial_count - 1


def test_delete_invalid_activity_returns_404(client):
    """
    Arrange: Non-existent activity name
    Act: DELETE signup request with invalid activity
    Assert: Returns 404 with appropriate error message
    """
    # Arrange
    invalid_activity = "Nonexistent Club"
    email = "someone@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{invalid_activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_delete_unregistered_participant_returns_400(client):
    """
    Arrange: Email not registered for Basketball Team
    Act: DELETE signup request for unregistered email
    Assert: Returns 400 with appropriate error message
    """
    # Arrange
    activity = "Basketball Team"
    unregistered_email = "notregistered@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": unregistered_email}
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_delete_response_contains_message(client):
    """
    Arrange: Registered participant in Chess Club
    Act: DELETE signup request
    Assert: Response contains success message with participant and activity names
    """
    # Arrange
    activity = "Chess Club"
    email = "daniel@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert activity in data["message"]
    assert email in data["message"]


def test_delete_decreases_participant_count(client):
    """
    Arrange: Chess Club with multiple participants
    Act: DELETE signup request
    Assert: Participant count decreases by 1
    """
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    initial_count = len(activities[activity]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert len(activities[activity]["participants"]) == initial_count - 1


# ============================================================================
# Edge Case Tests
# ============================================================================

def test_signup_to_activity_with_empty_participant_list(client):
    """
    Arrange: Basketball Team with no participants
    Act: POST signup request to empty activity
    Assert: Participant successfully added
    """
    # Arrange
    activity = "Basketball Team"
    email = "first@mergington.edu"
    assert len(activities[activity]["participants"]) == 0
    
    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]


def test_multiple_signups_to_different_activities(client):
    """
    Arrange: Same user wants to sign up for multiple activities
    Act: POST signup requests to different activities
    Assert: User successfully registered for all activities
    """
    # Arrange
    email = "multi@mergington.edu"
    activities_to_join = ["Basketball Team", "Programming Class"]
    
    # Act & Assert
    for activity in activities_to_join:
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
