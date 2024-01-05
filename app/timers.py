"""Module contains all the timer functions for the application"""

import azure.functions as func

from shared_code import cosmosdb_module, queue_helpers

bp = func.Blueprint()


@bp.timer_trigger(
    schedule="0 0 0 * * *", arg_name="timer", run_on_startup=False, use_monitor=False
)
def enqueue_non_enriched_activities(timer: func.TimerRequest) -> None:
    """Will add any none enriched activities to the enrichment queue"""
    container = cosmosdb_module.cosmosdb_container("activities")
    activities = container.query_items(
        query="SELECT * FROM c WHERE c.full_data = false",
        enable_cross_partition_query=True,
    )
    queue_helpers.add_activity_to_enrichment_queue(activities, "enrichment-queue")


@bp.timer_trigger(
    schedule="0 0 0 * * *", arg_name="timer", run_on_startup=False, use_monitor=False
)
def enqueue_non_calculated_activities(timer: func.TimerRequest) -> None:
    """Will add any none enriched activities to the enrichment queue"""
    container = cosmosdb_module.cosmosdb_container("activities")
    activities = container.query_items(
        query="SELECT * FROM c WHERE c.custom_fields_calculated = false AND c.full_data = true",
        enable_cross_partition_query=True,
    )
    queue_helpers.add_activity_to_enrichment_queue(activities, "calculate-fields-queue")
