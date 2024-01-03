""""Enrich data module"""

import datetime
import logging
import time
import uuid
from functools import partial

import azure.functions as func
from stravalib.exc import ObjectNotFound, RateLimitExceeded

from app.gather_data import add_activity_to_enrichment_queue, get_user_settings
from shared_code import cosmosdb_module, strava_helpers, trimp_helpers

bp = func.Blueprint()


@bp.function_name(name="enrich_activity")
@bp.queue_trigger(
    connection="AzureWebJobsStorage", arg_name="queue", queue_name="enrichment-queue"
)
def enrich_activity(
    queue: func.QueueMessage,
) -> None:
    """Enrich activity function"""
    # Get message
    msg = queue.get_json()
    activity_id, user_id = msg["activity_id"], msg["user_id"]
    logging.info(f"Enriching activity {activity_id} for user {user_id}")

    # Get user settings
    get_user_settings_function = get_user_settings.build().get_user_function()
    user_settings = get_user_settings_function([user_id])["user_settings"]

    # Get activity and streams data
    (
        client,
        user_settings,
    ) = strava_helpers.create_strava_client(user_settings)
    try:
        activity = client.get_activity(activity_id).dict()
        if activity is None:
            raise RateLimitExceeded
    except RateLimitExceeded:
        handle_rate_limit_exceeded()

    try:
        streams = client.get_activity_streams(
            activity_id,
            types=[
                "time",
                "latlng",
                "distance",
                "altitude",
                "velocity_smooth",
                "heartrate",
                "cadence",
                "moving",
                "grade_smooth",
            ],
        )
    except ObjectNotFound:
        streams = {}
    except RateLimitExceeded:
        handle_rate_limit_exceeded()

    # Cleanup activity and streams data
    for key, value in streams.items():
        streams[key] = value.dict()
    streams["id"] = activity_id
    streams["userId"] = user_id
    activity = strava_helpers.cleanup_activity(activity, user_id, True)

    # Calculate custom fields
    activity = calculate_custom_fields(activity, user_settings)

    # Add activity and streams data to cosmosdb6
    container = cosmosdb_module.cosmosdb_container("activities")
    cosmosdb_module.container_function_with_back_off(
        partial(
            container.upsert_item,
            activity,
        )
    )
    container = cosmosdb_module.cosmosdb_container("streams")
    cosmosdb_module.container_function_with_back_off(
        partial(
            container.upsert_item,
            streams,
        )
    )


def calculate_custom_fields(activity: dict, user_settings: dict) -> dict:
    """Calculate custom fields"""
    # Calculate Reserves
    if activity["has_heartrate"]:
        activity["hr_reserve"] = trimp_helpers.calculate_hr_reserve(
            activity["average_heartrate"],
            user_settings["heart_rate"]["resting"],
            user_settings["heart_rate"]["max"],
        )
    if activity["type"] == "Run":
        activity["pace_reserve"] = trimp_helpers.calculate_pace_reserve(
            activity["average_speed"],
            user_settings["pace"]["threshold"],
        )

    # Calculate TRIMP
    if activity["has_heartrate"]:
        activity["hr_trimp"] = trimp_helpers.calculate_hr_trimp(
            activity["moving_time"],
            activity["hr_reserve"],
            user_settings["gender"],
            True,
        )
    if activity["type"] == "Run":
        activity["pace_trimp"] = trimp_helpers.calculate_pace_trimp(
            activity["moving_time"],
            activity["pace_reserve"],
            user_settings["gender"],
            True,
        )

    # Calculate VO2Max
    if activity["has_heartrate"]:
        activity["hr_max_percentage"] = trimp_helpers.calculate_hr_max_percentage(
            activity["average_heartrate"],
            user_settings["heart_rate"]["max"],
        )
        activity["vo2max_estimate"] = trimp_helpers.calculate_vo2max_estimate(
            activity["distance"],
            activity["moving_time"],
            activity["hr_max_percentage"],
            True,
        )

    return activity


@bp.function_name(name="enrich_activity_poison_queue")
@bp.queue_trigger(
    connection="AzureWebJobsStorage",
    arg_name="queue",
    queue_name="enrichment-queue-poison",
)
def enrich_activity_poison_queue(
    queue: func.QueueMessage,
) -> None:
    """Enrich activity poison queue function"""

    try:
        msg = queue.get_json()
    except Exception:
        msg = "Error parsing message"

    try:
        user_id = msg["activity_id"]
    except KeyError:
        user_id = "unknown"

    notification = {
        "id": str(uuid.uuid4()),
        "type": "enrichment",
        "status": "failed",
        "message": msg,
        "userId": user_id,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    container = cosmosdb_module.cosmosdb_container("notifications")
    cosmosdb_module.container_function_with_back_off(
        partial(
            container.upsert_item,
            notification,
        )
    )


def handle_rate_limit_exceeded():
    """Handle rate limit exceeded"""

    now = datetime.datetime.now()
    next_15 = (now + datetime.timedelta(minutes=15 - now.minute % 15)).replace(
        second=0, microsecond=0
    )
    sleep_time = (next_15 - now).seconds
    sleep_time_original = sleep_time
    logging.info(f"Rate limit exceeded sleeping for {sleep_time} seconds")

    while sleep_time > 0:
        time.sleep(min(30, sleep_time))
        sleep_time -= 30
        if sleep_time > 0:
            logging.info(f"{sleep_time} seconds remaining")

    raise Exception(
        f"Rate limit exceeded waited for ${sleep_time_original} before raising exception and requeueing the message"
    )


@bp.timer_trigger(
    schedule="0 0 0 * * *", arg_name="timer", run_on_startup=False, use_monitor=False
)
def enqueue_non_enriched_activities(timer: func.TimerRequest) -> None:
    """Will add any none enriched activities to the enrichment queue"""
    container = cosmosdb_module.cosmosdb_container("activities")
    activities = container.query_items(
        query="SELECT * FROM c WHERE c.full_data = false",
        enable_cross_partition_query=True,
    )

    add_activity_to_enrichment_queue_function = (
        add_activity_to_enrichment_queue.build().get_user_function()
    )
    result = add_activity_to_enrichment_queue_function([activities])

    logging.info(result)
