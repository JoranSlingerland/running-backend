"""Entry point for Azure Functions."""

import azure.functions as func

from callback import bp as callback_bp
from gather_data import bp as gather_data_bp
from orchestrator import bp as orchestrator_bp
from output_to_cosmosdb import bp as output_to_cosmosdb_bp
from user import bp as user_bp

app = func.FunctionApp()


def main():
    """Main function."""
    blueprints = [
        user_bp,
        callback_bp,
        orchestrator_bp,
        gather_data_bp,
        output_to_cosmosdb_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


main()
