"""Schema for the input data"""


def user_data() -> dict:
    """Schema for user data"""
    return {
        "type": "object",
        "properties": {
            "dark_mode": {"type": "string", "enum": ["dark", "light", "system"]},
            "strava_authentication": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                    "expires_at": {"type": "number"},
                    "client_id": {"type": "string", "minLength": 1},
                    "client_secret": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
                "required": [
                    "access_token",
                    "refresh_token",
                    "expires_at",
                    "client_id",
                    "client_secret",
                ],
            },
        },
        "additionalProperties": False,
        "required": [
            "dark_mode",
            "strava_authentication",
        ],
    }
