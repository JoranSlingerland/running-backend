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
                },
                "additionalProperties": False,
                "required": [
                    "access_token",
                    "refresh_token",
                    "expires_at",
                ],
            },
            "heart_rate": {
                "type": "object",
                "properties": {
                    "max": {"type": "integer"},
                    "resting": {"type": "integer"},
                    "threshold": {"type": "integer"},
                    "zones": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "min": {"type": "number"},
                                "max": {"type": "number"},
                            },
                            "additionalProperties": False,
                            "required": ["name", "min", "max"],
                        },
                        "additionalItems": True,
                    },
                },
                "additionalProperties": False,
                "required": ["max", "resting", "threshold", "zones"],
            },
            "pace": {
                "type": "object",
                "properties": {"threshold": {"type": "integer"}},
                "additionalProperties": False,
                "required": ["threshold"],
            },
        },
        "additionalProperties": False,
        "required": [
            "dark_mode",
            "strava_authentication",
            "heart_rate",
            "pace",
        ],
    }
