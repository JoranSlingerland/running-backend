""""Queue api"""


import json
import logging

import azure.functions as func

from shared_code import cosmosdb_module, queue_helpers, user_helpers

bp = func.Blueprint()


@bp.route(route="queue/activities", methods=["POST"])
def queue_activities(req: func.HttpRequest) -> func.HttpResponse:
    """Main function"""
    logging.info("Getting container data")

    queue_name = req.params.get("queueName")
    activity_id = req.params.get("activityId")

    allowed_queues = [
        "enrichment-queue",
        "enrichment-queue-poison",
        "calculate-fields-queue",
        "calculate-fields-queue-poison",
    ]

    if queue_name not in allowed_queues:
        return func.HttpResponse(
            body='{"result": "Invalid queue name"}',
            mimetype="application/json",
            status_code=400,
        )

    userid = user_helpers.get_user(req)["userId"]

    query = "SELECT * FROM c WHERE c.userId = @userid"
    if activity_id:
        query += " AND c.id = @activityId"
    parameters = [
        {"name": "@userid", "value": userid},
        {"name": "@activityId", "value": activity_id},
    ]

    container = cosmosdb_module.cosmosdb_container("activities")
    activities = list(
        container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
    )

    queue_helpers.add_activity_to_enrichment_queue(activities, queue_name)

    result = {"queued": len(activities)}

    return func.HttpResponse(
        body=json.dumps(result), mimetype="application/json", status_code=200
    )
