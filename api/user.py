"""User module"""
import json
import logging

import azure.functions as func

from shared_code import cosmosdb_module, schemas, utils

bp = func.Blueprint()


@bp.route(route="user", methods=["GET"])
def get_user(req: func.HttpRequest) -> func.HttpResponse:
    """Main function"""
    logging.info("Getting container data")

    userid = utils.get_user(req)["userId"]

    container = cosmosdb_module.cosmosdb_container("users")
    result = list(
        container.query_items(
            query="select * from c where c.id = @userid",
            parameters=[
                {"name": "@userid", "value": userid},
            ],
            enable_cross_partition_query=True,
        )
    )

    if len(result) != 1:
        return func.HttpResponse(
            body='{"status": "No data found"}',
            mimetype="application/json",
            status_code=400,
        )

    keys_to_pop = [
        "_rid",
        "_self",
        "_etag",
        "_attachments",
        "_ts",
        "id",
    ]
    for key in keys_to_pop:
        result[0].pop(key)

    return func.HttpResponse(
        body=json.dumps(result[0]), mimetype="application/json", status_code=200
    )


@bp.route(route="user", methods=["POST"])
async def post_user(req: func.HttpRequest) -> func.HttpResponse:
    """Add user data."""
    try:
        data = json.loads(req.get_body().decode("utf-8"))
    except Exception as ex:
        logging.error(ex)
        return func.HttpResponse(
            body='{"result": "Invalid json body"}',
            mimetype="application/json",
            status_code=400,
        )

    if utils.validate_json(data, schemas.user_data()):
        return utils.validate_json(data, schemas.user_data())

    userid = utils.get_user(req)["userId"]
    data["id"] = userid

    container = cosmosdb_module.cosmosdb_container("users")
    container.upsert_item(data)

    return func.HttpResponse(
        body='{"result": "done"}',
        mimetype="application/json",
        status_code=200,
    )
