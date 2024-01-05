"""Entry point for Azure Functions."""

import azure.functions as func

from api.callback import bp as callback_bp
from api.data import bp as data_bp
from api.orchestrator import bp as orchestrator_bp
from api.queue import bp as queue_bp
from api.user import bp as user_bp
from app.calculate_fields import bp as calculate_fields_bp
from app.enrich_data import bp as enrich_data_bp
from app.gather_data import bp as gather_data_bp
from app.output_to_cosmosdb import bp as output_to_cosmosdb_bp
from app.timers import bp as timers_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def main():
    """Main function."""
    blueprints = [
        callback_bp,
        data_bp,
        orchestrator_bp,
        queue_bp,
        user_bp,
        calculate_fields_bp,
        enrich_data_bp,
        gather_data_bp,
        output_to_cosmosdb_bp,
        timers_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


main()
