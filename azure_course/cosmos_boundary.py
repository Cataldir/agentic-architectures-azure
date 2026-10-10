"""Named Cosmos operations; runtime identity is scoped to the owned orders DB."""
from __future__ import annotations
import os
from typing import Any
from .cloud_guard import require_effects, endpoint


def container() -> Any:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.cosmos import CosmosClient
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    client = CosmosClient(endpoint("COSMOS_ENDPOINT", ".documents.azure.com"),
                          credential=credential)
    return client.get_database_client("orders").get_container_client("state")


def lookup_order(order_id: str) -> dict[str, str]:
    if not order_id.isascii() or not order_id.isalnum() or len(order_id) > 64:
        raise ValueError("bounded order ID required")
    item = container().read_item(item=order_id, partition_key=order_id)
    if item.get("tenant") != os.environ["COURSE_TENANT"]:
        raise PermissionError("stored order tenant differs")
    return {"id": str(item["id"]), "status": str(item["status"])}


def main() -> None:
    # A readable seeded row proves authorization only for the selected identity/path.
    print(lookup_order(os.environ.get("COURSE_ORDER_ID", "order1")))


if __name__ == "__main__":
    main()
