"""Http start function"""

import contextlib
import json
import logging
from datetime import datetime, timedelta

import azure.durable_functions as df
import azure.functions as func

from shared_code import aio_helper, user_helpers

bp = df.Blueprint()


@bp.route(route="orchestrator/start", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def orchestrator_start(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    """Http Trigger"""

    function_name = req.params.get("functionName", None)

    if function_name != "orch_gather_data":
        return func.HttpResponse(
            '{"status": "Please pass a valid function name in the route parameters"}',
            status_code=400,
        )

    userid = user_helpers.get_user(req)["userId"]

    instance_id = await client.start_new(function_name, None, [userid])

    logging.info("Started orchestration with ID = '%s'.", instance_id)

    return client.create_check_status_response(req, instance_id)


@bp.route(route="orchestrator/terminate", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def orchestrator_terminate(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    """Terminate orchestration"""
    instance_id = req.params.get("instanceId", None)

    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instanceId"}), status_code=400
        )

    userid = user_helpers.get_user(req)["userId"]
    logging.info(f"Terminating orchestration with ID {instance_id}")

    status = await client.get_status(instance_id)
    try:
        status = status.to_json()
    except AttributeError:
        return func.HttpResponse(
            json.dumps({"status": "Instance not found"}),
            status_code=404,
            mimetype="application/json",
        )

    if userid not in status.get("input", ""):
        return func.HttpResponse(
            json.dumps({"status": "Not authorized to terminate this instance"}),
            status_code=401,
            mimetype="application/json",
        )

    if status["runtimeStatus"] in ["Completed", "Failed", "Terminated"]:
        return func.HttpResponse(
            json.dumps({"status": "Instance already terminated"}),
            status_code=200,
            mimetype="application/json",
        )

    try:
        await client.terminate(instance_id, "Killed by user")
    except Exception:
        return func.HttpResponse(
            json.dumps({"status": "Error terminating instance"}),
            status_code=500,
            mimetype="application/json",
        )
    return func.HttpResponse(
        json.dumps({"status": "Termination request send to instance"}),
        status_code=200,
        mimetype="application/json",
    )


@bp.route(route="orchestrator/purge", methods=["DELETE"])
@bp.durable_client_input(client_name="client")
async def orchestrator_purge(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    """Purge orchestration"""
    instance_id = req.params.get("instanceId", None)

    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instanceId"}), status_code=400
        )

    userid = user_helpers.get_user(req)["userId"]

    logging.info(f"Purging orchestration with ID {instance_id}")

    status = await client.get_status(instance_id)
    try:
        status = status.to_json()
    except AttributeError:
        return func.HttpResponse(
            json.dumps({"status": "Instance not found"}),
            status_code=404,
            mimetype="application/json",
        )

    if userid not in status.get("input", ""):
        return func.HttpResponse(
            json.dumps({"status": "Not authorized to purge this instance"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        status = await client.purge_instance_history(instance_id)
    except Exception:
        return func.HttpResponse(
            json.dumps({"status": "Error purging instance"}),
            status_code=500,
            mimetype="application/json",
        )
    if status.instances_deleted > 0:
        return func.HttpResponse(
            json.dumps({"status": "Instance purged"}),
            status_code=200,
            mimetype="application/json",
        )
    return func.HttpResponse(
        json.dumps({"status": "Instance could not be purged"}),
        status_code=500,
        mimetype="application/json",
    )


@bp.route(route="orchestrator/list", methods=["GET"])
@bp.durable_client_input(client_name="client")
async def orchestrator_list(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    """List all orchestrations"""
    logging.info("Getting all orchestrations")

    output = []
    days = req.params.get("days", None)
    end_date = datetime.today()

    if not days:
        return func.HttpResponse(json.dumps({"error": "Missing days"}), status_code=400)

    userid = user_helpers.get_user(req)["userId"]

    tasks = []
    for i in range(int(days)):
        start_date = end_date - timedelta(days=i + 1)
        end_date = end_date - timedelta(days=i)
        tasks.append(get_orchestrations(start_date, end_date, client, userid))

    output = await aio_helper.gather_with_concurrency(10, *tasks)
    output = [item for sublist in output for item in sublist]

    output.sort(key=lambda x: x["createdTime"], reverse=True)

    return func.HttpResponse(
        json.dumps(output), status_code=200, mimetype="application/json"
    )


async def get_orchestrations(
    start_date: datetime,
    end_date: datetime,
    client: df.DurableOrchestrationClient,
    userid: str,
) -> list:
    """Get orchestrations"""
    instances = await client.get_status_by(
        created_time_from=start_date, created_time_to=end_date
    )
    output = []
    for instance in instances:
        instance = instance.to_json()
        if instance["name"] == "orch_gather_data" and userid in instance["input"]:
            instance["createdTime"] = instance["createdTime"].replace("T", " ")
            instance["lastUpdatedTime"] = instance["lastUpdatedTime"].replace("T", " ")
            instance["createdTime"] = instance["createdTime"].replace(".000000Z", "")
            instance["lastUpdatedTime"] = instance["lastUpdatedTime"].replace(
                ".000000Z", ""
            )
            instance.pop("customStatus", None)
            instance.pop("history", None)
            instance.pop("name", None)
            instance.pop("input", None)
            output.append(instance)
            with contextlib.suppress(Exception):
                instance["output"] = json.loads(instance["output"])

    return output
