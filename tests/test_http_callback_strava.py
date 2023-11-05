"""Test http_user_add"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from http_callback_strava import main
from shared_code.utils import create_params_func_request

with open(Path(__file__).parent / "data" / "get_user_data.json", "r") as f:
    mock_get_user_data = json.load(f)


@pytest.mark.asyncio()
@patch("shared_code.utils.get_user")
async def test_no_code_param(get_user_mock):
    """Test no code param"""
    req = create_params_func_request(
        method="get",
        params={"invalid": "invalid"},
        url="/api/callback/strava",
    )
    get_user_mock.return_value = mock_get_user_data

    response = await main(req)
    assert response.status_code == 400
    assert response.get_body() == b'{"result": "Invalid code"}'


@pytest.mark.asyncio()
@patch("shared_code.utils.get_user")
@patch("shared_code.cosmosdb_module.cosmosdb_container")
async def test_no_data_in_cosmosdb(cosmosdb_container, get_user_mock):
    """Test no data in cosmosdb"""
    req = create_params_func_request(
        url="http://localhost:7071/api/user",
        method="GET",
        params={
            "code": "code",
        },
    )

    cosmosdb_container.return_value.query_items.return_value = []
    get_user_mock.return_value = mock_get_user_data

    result = await main(req)
    assert result.status_code == 400
    assert result.get_body() == b'{"result": "User not found"}'


@pytest.mark.asyncio()
@patch("shared_code.utils.get_user")
@patch("shared_code.cosmosdb_module.cosmosdb_container")
async def test_no_id_or_secret(cosmosdb_container, get_user_mock):
    """Test no data in cosmosdb"""
    req = create_params_func_request(
        url="http://localhost:7071/api/user",
        method="GET",
        params={
            "code": "code",
        },
    )

    cosmosdb_container.return_value.query_items.return_value = [
        {
            "id": "id",
            "strava_authentication": {
                "access_token": "123",
                "refresh_token": "123",
                "expires_at": 1699220922,
                "client_id": "",
                "client_secret": "",
            },
        }
    ]
    get_user_mock.return_value = mock_get_user_data

    result = await main(req)
    assert result.status_code == 400
    assert (
        result.get_body()
        == b'{"result": "Please fill in client_id and client_secret in user settings"}'
    )


@pytest.mark.asyncio()
@patch("shared_code.strava_helpers.initial_strava_auth")
@patch("shared_code.utils.get_user")
@patch("shared_code.cosmosdb_module.cosmosdb_container")
async def test_valid_request(cosmosdb_container, get_user_mock, initial_strava_auth):
    """Test no data in cosmosdb"""
    req = create_params_func_request(
        url="http://localhost:7071/api/user",
        method="GET",
        params={
            "code": "code",
        },
    )

    initial_strava_auth.return_value = {
        "access_token": "123",
        "refresh_token": "123",
        "expires_at": 1699220922,
        "client_id": "123",
        "client_secret": "123",
    }

    cosmosdb_container.return_value.query_items.return_value = [
        {
            "id": "id",
            "strava_authentication": {
                "access_token": "123",
                "refresh_token": "123",
                "expires_at": 1699220922,
                "client_id": "123",
                "client_secret": "123",
            },
        }
    ]
    get_user_mock.return_value = mock_get_user_data

    result = await main(req)
    assert result.status_code == 200
    assert result.get_body() == b'{"result": "done"}'
    # check if strava_helpers.initial_strava_auth is called with correct parameters
    initial_strava_auth.assert_called_with("code", client_id="123", client_secret="123")
    cosmosdb_container.return_value.upsert_item.assert_called_with(
        {
            "id": "id",
            "strava_authentication": {
                "access_token": "123",
                "refresh_token": "123",
                "expires_at": 1699220922,
                "client_id": "123",
                "client_secret": "123",
            },
        }
    )
