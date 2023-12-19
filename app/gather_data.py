"""Gather data orchestration and activity functions"""

import logging

import azure.durable_functions as df

from shared_code import cosmosdb_module, strava_helpers

bp = df.Blueprint()


@bp.orchestration_trigger(context_name="context")
def orch_gather_data(context: df.DurableOrchestrationContext):
    """Orchestrator function"""
    # step 0: Get user settings and latest activity date + id from cosmosdb
    logging.info("Getting user settings from cosmosdb")
    userid = context.get_input()[0]
    output = yield context.call_activity("get_user_settings", [userid])

    user_settings = output["user_settings"]
    latest_activity = output["latest_activity"]

    # step 1: get activities from strava from latest activity date + id
    logging.info("Getting activities from strava")
    output = yield context.call_activity(
        "get_activities", [latest_activity, user_settings]
    )

    activities = output["activities"]
    user_settings = output["user_settings"]

    # step 3: get detailed activity data from strava

    # step 4: get activity streams from strava

    # step 5: save activity data to cosmosdb
    logging.info("Saving activities to cosmosdb")
    provisioning_tasks = []
    id_ = 0
    child_id = f"{context.instance_id}:{id_}"
    provision_task = context.call_sub_orchestrator(
        "sub_orch_output_to_cosmosdb",
        [{"activities": activities}],
        child_id,
    )
    provisioning_tasks.append(provision_task)
    output = (yield context.task_all(provisioning_tasks))[0]

    return output


@bp.activity_trigger(input_name="payload")
def get_user_settings(payload: str) -> dict:
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
            "start_date": latest_activity[0]["start_date"] if latest_activity else None,
        },
    }


@bp.activity_trigger(input_name="payload")
def get_activities(payload: str) -> dict:
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

    for activity in activities_list:
        activity["start_date"] = activity["start_date"].strftime("%Y-%m-%dT%H:%M:%SZ")
        activity["start_date_local"] = activity["start_date_local"].strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        activity["id"] = str(activity["id"])
        activity["userId"] = user_settings["id"]
        activity["full_data"] = False
        activity.pop("athlete")
        activity.pop("splits_standard")

    return {
        "activities": activities_list,
        "user_settings": user_settings,
    }
