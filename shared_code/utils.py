"""General utility functions"""

import azure.functions as func


def get_unique_items(items: list, key_to_filter: str) -> list:
    """Get unique items from list of dictionaries by key"""
    output_list = []
    for item in items:
        output_list.append(item[key_to_filter])
    return list(dict.fromkeys(output_list))


def get_weighted_average(data: list, weight: list) -> float:
    """Get weighted average"""
    return float(sum(a * b for a, b in zip(data, weight)) / sum(weight))


def create_params_func_request(
    url: str, method: str, params: dict, body: dict | None = None
) -> func.HttpRequest:
    """Create func.HttpRequest"""

    query_string = ""
    for key, value in params.items():
        query_string += f"{key}={value}&"
    query_string = query_string[:-1]
    if query_string:
        query_string = f"?{query_string}"

    req = func.HttpRequest(
        method=method,
        url=f"{url}{query_string}",
        body=body,
        params=params,
    )

    return req
