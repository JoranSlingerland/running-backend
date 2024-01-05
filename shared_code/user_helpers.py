"""Helper functions for getting user data"""

import base64
import json
import logging

import azure.functions as func

from shared_code import cosmosdb_module


def get_user(
    req: func.HttpRequest,
) -> dict[str, str | list[str]]:
    """Get user from request"""

    headers = req.headers.get("x-ms-client-principal", None)
    if headers:
        headers = base64.b64decode(headers).decode("ascii")
        headers = json.loads(headers)

    return headers


def get_user_settings(userid: str) -> dict:
    """Get user data and strava client"""
    logging.info("Getting user data")

    # suppress logger output
    logger = logging.getLogger("azure")
    logger.setLevel(logging.CRITICAL)

    parameters = [{"name": "@userid", "value": userid}]

    user_settings = cosmosdb_module.get_cosmosdb_items(
        "SELECT * FROM c WHERE c.id = @userid", parameters, "users"
    )

    if not user_settings:
        raise ValueError(f"No user found with id {userid}")

    return user_settings[0]
