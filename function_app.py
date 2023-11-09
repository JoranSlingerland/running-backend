"""Entry point for Azure Functions."""

import azure.functions as func

from api.callback import bp as callback_bp
from api.data import bp as data_bp
from api.orchestrator import bp as orchestrator_bp
from api.user import bp as user_bp
from app.gather_data import bp as gather_data_bp
from app.output_to_cosmosdb import bp as output_to_cosmosdb_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def main():
    """Main function."""
    blueprints = [
        user_bp,
        callback_bp,
        orchestrator_bp,
        gather_data_bp,
        output_to_cosmosdb_bp,
        data_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


main()
