"""Test data module"""

import json
from pathlib import Path
from unittest.mock import patch

from api.data import list_activities
from shared_code.utils import create_params_func_request

with open(Path(__file__).parent / "data" / "get_user_data.json", "r") as f:
    mock_get_user_data = json.load(f)

mock_container_response = [
    {
        "id": "123",
        "_rid": "+qI9AL5k7vYBAAAAAAAAAA==",
        "_self": "dbs/+qI9AA==/colls/+qI9AL5k7vY=/docs/+qI9AL5k7vYBAAAAAAAAAA==/",
        "_etag": '"00000000-0000-0000-794c-37981eb601d9"',
        "_attachments": "attachments/",
        "_ts": 1682629624,
    }
]


class TestListActivities:
    """Test list_activities"""

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    def test_valid_request(self, cosmosdb_container, mock_get_user):
        """Test valid request"""
        req = create_params_func_request(
            url="/api/data/activities",
            method="GET",
            params={},
        )

        cosmosdb_container.return_value.query_items.return_value = (
            mock_container_response
        )
        mock_get_user.return_value = mock_get_user_data

        func_call = list_activities.build().get_user_function()
        result = func_call(req)
        body = json.loads(result.get_body().decode("utf-8"))
        assert result.status_code == 200
        assert body == [mock_container_response[0]]

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    def test_no_data_in_cosmosdb(self, cosmosdb_container, mock_get_user):
        """Test no data in cosmosdb"""
        req = create_params_func_request(
            url="/api/data/activities",
            method="GET",
            params={},
        )

        cosmosdb_container.return_value.query_items.return_value = []
        mock_get_user.return_value = mock_get_user_data

        func_call = list_activities.build().get_user_function()
        result = func_call(req)
        assert result.status_code == 200
        assert result.get_body() == b"{[]}"

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    def test_with_start_and_end_date(self, cosmosdb_container, mock_get_user):
        """Test with start and end date"""
        req = create_params_func_request(
            url="/api/data/activities",
            method="GET",
            params={
                "startDate": "2023-11-05T09:48:49Z",
                "endDate": "2023-11-05T09:48:49Z",
            },
        )

        mock_container_response = [
            {
                "id": "123",
                "_rid": "+qI9AL5k7vYBAAAAAAAAAA==",
                "_self": "dbs/+qI9AA==/colls/+qI9AL5k7vY=/docs/+qI9AL5k7vYBAAAAAAAAAA==/",
                "_etag": '"00000000-0000-0000-794c-37981eb601d9"',
                "_attachments": "attachments/",
                "_ts": 1682629624,
            }
        ]

        cosmosdb_container.return_value.query_items.return_value = (
            mock_container_response
        )
        mock_get_user.return_value = mock_get_user_data

        func_call = list_activities.build().get_user_function()
        result = func_call(req)

        assert result.status_code == 200
        assert result.get_body() == b'[{"id": "123"}]'
