"""Schema for the input data"""


def user_data() -> dict:
    """Schema for user data"""
    return {
        "type": "object",
        "properties": {
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
                "properties": {
                    "threshold": {"type": "number"},
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
                "required": ["threshold", "zones"],
            },
            "gender": {"type": "string", "enum": ["male", "female"]},
            "preferences": {
                "type": "object",
                "properties": {
                    "preferred_tss_type": {"type": "string", "enum": ["hr", "pace"]},
                    "units": {"type": "string", "enum": ["metric", "imperial"]},
                    "dark_mode": {
                        "type": "string",
                        "enum": ["dark", "light", "system"],
                    },
                },
                "additionalProperties": False,
                "required": ["preferred_tss_type", "units", "dark_mode"],
            },
        },
        "additionalProperties": False,
        "required": [
            "strava_authentication",
            "heart_rate",
            "pace",
            "gender",
            "preferences",
        ],
    }
