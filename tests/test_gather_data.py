"""Test act_get_user_settings.py"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from azure.storage.queue import QueueClient

from app.gather_data import (
    add_activity_to_enrichment_queue,
    get_activities,
    get_user_settings,
)

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
            data["start_date"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone(timedelta(hours=0)))
        self.data["start_date_local"] = datetime.strptime(
            data["start_date_local"], "%Y-%m-%dT%H:%M:%SZ"
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
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "athlete": "test",
                    "splits_standard": "test",
                    "segment_efforts": "test",
                    "laps": None,
                    "best_efforts": None,
                    "comment_count": "test",
                    "commute": "test",
                    "flagged": "test",
                    "has_kudoed": "test",
                    "hide_from_home": "test",
                    "kudos_count": "test",
                    "photo_count": "test",
                    "private": "test",
                    "total_photo_count": "test",
                    "photos": "test",
                    "suffer_score": "test",
                    "instagram_primary_photo": "test",
                    "partner_logo_url": "test",
                    "partner_brand_tag": "test",
                    "from_accepted_tag": "test",
                    "segment_leaderboard_opt_out": "test",
                }
            ),
            MockActivity(
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "athlete": "test",
                    "splits_standard": "test",
                    "segment_efforts": "test",
                    "laps": None,
                    "best_efforts": None,
                    "comment_count": "test",
                    "commute": "test",
                    "flagged": "test",
                    "has_kudoed": "test",
                    "hide_from_home": "test",
                    "kudos_count": "test",
                    "photo_count": "test",
                    "private": "test",
                    "total_photo_count": "test",
                    "photos": "test",
                    "suffer_score": "test",
                    "instagram_primary_photo": "test",
                    "partner_logo_url": "test",
                    "partner_brand_tag": "test",
                    "from_accepted_tag": "test",
                    "segment_leaderboard_opt_out": "test",
                }
            ),
        ]
        mock_client.get_activities.return_value = mock_activities

        expected_output = {
            "activities": [
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "laps": None,
                    "best_efforts": None,
                    "full_data": False,
                    "hr_reserve": None,
                    "pace_reserve": None,
                    "hr_trimp": None,
                    "pace_trimp": None,
                    "hr_max_percentage": None,
                    "vo2max_estimate": {
                        "workout_vo2_max": None,
                        "vo2_max_percentage": None,
                        "estimated_vo2_max": None,
                    },
                    "user_input": {
                        "include_in_vo2max_estimate": True,
                        "tags": [],
                        "notes": "",
                    },
                },
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "laps": None,
                    "best_efforts": None,
                    "full_data": False,
                    "hr_reserve": None,
                    "pace_reserve": None,
                    "hr_trimp": None,
                    "pace_trimp": None,
                    "hr_max_percentage": None,
                    "vo2max_estimate": {
                        "workout_vo2_max": None,
                        "vo2_max_percentage": None,
                        "estimated_vo2_max": None,
                    },
                    "user_input": {
                        "include_in_vo2max_estimate": True,
                        "tags": [],
                        "notes": "",
                    },
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
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "athlete": "test",
                    "splits_standard": "test",
                    "segment_efforts": "test",
                    "laps": None,
                    "best_efforts": None,
                    "comment_count": "test",
                    "commute": "test",
                    "flagged": "test",
                    "has_kudoed": "test",
                    "hide_from_home": "test",
                    "kudos_count": "test",
                    "photo_count": "test",
                    "private": "test",
                    "total_photo_count": "test",
                    "photos": "test",
                    "suffer_score": "test",
                    "instagram_primary_photo": "test",
                    "partner_logo_url": "test",
                    "partner_brand_tag": "test",
                    "from_accepted_tag": "test",
                    "segment_leaderboard_opt_out": "test",
                }
            ),
            MockActivity(
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "athlete": "test",
                    "splits_standard": "test",
                    "segment_efforts": "test",
                    "laps": None,
                    "best_efforts": None,
                    "comment_count": "test",
                    "commute": "test",
                    "flagged": "test",
                    "has_kudoed": "test",
                    "hide_from_home": "test",
                    "kudos_count": "test",
                    "photo_count": "test",
                    "private": "test",
                    "total_photo_count": "test",
                    "photos": "test",
                    "suffer_score": "test",
                    "instagram_primary_photo": "test",
                    "partner_logo_url": "test",
                    "partner_brand_tag": "test",
                    "from_accepted_tag": "test",
                    "segment_leaderboard_opt_out": "test",
                }
            ),
        ]
        mock_client.get_activities.return_value = mock_activities

        expected_output = {
            "activities": [
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "laps": None,
                    "best_efforts": None,
                    "full_data": False,
                    "hr_reserve": None,
                    "pace_reserve": None,
                    "hr_trimp": None,
                    "pace_trimp": None,
                    "hr_max_percentage": None,
                    "vo2max_estimate": {
                        "workout_vo2_max": None,
                        "vo2_max_percentage": None,
                        "estimated_vo2_max": None,
                    },
                    "user_input": {
                        "include_in_vo2max_estimate": True,
                        "tags": [],
                        "notes": "",
                    },
                },
                {
                    "id": "1",
                    "start_date": "2022-01-01T00:00:00Z",
                    "start_date_local": "2022-01-01T00:00:00Z",
                    "userId": "def",
                    "laps": None,
                    "best_efforts": None,
                    "full_data": False,
                    "hr_reserve": None,
                    "pace_reserve": None,
                    "hr_trimp": None,
                    "pace_trimp": None,
                    "hr_max_percentage": None,
                    "vo2max_estimate": {
                        "workout_vo2_max": None,
                        "vo2_max_percentage": None,
                        "estimated_vo2_max": None,
                    },
                    "user_input": {
                        "include_in_vo2max_estimate": True,
                        "tags": [],
                        "notes": "",
                    },
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


class TestAddActivityToEnrichmentQueue:
    """Test add_activity_to_enrichment_queue"""

    @patch.dict(
        os.environ,
        {
            "AZUREWEBJOBSSTORAGE": "test_endpoint",
        },
    )
    @patch.object(QueueClient, "from_connection_string", return_value=Mock())
    def test_add_activity_to_enrichment_queue(self, mock_queue_client):
        """Test the main function."""
        mock_queue_client.return_value.send_message = Mock()

        payload = [
            {"id": "123", "userId": "abc"},
            {"id": "456", "userId": "def"},
        ]

        # Call
        func_call = add_activity_to_enrichment_queue.build().get_user_function()
        result = func_call([payload])

        # Assert
        assert result == {"status": "success"}
        assert mock_queue_client.return_value.send_message.call_count == len(payload)

        for activity in payload:
            mock_queue_client.return_value.send_message.assert_any_call(
                json.dumps(
                    {"activity_id": activity["id"], "user_id": activity["userId"]}
                )
            )
