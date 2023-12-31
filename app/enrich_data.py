""""Enrich data module"""

import datetime
import logging
import time
from functools import partial

import azure.functions as func
from stravalib.exc import ObjectNotFound, RateLimitExceeded

from shared_code import cosmosdb_module, queue_helpers, strava_helpers, user_helpers

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
    user_settings = user_helpers.get_user_settings(user_id)

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
    activity = strava_helpers.cleanup_activity(activity, user_id, True, False)

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

    # Add activity to calculate_fields queue
    queue_helpers.add_activity_to_enrichment_queue([activity], "calculate-fields-queue")


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
    queue_helpers.handle_poison_message(queue, "enrichment-queue")


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
