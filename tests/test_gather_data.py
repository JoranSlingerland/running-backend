"""Test act_get_user_settings.py"""

import json
from pathlib import Path
from unittest.mock import patch

from gather_data import get_user_settings

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
