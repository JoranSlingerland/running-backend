"""Calculate custom fields for activities"""

import bisect
import logging
from functools import partial
from statistics import mean

import azure.functions as func

from shared_code import cosmosdb_module, queue_helpers, trimp_helpers, user_helpers

bp = func.Blueprint()


@bp.function_name(name="calculate_fields")
@bp.queue_trigger(
    connection="AzureWebJobsStorage",
    arg_name="queue",
    queue_name="calculate-fields-queue",
)
def calculate_fields(
    queue: func.QueueMessage,
) -> None:
    """Calculate custom fields"""
    msg = queue.get_json()
    activity_id, user_id = msg["activity_id"], msg["user_id"]
    logging.info(f"Calculating values for {activity_id} and user {user_id}")

    # Get user settings
    user_settings = user_helpers.get_user_settings(user_id)

    # Get activity
    parameters = [
        {"name": "@activity_id", "value": activity_id},
        {"name": "@user_id", "value": user_id},
    ]
    query = "SELECT * FROM c WHERE c.id = @activity_id AND c.userId = @user_id"
    activity = cosmosdb_module.get_cosmosdb_items(query, parameters, "activities")
    stream = cosmosdb_module.get_cosmosdb_items(query, parameters, "streams")

    if not activity or not stream:
        logging.error(
            f"No activity or stream found with id {activity_id} and user {user_id}"
        )
        return

    # Calculate custom fields
    activity = calculate_custom_fields(activity[0], stream[0], user_settings)

    # Update activity
    container = cosmosdb_module.cosmosdb_container("activities")
    cosmosdb_module.container_function_with_back_off(
        partial(
            container.upsert_item,
            activity,
        )
    )


def calculate_custom_fields(activity: dict, stream: dict, user_settings: dict) -> dict:
    """Calculate custom fields"""
    # Calculate Reserves
    total_time = 0
    if activity["has_heartrate"]:
        for lap in activity["laps"]:
            start_time = total_time
            elapsed_time = lap["elapsed_time"]
            total_time += elapsed_time
            lap["start_index"] = bisect.bisect_left(stream["time"]["data"], start_time)
            lap["end_index"] = bisect.bisect_left(stream["time"]["data"], total_time)
            heart_rate_data = stream["heartrate"]["data"][
                lap["start_index"] : lap["end_index"]
            ]
            lap["average_heartrate"] = mean(heart_rate_data)
            lap["hr_reserve"] = trimp_helpers.calculate_hr_reserve(
                lap["average_heartrate"],
                user_settings["heart_rate"]["resting"],
                user_settings["heart_rate"]["max"],
            )

        activity["hr_reserve"] = trimp_helpers.calculate_hr_reserve(
            activity["average_heartrate"],
            user_settings["heart_rate"]["resting"],
            user_settings["heart_rate"]["max"],
        )

    if activity["type"] == "Run":
        for lap in activity["laps"]:
            lap["pace_reserve"] = trimp_helpers.calculate_pace_reserve(
                lap["average_speed"],
                user_settings["pace"]["threshold"],
            )

        activity["pace_reserve"] = trimp_helpers.calculate_pace_reserve(
            activity["average_speed"],
            user_settings["pace"]["threshold"],
        )

    # Calculate TRIMP
    if activity["has_heartrate"]:
        for lap in activity["laps"]:
            lap["hr_trimp"] = trimp_helpers.calculate_hr_trimp(
                lap["moving_time"],
                lap["hr_reserve"],
                user_settings["gender"],
                True,
            )
        activity["hr_trimp"] = sum([lap["hr_trimp"] for lap in activity["laps"]])

    if activity["type"] == "Run":
        for lap in activity["laps"]:
            lap["pace_trimp"] = trimp_helpers.calculate_pace_trimp(
                lap["moving_time"],
                lap["pace_reserve"],
                user_settings["gender"],
                True,
            )
        activity["pace_trimp"] = sum([lap["pace_trimp"] for lap in activity["laps"]])

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

    # Set activity as calculated
    activity["custom_fields_calculated"] = True

    return activity


@bp.function_name(name="calculate_values_poison_queue")
@bp.queue_trigger(
    connection="AzureWebJobsStorage",
    arg_name="queue",
    queue_name="calculate-fields-queue-poison",
)
def calculate_values_poison_queue(
    queue: func.QueueMessage,
) -> None:
    """Handle poison message"""
    queue_helpers.handle_poison_message(queue, "calculate-fields-queue")
