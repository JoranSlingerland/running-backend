"""main Orchestrator function"""


import logging

import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    """Orchestrator function"""
    # step 0: get the input
    logging.info("Step 0")
    return "Done"


main = df.Orchestrator.create(orchestrator_function)
