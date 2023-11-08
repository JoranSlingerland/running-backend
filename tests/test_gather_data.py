"""Test act_get_user_settings.py"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from gather_data import get_activities, get_user_settings

with open(Path(__file__).parent / "data" / "user_settings.json", "r") as f:
    mock_user_settings = json.load(f)


class TestGetUserSettings:
    """Test get_user_settings"""

    @patch("shared_code.cosmosdb_module.get_cosmosdb_items")
    def test_main(self, mock_get_cosmosdb_items):
        """Test the main function."""
        # Arrange
        mock_get_cosmosdb_items.side_effect = [[mock_user_settings], []]
        expected_output = {
            "user_settings": mock_user_settings,
            "latest_activity": {
                "id": None,
                "start_date": None,
            },
        }

        # Act
        func_call = get_user_settings.build().get_user_function()
        result = func_call(["test_userid"])

        # Assert
        assert result == expected_output
        mock_get_cosmosdb_items.assert_any_call(
            "SELECT * FROM c WHERE c.id = @userid",
            [{"name": "@userid", "value": "test_userid"}],
            "users",
            ["_rid", "_self", "_etag", "_attachments", "_ts"],
        )
        mock_get_cosmosdb_items.assert_any_call(
            "SELECT top 1 * FROM c WHERE c.userId = @userid ORDER BY c.start_date DESC",
            [{"name": "@userid", "value": "test_userid"}],
            "activities",
            ["_rid", "_self", "_etag", "_attachments", "_ts"],
        )


class MockActivity:
    """Mock activity class"""

    def __init__(self, data):
        """Initialize"""

        self.data = data
        self.data["start_date"] = datetime.strptime(
            data["start_date"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone(timedelta(hours=0)))
        self.data["start_date_local"] = datetime.strptime(
            data["start_date_local"], "%Y-%m-%d %H:%M:%S"
        )

    def dict(self):
        """Return data"""
        return self.data


class TestGetActivities:
    """Test get_activities"""

    @patch("shared_code.strava_helpers.create_strava_client")
    def test_get_activities_none(self, mock_create_strava_client):
        """Test the main function."""

        # Arrange
        mock_client = MagicMock()
        mock_payload = [{"id": None, "start_date": None}, mock_user_settings]
        mock_create_strava_client.return_value = (mock_client, mock_user_settings)

        mock_activities = [
            MockActivity(
                {
                    "id": "1",
                    "start_date": "2022-01-01 00:00:00",
                    "start_date_local": "2022-01-01 00:00:00",
                    "userId": "def",
                }
            ),
            MockActivity(
                {
                    "id": "2",
                    "start_date": "2022-01-02 00:00:00",
                    "start_date_local": "2022-01-02 00:00:00",
                    "userId": "def",
                }
            ),
        ]
        mock_client.get_activities.return_value = mock_activities

        expected_output = {
            "activities": [
                {
                    "id": "1",
                    "start_date": "2022-01-01 00:00:00",
                    "start_date_local": "2022-01-01 00:00:00",
                    "userId": "def",
                    "full_data": False,
                },
                {
                    "id": "2",
                    "start_date": "2022-01-02 00:00:00",
                    "start_date_local": "2022-01-02 00:00:00",
                    "userId": "def",
                    "full_data": False,
                },
            ],
            "user_settings": mock_user_settings,
        }

        # Act
        func_call = get_activities.build().get_user_function()
        result = func_call(mock_payload)

        # Assert
        assert result == expected_output
        mock_create_strava_client.assert_called_once_with(mock_payload[1])
        mock_client.get_activities.assert_called_once_with()

    @patch("shared_code.strava_helpers.create_strava_client")
    def test_get_activities_with_start_date(self, mock_create_strava_client):
        """Test the main function."""

        # Arrange
        mock_client = MagicMock()
        mock_payload = [{"id": 123, "start_date": "2021-01-01"}, mock_user_settings]
        mock_create_strava_client.return_value = (mock_client, mock_user_settings)

        mock_activities = [
            MockActivity(
                {
                    "id": "1",
                    "start_date": "2022-01-01 00:00:00",
                    "start_date_local": "2022-01-01 00:00:00",
                    "userId": "def",
                }
            ),
            MockActivity(
                {
                    "id": "2",
                    "start_date": "2022-01-02 00:00:00",
                    "start_date_local": "2022-01-02 00:00:00",
                    "userId": "def",
                }
            ),
        ]
        mock_client.get_activities.return_value = mock_activities

        expected_output = {
            "activities": [
                {
                    "id": "1",
                    "start_date": "2022-01-01 00:00:00",
                    "start_date_local": "2022-01-01 00:00:00",
                    "userId": "def",
                    "full_data": False,
                },
                {
                    "id": "2",
                    "start_date": "2022-01-02 00:00:00",
                    "start_date_local": "2022-01-02 00:00:00",
                    "userId": "def",
                    "full_data": False,
                },
            ],
            "user_settings": mock_user_settings,
        }

        # Act
        func_call = get_activities.build().get_user_function()
        result = func_call(mock_payload)

        # Assert
        assert result == expected_output
        mock_create_strava_client.assert_called_once_with(mock_payload[1])
        mock_client.get_activities.assert_called_once_with(
            after=mock_payload[0]["start_date"]
        )
