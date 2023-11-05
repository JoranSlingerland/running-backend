"""Strava helper functions"""

import time

from stravalib.client import Client


def initial_strava_auth(code: str, client_id: str, client_secret: str):
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


def refresh_strava_auth(refresh_token: str, client_id: str, client_secret: str):
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


def create_strava_client(auth_object: object) -> Client:
    """Create strava client"""

    is_new_auth_object = False

    client = Client()

    # check if token is expired
    if time.time() > auth_object["expires_at"]:
        auth_object = refresh_strava_auth(
            auth_object["refresh_token"],
            auth_object["client_id"],
            auth_object["client_secret"],
        )
        is_new_auth_object = True

    client.access_token = auth_object["access_token"]

    return (
        client,
        auth_object,
        is_new_auth_object,
    )
