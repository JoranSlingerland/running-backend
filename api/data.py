"""Function to query cosmosDB for container data"""

import json
import logging

import azure.functions as func

from shared_code import cosmosdb_module, user_helpers

bp = func.Blueprint()


@bp.route(route="data/activities", methods=["GET"])
def list_activities(req: func.HttpRequest) -> func.HttpResponse:
    """Main function"""
    logging.info("Getting container data")

    start_date = req.params.get("startDate")
    end_date = req.params.get("endDate")

    query = "SELECT * FROM c WHERE c.userId = @userid"
    if start_date:
        query += " AND c.start_date >= @startDate"
    if end_date:
        query += " AND c.start_date <= @endDate"

    userid = user_helpers.get_user(req)["userId"]

    container = cosmosdb_module.cosmosdb_container("activities")
    result = list(
        container.query_items(
            query=query,
            parameters=[
                {"name": "@userid", "value": userid},
                {"name": "@startDate", "value": start_date},
                {"name": "@endDate", "value": end_date},
            ],
            enable_cross_partition_query=True,
        )
    )

    if not result:
        return func.HttpResponse(
            body="{[]}",
            mimetype="application/json",
            status_code=200,
        )

    keys_to_pop = [
        "_rid",
        "_self",
        "_etag",
        "_attachments",
        "_ts",
    ]
    for key in keys_to_pop:
        result[0].pop(key)

    return func.HttpResponse(
        body=json.dumps(result), mimetype="application/json", status_code=200
    )
