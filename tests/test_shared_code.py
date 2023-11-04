"""Test get_config.py"""

import asyncio
import os
from unittest import mock

import pytest
from azure.cosmos import exceptions

from shared_code import aio_helper, cosmosdb_module, get_config, utils


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
    async def test_container_function_with_back_off(self):
        """Test container function with back off"""
        function = mock.AsyncMock()
        max_retries = 2
        delay = 0.1
        max_delay = 1

        await cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosResourceExistsError()
        await cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = exceptions.CosmosHttpResponseError(status_code=404)
        await cosmosdb_module.container_function_with_back_off(
            function, max_retries, delay, max_delay
        )
        function.assert_called_once()

        function.reset_mock()
        function.side_effect = Exception("test exception")

        # should raise an exception exception("test exception")
        with pytest.raises(Exception, match="test exception"):
            await cosmosdb_module.container_function_with_back_off(
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
