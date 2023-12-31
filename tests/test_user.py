"""Test http_user_add"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import azure.functions as func
import pytest
from azure.cosmos import ContainerProxy

from api.user import get_user, post_user
from shared_code.utils import create_params_func_request

with open(Path(__file__).parent / "data" / "get_user_data.json", "r") as f:
    mock_get_user_data = json.load(f)


@pytest.mark.asyncio()
class TestPostUser:
    """Test post_user"""

    async def test_invalid_json_body(self):
        """Test with invalid json body"""
        req = func.HttpRequest(
            method="POST",
            body={"invalid": "json"},
            url="/api/user",
        )

        func_call = post_user.build().get_user_function()
        response = await func_call(req)

        assert response.status_code == 400
        assert response.get_body() == b'{"result": "Invalid json body"}'

    async def test_invalid_schema(self):
        """Test invalid schema"""
        body = {"invalid": "json"}

        req = func.HttpRequest(
            method="POST",
            body=json.dumps(body).encode("utf-8"),
            url="/api/user",
        )

        func_call = post_user.build().get_user_function()
        response = await func_call(req)
        assert response.status_code == 400
        assert response.get_body() == b'{"result": "Schema validation failed"}'

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    async def test_main(self, cosmosdb_container_mock, get_user_mock):
        """Test add_item_to_input"""
        body = {
            "dark_mode": "system",
            "strava_authentication": {
                "access_token": "123",
                "refresh_token": "123",
                "expires_at": 123,
            },
            "heart_rate": {
                "max": 206,
                "resting": 48,
                "threshold": 192,
                "zones": [{"name": "Zone 1: Recovery", "min": 0, "max": 164}],
            },
            "pace": {
                "threshold": 3.8461538461538463,
                "zones": [{"name": "Zone 1: Recovery", "min": 3, "max": 0}],
            },
        }

        req = func.HttpRequest(
            method="POST",
            body=json.dumps(body).encode("utf-8"),
            url="/api/user",
        )

        cosmosdb_container_mock.return_value = MagicMock(spec=ContainerProxy)
        cosmosdb_container_mock.return_value.create_item = AsyncMock()
        get_user_mock.return_value = mock_get_user_data

        func_call = post_user.build().get_user_function()
        response = await func_call(req)

        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.get_body().decode() == '{"result": "done"}'


class TestGetUser:
    """Test get_user"""

    mock_container_response = [
        {
            "id": "123",
            "dark_mode": True,
            "strava_client_id": "123",
            "strava_client_secret": "123",
            "_rid": "+qI9AL5k7vYBAAAAAAAAAA==",
            "_self": "dbs/+qI9AA==/colls/+qI9AL5k7vY=/docs/+qI9AL5k7vYBAAAAAAAAAA==/",
            "_etag": '"00000000-0000-0000-794c-37981eb601d9"',
            "_attachments": "attachments/",
            "_ts": 1682629624,
        }
    ]

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    def test_valid_request(self, cosmosdb_container, mock_get_user):
        """Test valid request"""
        req = create_params_func_request(
            url="http://localhost:7071/api/user",
            method="GET",
            params={},
        )

        cosmosdb_container.return_value.query_items.return_value = (
            self.mock_container_response
        )
        mock_get_user.return_value = mock_get_user_data

        func_call = get_user.build().get_user_function()
        result = func_call(req)
        body = json.loads(result.get_body().decode("utf-8"))
        assert result.status_code == 200
        assert body == self.mock_container_response[0]

    @patch("shared_code.utils.get_user")
    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    def test_no_data_in_cosmosdb(self, cosmosdb_container, mock_get_user):
        """Test no data in cosmosdb"""
        req = create_params_func_request(
            url="http://localhost:7071/api/user",
            method="GET",
            params={},
        )

        cosmosdb_container.return_value.query_items.return_value = []
        mock_get_user.return_value = mock_get_user_data

        func_call = get_user.build().get_user_function()
        result = func_call(req)
        assert result.status_code == 400
        assert result.get_body() == b'{"status": "No data found"}'
