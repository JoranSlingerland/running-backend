"""Helper functions for azure queues"""

import json
import os
import uuid
from datetime import datetime
from functools import partial

from azure.functions import QueueMessage
from azure.storage.queue import QueueClient, TextBase64EncodePolicy

from shared_code import cosmosdb_module


def create_queue_client(queue_name: str) -> QueueClient:
    """Create queue client"""
    account_url = os.environ["AZUREWEBJOBSSTORAGE"]
    queue_client = QueueClient.from_connection_string(
        conn_str=account_url,
        queue_name=queue_name,
        message_encode_policy=TextBase64EncodePolicy(),
    )
    return queue_client


def add_activity_to_enrichment_queue(activities: dict, queue_name: str) -> dict:
    """Orchestrator function"""
    queue_client = create_queue_client(queue_name)

    for activity in activities:
        queue_client.send_message(
            json.dumps({"activity_id": activity["id"], "user_id": activity["userId"]})
        )

    return {"status": "success"}


def handle_poison_message(queue: QueueMessage, queue_name: str) -> None:
    """Handle poison message"""

    try:
        msg = queue.get_json()
    except Exception:
        msg = {"message": "Error parsing message", "user_id": "unknown"}

    try:
        user_id = msg["user_id"]
    except KeyError:
        user_id = "unknown"

    notification = {
        "id": str(uuid.uuid4()),
        "type": "enrichment",
        "status": "failed",
        "message": msg,
        "userId": user_id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "queue": queue_name,
    }

    container = cosmosdb_module.cosmosdb_container("notifications")
    cosmosdb_module.container_function_with_back_off(
        partial(
            container.upsert_item,
            notification,
        )
    )
