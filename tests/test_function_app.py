"""Test the function_app module"""

from unittest.mock import patch

from function_app import app, main


@patch.object(app, "register_blueprint")
def test_main(mock_register_blueprint):
    """Test the main function."""
    # Act
    main()

    # Assert
    assert mock_register_blueprint.call_count == 6
