"""Output to CosmosDB orchestrator and activity functions"""

import logging
from functools import partial

import azure.durable_functions as df

from shared_code import aio_helper, cosmosdb_module

bp = df.Blueprint()


@bp.orchestration_trigger(context_name="context")
def sub_orch_output_to_cosmosdb(context: df.DurableOrchestrationContext):
    """Orchestrator function"""
    data = context.get_input()[0]

    result = {"status": "No data to process"}

    for container_name, items in data.items():
        items = [items[i : i + 5000] for i in range(0, len(items), 5000)]
        for batch in items:
            result = yield context.call_activity(
                "output_to_cosmosdb", [container_name, batch]
            )

    return result


@bp.activity_trigger(input_name="payload")
async def output_to_cosmosdb(payload: str) -> str:
    """Function to output data to CosmosDB"""

    # suppress logger output
    logger = logging.getLogger("azure")
    logger.setLevel(logging.CRITICAL)

    # get config
    container_name = payload[0]
    items = payload[1]

    logging.info(f"Outputting to container {container_name}")

    tasks = []
    container = cosmosdb_module.cosmosdb_container(container_name)

    for item in items:
        # fill event loop list
        tasks.append(
            cosmosdb_module.container_function_with_back_off(
                partial(container.create_item, item)
            )
        )

    await aio_helper.gather_with_concurrency(50, *tasks)

    return '{"status": "Done"}'
