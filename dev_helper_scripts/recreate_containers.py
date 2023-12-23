"""Recreate all containers."""

import logging
import os
import sys

from azure.cosmos import PartitionKey

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from shared_code import cosmosdb_module  # noqa: E402


def main():
    """Recreate all containers."""
    delete_critical_containers = False
    delete_critical_containers_user_input = input(
        "Do you want to delete critical containers? (default is False) [y/N]: "
    ).lower()
    containers = [
        {
            "name": "activities",
            "partition_key": "/id",
            "critical": False,
        },
        {
            "name": "streams",
            "partition_key": "/id",
            "critical": False,
        },
        {
            "name": "users",
            "partition_key": "/id",
            "critical": True,
        },
        {
            "name": "notifications",
            "partition_key": "/id",
            "critical": False,
        },
    ]

    if delete_critical_containers_user_input == "y":
        delete_critical_containers = True

    cosmosdb_database = cosmosdb_module.cosmosdb_database()
    for container in containers:
        if container["critical"] and not delete_critical_containers:
            continue
        try:
            logging.info(f"Deleting container {container['name']}")
            cosmosdb_database.delete_container(container["name"])
        except Exception:
            logging.debug("Container does not exist")
        logging.info(f"Creating container {container['name']}")
        cosmosdb_database.create_container(
            id=container["name"],
            partition_key=PartitionKey(path=container["partition_key"]),
        )

    logging.info("Done")


if __name__ == "__main__":
    main()
