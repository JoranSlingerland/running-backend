"""Add user data."""

import azure.functions as func

from shared_code import cosmosdb_module, strava_helpers, user_helpers

bp = func.Blueprint()


@bp.route(route="callback/strava", methods=["GET"])
async def callback_strava(req: func.HttpRequest) -> func.HttpResponse:
    """Add user data."""
    # Get request data
    code = req.params.get("code")
    scope = req.params.get("scope")
    userid = user_helpers.get_user(req)["userId"]

    # Set parameters
    parameters = [{"name": "@userid", "value": userid}]

    # Validate request
    if not code or not scope:
        return func.HttpResponse(
            body='{"result": "Missing code or scope"}',
            mimetype="application/json",
            status_code=400,
        )

    expected_scope = ["read", "activity:read_all", "profile:read_all"]
    if sorted(scope.split(",")) != sorted(expected_scope):
        return func.HttpResponse(
            body='{"result": "Invalid scope"}',
            mimetype="application/json",
            status_code=400,
        )

    user_settings = cosmosdb_module.get_cosmosdb_items(
        "SELECT * FROM c WHERE c.id = @userid", parameters, "users"
    )

    if not user_settings:
        return func.HttpResponse(
            body='{"result": "User not found"}',
            mimetype="application/json",
            status_code=400,
        )
    else:
        user_settings = user_settings[0]

    # Get Strava authentication object
    auth_object = strava_helpers.initial_strava_auth(
        code,
    )

    # Update user settings
    user_settings["strava_authentication"] = auth_object
    container = cosmosdb_module.cosmosdb_container("users")
    container.upsert_item(user_settings)

    return func.HttpResponse(
        body='{"result": "Success"}',
        mimetype="application/json",
        status_code=200,
    )
