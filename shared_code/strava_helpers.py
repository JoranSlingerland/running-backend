"""Strava helper functions"""

import time
from typing import Tuple

from stravalib.client import Client

from shared_code import cosmosdb_module


def initial_strava_auth(code: str, client_id: str, client_secret: str) -> dict:
    """Initial strava authentication"""
    client = Client()
    token_response = client.exchange_code_for_token(client_id, client_secret, code)

    auth_object = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response["refresh_token"],
        "expires_at": token_response["expires_at"],
        "client_id": client_id,
        "client_secret": client_secret,
    }

    return auth_object


def refresh_strava_auth(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Refresh strava authentication"""
    client = Client()
    token_response = client.refresh_access_token(
        client_id, client_secret, refresh_token
    )

    auth_object = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response["refresh_token"],
        "expires_at": token_response["expires_at"],
        "client_id": client_id,
        "client_secret": client_secret,
    }

    return auth_object


def create_strava_client(user_settings: object) -> Tuple[Client, dict, bool]:
    """Create strava client"""

    auth_object = user_settings["strava_authentication"]

    client = Client()

    # check if token is expired
    if time.time() > auth_object["expires_at"]:
        auth_object = refresh_strava_auth(
            auth_object["refresh_token"],
            auth_object["client_id"],
            auth_object["client_secret"],
        )
        user_settings["strava_authentication"] = auth_object
        cosmosdb_module.cosmosdb_container("users").upsert_item(user_settings)

    client.access_token = auth_object["access_token"]

    return (
        client,
        user_settings,
    )


def cleanup_activity(activity: dict, user_id: str, full_data: bool) -> object:
    """Cleanup activity"""
    # convert datetime to string
    activity["start_date"] = activity["start_date"].strftime("%Y-%m-%dT%H:%M:%SZ")
    activity["start_date_local"] = activity["start_date_local"].strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    if activity["laps"] is not None:
        for lap in activity["laps"]:
            lap["start_date"] = lap["start_date"].strftime("%Y-%m-%dT%H:%M:%SZ")
            lap["start_date_local"] = lap["start_date_local"].strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
    if activity["best_efforts"] is not None:
        for effort in activity["best_efforts"]:
            effort["start_date"] = effort["start_date"].strftime("%Y-%m-%dT%H:%M:%SZ")
            effort["start_date_local"] = effort["start_date_local"].strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
    # Add custom fields
    activity["id"] = str(activity["id"])
    activity["userId"] = user_id
    activity["full_data"] = full_data

    # Remove fields
    fields_to_remove = [
        "athlete",
        "splits_standard",
        "segment_efforts",
        "comment_count",
        "commute",
        "flagged",
        "has_kudoed",
        "hide_from_home",
        "kudos_count",
        "photo_count",
        "private",
        "total_photo_count",
        "photos",
        "suffer_score",
        "instagram_primary_photo",
        "partner_logo_url",
        "partner_brand_tag",
        "from_accepted_tag",
        "segment_leaderboard_opt_out",
    ]
    for field in fields_to_remove:
        activity.pop(field)
    if activity["best_efforts"] is not None:
        for effort in activity["best_efforts"]:
            effort.pop("athlete")
            effort.pop("activity")

    return activity
