"""Http start function"""

import logging

import azure.durable_functions as df
import azure.functions as func

from shared_code import utils


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """Http Trigger"""
    client = df.DurableOrchestrationClient(starter)

    function_name = req.params.get("functionName", None)

    if function_name != "orch_gather_data":
        return func.HttpResponse(
            '{"status": "Please pass a valid function name in the route parameters"}',
            status_code=400,
        )

    userid = utils.get_user(req)["userId"]

    instance_id = await client.start_new(function_name, None, [userid])

    logging.info("Started orchestration with ID = '%s'.", instance_id)

    return client.create_check_status_response(req, instance_id)
