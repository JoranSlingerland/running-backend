"""main Orchestrator function"""


import logging

import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    """Orchestrator function"""
    # step 0: Get user settings and latest activity date + id from cosmosdb
    logging.info("Getting user settings from cosmosdb")
    userid = context.get_input()[0]
    output = yield context.call_activity("act_get_user_settings", [userid])

    user_settings = output["user_settings"]
    latest_activity = output["latest_activity"]

    # step 1: get activities from strava from latest activity date + id
    logging.info("Getting activities from strava")
    output = yield context.call_activity(
        "act_get_activities", [latest_activity, user_settings]
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


main = df.Orchestrator.create(orchestrator_function)
