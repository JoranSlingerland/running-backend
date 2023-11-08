"""Test the output_to_cosmosdb function."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.cosmos import ContainerProxy

from output_to_cosmosdb import output_to_cosmosdb


@pytest.mark.asyncio()
class TestoutputToCosmosdb:
    """Test output_to_cosmosdb"""

    mock_items = [
        {
            "id": "1",
        }
    ]

    @patch("shared_code.cosmosdb_module.cosmosdb_container")
    async def test_all(self, cosmosdb_container_mock):
        """Test the main function."""
        payload = ["test", self.mock_items]

        cosmosdb_container_mock.return_value = MagicMock(spec=ContainerProxy)
        cosmosdb_container_mock.return_value.create_item = AsyncMock()

        func_call = output_to_cosmosdb.build().get_user_function()
        response = await func_call(payload)

        assert response == '{"status": "Done"}'
        assert cosmosdb_container_mock.return_value.create_item.await_count == 1
        cosmosdb_container_mock.assert_called_with("test")
        cosmosdb_container_mock.return_value.create_item.assert_called_with(
            self.mock_items[0]
        )
