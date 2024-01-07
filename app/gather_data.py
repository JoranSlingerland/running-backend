"""Gather data orchestration and activity functions"""

import logging

import azure.durable_functions as df

from shared_code import cosmosdb_module, queue_helpers, strava_helpers, user_helpers

bp = df.Blueprint()


@bp.orchestration_trigger(context_name="context")
def orch_gather_data(context: df.DurableOrchestrationContext):
    """Orchestrator function"""
    # step 1: Get user settings and latest activity date + id from cosmosdb
    logging.info("Step 1: Getting user settings from cosmosdb")
    userid = context.get_input()[0]
    output = yield context.call_activity("get_user_settings", [userid])

    user_settings = output["user_settings"]
    latest_activity = output["latest_activity"]

    # step 2: get activities from strava from latest activity date + id
    logging.info("Step 2: Getting activities from strava")
    output = yield context.call_activity(
        "get_activities", [latest_activity, user_settings]
    )

    activities = output["activities"]
    user_settings = output["user_settings"]

    # step 3: save activity data to cosmosdb
    logging.info("Step 3: Saving activities to cosmosdb")
    provisioning_tasks = []
    id_ = 1
    child_id = f"{context.instance_id}:{id_}"
    provision_task = context.call_sub_orchestrator(
        "sub_orch_output_to_cosmosdb",
        [{"activities": activities}],
        child_id,
    )
    provisioning_tasks.append(provision_task)
    output = (yield context.task_all(provisioning_tasks))[0]

    # step 4: add activity id to enrichment queue
    logging.info("Step 4: Adding activity id to enrichment queue")
    yield context.call_activity(
        "add_activity_to_enrichment_queue", [activities, "enrichment-queue"]
    )

    return {"status": "success", "ActivitiesAdded": len(activities)}


@bp.activity_trigger(input_name="payload")
def get_user_settings(payload: str) -> dict:
    """Get user data and strava client"""
    logging.info("Getting user data + strava client")

    # suppress logger output
    logger = logging.getLogger("azure")
    logger.setLevel(logging.CRITICAL)

    userid = payload[0]

    parameters = [{"name": "@userid", "value": userid}]

    user_settings = user_helpers.get_user_settings(userid)

    latest_activity = cosmosdb_module.get_cosmosdb_items(
        "SELECT top 1 * FROM c WHERE c.userId = @userid ORDER BY c.start_date DESC",
        parameters,
        "activities",
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
        activity = strava_helpers.cleanup_activity(
            activity, user_settings["id"], False, False
        )

    return {
        "activities": activities_list,
        "user_settings": user_settings,
    }


@bp.activity_trigger(input_name="payload")
def add_activity_to_enrichment_queue(payload: str) -> dict:
    """Orchestrator function"""

    activities = payload[0]
    queue_name = payload[1]

    status = queue_helpers.add_activity_to_enrichment_queue(activities, queue_name)

    return status
