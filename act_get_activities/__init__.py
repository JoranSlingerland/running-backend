""""Get Stock data orchestrator function"""

from shared_code import strava_helpers


def main(payload: str) -> dict:
    """Orchestrator function"""

    # initialize variables
    latest_activity = payload[0]
    user_settings = payload[1]

    (
        client,
        user_settings,
    ) = strava_helpers.create_strava_client(user_settings)

    if not latest_activity["id"] or not latest_activity["start_date"]:
        activities = client.get_activities()

    else:
        activities = client.get_activities(
            after=latest_activity["start_date"],
        )

    activities_list = [activity.dict() for activity in activities]

    # Convert start_date and end_date from datetime to string
    for activity in activities_list:
        activity["start_date"] = activity["start_date"].strftime("%Y-%m-%d %H:%M:%S")
        activity["start_date_local"] = activity["start_date_local"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    return {
        "activities": activities_list,
        "user_settings": user_settings,
    }
