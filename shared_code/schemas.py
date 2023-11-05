"""Schema for the input data"""


def user_data() -> dict:
    """Schema for user data"""
    return {
        "type": "object",
        "properties": {
            "dark_mode": {"type": "string", "enum": ["dark", "light", "system"]},
            "strava_client_id": {"type": "string", "minLength": 1},
            "strava_client_secret": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
        "required": [
            "dark_mode",
            "strava_client_id",
            "strava_client_secret",
        ],
    }
