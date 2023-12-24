"""Get required environment variables"""

# Imports
import os

from dotenv import load_dotenv


# functions
def get_cosmosdb() -> dict[str, str]:
    """Get cosmosdb"""

    load_dotenv()

    return {
        "endpoint": os.environ["COSMOSDB_ENDPOINT"],
        "key": os.environ["COSMOSDB_KEY"],
        "database": os.environ["COSMOSDB_DATABASE"],
    }


def get_strava_auth() -> dict[str, str]:
    """Get strava auth"""

    load_dotenv()

    return {
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
    }
