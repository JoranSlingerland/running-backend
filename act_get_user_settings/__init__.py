"""Get user settings"""

import logging

from shared_code import cosmosdb_module


def main(payload: str) -> dict:
    """Get user data and strava client"""
    logging.info("Getting user data + strava client")

    # suppress logger output
    logger = logging.getLogger("azure")
    logger.setLevel(logging.CRITICAL)

    userid = payload[0]

    parameters = [{"name": "@userid", "value": userid}]
    keys_to_pop = ["_rid", "_self", "_etag", "_attachments", "_ts"]

    # TODO Handle case where user does not exist in cosmosdb
    user_settings = cosmosdb_module.get_cosmosdb_items(
        "SELECT * FROM c WHERE c.id = @userid", parameters, "users", keys_to_pop
    )[0]

    latest_activity = cosmosdb_module.get_cosmosdb_items(
        "SELECT top 1 * FROM c WHERE c.userId = @userid ORDER BY c.start_date DESC",
        parameters,
        "activities",
        keys_to_pop,
    )

    return {
        "user_settings": user_settings,
        "latest_activity": {
            "id": latest_activity[0]["id"] if latest_activity else None,
            "start_date": latest_activity[0]["startDate"] if latest_activity else None,
        },
    }
