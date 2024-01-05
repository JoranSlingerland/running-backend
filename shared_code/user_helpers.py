"""Helper functions for getting user data"""

import base64
import json

import azure.functions as func


def get_user(
    req: func.HttpRequest,
) -> dict[str, str | list[str]]:
    """Get user from request"""

    headers = req.headers.get("x-ms-client-principal", None)
    if headers:
        headers = base64.b64decode(headers).decode("ascii")
        headers = json.loads(headers)

    return headers
