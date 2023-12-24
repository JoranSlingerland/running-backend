"""Test get_config.py"""

import asyncio
import base64
import datetime
import json
import os
from pathlib import Path
from unittest import mock

import azure.functions as func
import pytest
import time_machine
from azure.cosmos import exceptions

from shared_code import aio_helper, cosmosdb_module, get_config, strava_helpers, utils

with open(Path(__file__).parent / "data" / "get_user_data.json", "r") as f:
    mock_get_user_data = json.load(f)

with open(Path(__file__).parent / "data" / "user_settings.json", "r") as f:
    mock_user_settings = json.load(f)


@pytest.mark.asyncio()
async def test_gather_with_concurrency():
    """Test gather with concurrency"""

    async def my_coroutine(test_input):
        await asyncio.sleep(0.1)
        return test_input * 2

    tasks = [my_coroutine(i) for i in range(10)]
    result = await aio_helper.gather_with_concurrency(5, *tasks)
    assert result == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]


class TestCosmosdbModule:
    """Test cosmosdb module"""

    @mock.patch("shared_code.get_config.get_cosmosdb")
    @mock.patch("azure.cosmos.cosmos_client.CosmosClient")
    def test_cosmosdb_client(self, mock_cosmos_client, mock_get_cosmosdb):
        """Test cosmosdb client with mocked config and client"""
        mock_config = mock.MagicMock()
        mock_config.__getitem__.side_effect = lambda key: {
            "endpoint": "mock_endpoint",
            "key": "mock_key",
        }[key]
        mock_get_cosmosdb.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_cosmos_client.return_value = mock_client

        client = cosmosdb_module.cosmosdb_client()

        mock_cosmos_client.assert_called_once_with("mock_endpoint", "mock_key")
        assert client == mock_client

    @mock.patch("shared_code.cosmosdb_module.cosmosdb_client")
    @mock.patch("shared_code.cosmosdb_module.get_config.get_cosmosdb")
    def test_cosmosdb_database(self, mock_get_cosmosdb, mock_cosmosdb_client):
        """Test cosmosdb database"""
        mock_get_cosmosdb.return_value = {"database": "mock database"}
        mock_client = mock_cosmosdb_client.return_value
        mock_database_client = mock_client.get_database_client.return_value
        mock_database_client.return_value = "mock database client"

        result = cosmosdb_module.cosmosdb_database()

        # Assert that the result is as expected
        assert result == mock_database_client

    @mock.patch("shared_code.cosmosdb_module.cosmosdb_database")
    def test_cosmosdb_container(self, mock_cosmosdb_database):
        """Test cosmosdb container"""
        # mock_get_config = mock_get_config.return_value
        mock_database = mock_cosmosdb_database.return_value
        mock_container_client = mock_database.get_container_client.return_value
        result = cosmosdb_module.cosmosdb_container("mock container name")
        assert result == mock_container_client

    @pytest.mark.asyncio()
    async def test_container_function_with_back_off_async(self):
        """Test container function with back off"""
        function = mock.AsyncMock()
        max_retries = 2
        delay = 0.1
        max_delay = 1

        await cosmosdb_module.container_function_with_back_off_async(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosResourceExistsError()
        await cosmosdb_module.container_function_with_back_off_async(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosHttpResponseError(status_code=404)
        await cosmosdb_module.container_function_with_back_off_async(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = Exception("test exception")

        # should raise an exception exception("test exception")
        with pytest.raises(Exception, match="test exception"):
            await cosmosdb_module.container_function_with_back_off_async(
                function, max_retries, delay, max_delay
            )
        assert function.call_count == max_retries + 1

    def test_container_function_with_back_off(self):
        """Test container function with back off"""
        function = mock.Mock()
        max_retries = 2
        delay = 0.1
        max_delay = 1

        cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosResourceExistsError()
        cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosHttpResponseError(status_code=404)
        cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = Exception("test exception")

        # should raise an exception exception("test exception")
        with pytest.raises(Exception, match="test exception"):
            cosmosdb_module.container_function_with_back_off(
                function, max_retries, delay, max_delay
            )
        assert function.call_count == max_retries + 1


class TestGetConfig:
    """Test get_config.py"""

    @mock.patch.dict(
        os.environ,
        {
            "COSMOSDB_ENDPOINT": "test_endpoint",
            "COSMOSDB_KEY": "test_key",
            "COSMOSDB_DATABASE": "test_database",
        },
    )
    def test_get_cosmosdb(self):
        """Test get cosmosdb"""
        cosmosdb = get_config.get_cosmosdb()
        assert cosmosdb["endpoint"] == "test_endpoint"
        assert cosmosdb["key"] == "test_key"
        assert cosmosdb["database"] == "test_database"


class TestUtils:
    """Test utils"""

    def test_get_unique_items(self):
        """Test get unique items"""
        items = [
            {"key_to_filter": "a"},
            {"key_to_filter": "b"},
            {"key_to_filter": "c"},
            {"key_to_filter": "a"},
            {"key_to_filter": "b"},
            {"key_to_filter": "c"},
        ]
        key_to_filter = "key_to_filter"
        unique_items = utils.get_unique_items(items, key_to_filter)
        assert unique_items == ["a", "b", "c"]

        items = []
        unique_items = utils.get_unique_items(items, key_to_filter)
        assert not unique_items

    def test_get_weighted_average(self):
        """Test get weighted average"""
        data = [1, 4]
        weight = [1, 2]
        weighted_average = utils.get_weighted_average(data, weight)
        assert weighted_average == 3.0

    def test_get_user(self):
        """Test get user"""
        x_ms_client_principal = base64.b64encode(
            json.dumps(mock_get_user_data).encode("ascii")
        )

        req = func.HttpRequest(
            method="GET",
            url="/api/user",
            body=None,
            headers={
                "x-ms-client-principal": x_ms_client_principal,
            },
        )

        user = utils.get_user(req)

        assert user == mock_get_user_data


class TestStravaHelpers:
    """Test strava_helpers.py"""

    @mock.patch("shared_code.strava_helpers.Client")
    def test_initial_strava_auth(self, mock_client):
        """Test initial strava auth"""
        # Arrange
        mock_code = "test_code"
        auth_object = mock_user_settings["strava_authentication"]

        mock_client_instance = mock.MagicMock()
        mock_client_instance.exchange_code_for_token.return_value = {
            "access_token": auth_object["access_token"],
            "refresh_token": auth_object["refresh_token"],
            "expires_at": auth_object["expires_at"],
        }
        mock_client.return_value = mock_client_instance

        # Act
        result = strava_helpers.initial_strava_auth(mock_code)

        # Assert
        assert result == auth_object

    @mock.patch("shared_code.strava_helpers.Client")
    @mock.patch.dict(
        os.environ,
        {
            "STRAVA_CLIENT_ID": "test_client_id",
            "STRAVA_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_refresh_strava_auth(self, mock_client):
        """Test refresh strava auth"""
        # Arrange
        auth_object = mock_user_settings["strava_authentication"]

        mock_client_instance = mock.MagicMock()
        mock_client_instance.refresh_access_token.return_value = {
            "access_token": auth_object["access_token"],
            "refresh_token": auth_object["refresh_token"],
            "expires_at": auth_object["expires_at"],
        }
        mock_client.return_value = mock_client_instance

        # Act
        result = strava_helpers.refresh_strava_auth(
            auth_object["refresh_token"],
        )

        # Assert
        assert result == auth_object
        mock_client_instance.refresh_access_token.assert_called_once_with(
            "test_client_id",
            "test_client_secret",
            auth_object["refresh_token"],
        )

    @time_machine.travel("2025-01-01")
    @mock.patch("shared_code.cosmosdb_module.cosmosdb_container")
    @mock.patch("shared_code.strava_helpers.Client")
    @mock.patch("shared_code.strava_helpers.refresh_strava_auth")
    def test_create_strava_client(
        self, mock_refresh_strava_auth, mock_client, mock_container
    ):
        """Test create strava client"""
        # Arrange
        mock_refresh_strava_auth.return_value = mock_user_settings[
            "strava_authentication"
        ]

        mock_client_instance = mock.MagicMock()
        mock_client.return_value = mock_client_instance

        # Act
        result = strava_helpers.create_strava_client(mock_user_settings)

        # Assert
        mock_refresh_strava_auth.assert_called_once_with(
            mock_user_settings["strava_authentication"]["refresh_token"],
        )
        assert result == (mock_client_instance, mock_user_settings)
        assert (
            mock_client_instance.access_token
            == mock_user_settings["strava_authentication"]["access_token"]
        )

    def test_cleanup_activity(self):
        """Test cleanup activity"""
        # Create a mock activity
        mock_activity = {
            "start_date": datetime.datetime.now(),
            "start_date_local": datetime.datetime.now(),
            "laps": [
                {
                    "start_date": datetime.datetime.now(),
                    "start_date_local": datetime.datetime.now(),
                }
            ],
            "best_efforts": [
                {
                    "start_date": datetime.datetime.now(),
                    "start_date_local": datetime.datetime.now(),
                    "athlete": "mock_athlete",
                    "activity": "mock_activity",
                }
            ],
            "id": 123,
            "athlete": "mock_athlete",
            "splits_standard": "mock_splits_standard",
            "segment_efforts": "mock_segment_efforts",
            "comment_count": "mock_comment_count",
            "commute": "mock_commute",
            "flagged": "mock_flagged",
            "has_kudoed": "mock_has_kudoed",
            "hide_from_home": "mock_hide_from_home",
            "kudos_count": "mock_kudos_count",
            "photo_count": "mock_photo_count",
            "private": "mock_private",
            "total_photo_count": "mock_total_photo_count",
            "photos": "mock_photos",
            "suffer_score": "mock_suffer_score",
            "instagram_primary_photo": "mock_instagram_primary_photo",
            "partner_logo_url": "mock_partner_logo_url",
            "partner_brand_tag": "mock_partner_brand_tag",
            "from_accepted_tag": "mock_from_accepted_tag",
            "segment_leaderboard_opt_out": "mock_segment_leaderboard_opt_out",
        }

        # Call cleanup_activity with the mock activity
        cleaned_activity = strava_helpers.cleanup_activity(
            mock_activity, "mock_user_id", True
        )

        # Check that the returned activity has the expected format
        assert isinstance(cleaned_activity, dict)
        assert "start_date" in cleaned_activity
        assert "start_date_local" in cleaned_activity
        assert "laps" in cleaned_activity
        assert "best_efforts" in cleaned_activity
        assert "id" in cleaned_activity
        assert "userId" in cleaned_activity
        assert "full_data" in cleaned_activity
        assert "athlete" not in cleaned_activity
        assert "splits_standard" not in cleaned_activity
        assert "segment_efforts" not in cleaned_activity
        assert "comment_count" not in cleaned_activity
        assert "commute" not in cleaned_activity
        assert "flagged" not in cleaned_activity
        assert "has_kudoed" not in cleaned_activity
        assert "hide_from_home" not in cleaned_activity
        assert "kudos_count" not in cleaned_activity
        assert "photo_count" not in cleaned_activity
        assert "private" not in cleaned_activity
        assert "total_photo_count" not in cleaned_activity
        assert "photos" not in cleaned_activity
        assert "suffer_score" not in cleaned_activity
        assert "instagram_primary_photo" not in cleaned_activity
        assert "partner_logo_url" not in cleaned_activity
        assert "partner_brand_tag" not in cleaned_activity
        assert "from_accepted_tag" not in cleaned_activity
        assert "segment_leaderboard_opt_out" not in cleaned_activity
