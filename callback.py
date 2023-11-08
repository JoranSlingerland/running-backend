"""Add user data."""

import azure.functions as func

from shared_code import cosmosdb_module, strava_helpers, utils

bp = func.Blueprint()


@bp.route(route="callback/strava", methods=["GET"], auth_level="anonymous")
async def callback_strava(req: func.HttpRequest) -> func.HttpResponse:
    """Add user data."""
    # Get request data
    code = req.params.get("code")
    userid = utils.get_user(req)["userId"]

    # Set parameters
    parameters = [{"name": "@userid", "value": userid}]
    keys_to_pop = ["_rid", "_self", "_etag", "_attachments", "_ts"]

    # Validate request
    if not code:
        return func.HttpResponse(
            body='{"result": "Invalid code"}',
            mimetype="application/json",
            status_code=400,
        )

    user_settings = cosmosdb_module.get_cosmosdb_items(
        "SELECT * FROM c WHERE c.id = @userid", parameters, "users", keys_to_pop
    )

    if not user_settings:
        return func.HttpResponse(
            body='{"result": "User not found"}',
            mimetype="application/json",
            status_code=400,
        )
    else:
        user_settings = user_settings[0]

    if (
        not user_settings["strava_authentication"]["client_id"]
        or not user_settings["strava_authentication"]["client_secret"]
    ):
        return func.HttpResponse(
            body='{"result": "Please fill in client_id and client_secret in user settings"}',
            mimetype="application/json",
            status_code=400,
        )

    # Get Strava authentication object
    auth_object = strava_helpers.initial_strava_auth(
        code,
        client_id=user_settings["strava_authentication"]["client_id"],
        client_secret=user_settings["strava_authentication"]["client_secret"],
    )

    # Update user settings
    user_settings["strava_authentication"] = auth_object
    container = cosmosdb_module.cosmosdb_container("users")
    container.upsert_item(user_settings)

    return func.HttpResponse(
        body='{"result": "done"}',
        mimetype="application/json",
        status_code=200,
    )
