"""PeekLock consumer with durable same-partition teaching effects in Cosmos."""
from __future__ import annotations
import json
import os
from .cloud_guard import require_effects
from .cosmos_boundary import container


def process_once(message_id: str, payload: dict[str, str]) -> None:
    """One row is both effect and dedup marker: suitable for this bounded lesson.

    This is not an atomic transaction with arbitrary external tools or Service Bus.
    Conflict verifies payload equality. Ambiguous writes are reconciled by readback.
    """
    from azure.cosmos.exceptions import CosmosResourceExistsError
    required = {"id", "tenant", "operation", "saga_id"}
    if set(payload) != required or not all(isinstance(v, str) and 0 < len(v) <= 128
                                            for v in payload.values()):
        raise ValueError("invalid bounded command")
    if payload["tenant"] != os.environ["COURSE_TENANT"]:
        raise PermissionError("tenant mismatch")
    if payload["operation"] not in {"reserve", "charge", "ship", "undo-reserve", "undo-charge"}:
        raise ValueError("unknown command")
    if message_id != payload["id"]:
        raise ValueError("message/body identity mismatch")
    store = container()
    body = {**payload, "status": "recorded-teaching-effect"}
    try:
        store.create_item(body)
    except CosmosResourceExistsError:
        old = store.read_item(payload["id"], partition_key=payload["id"])
        if any(old.get(k) != v for k, v in body.items()):
            raise ValueError("idempotency key reused with changed payload")


def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode
    from azure.servicebus.exceptions import MessageLockLostError
    ns = os.environ["SERVICEBUS_FQDN"]
    if not ns.endswith(".servicebus.windows.net") or "/" in ns:
        raise ValueError("invalid namespace")
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    with ServiceBusClient(ns, credential, retry_total=2, try_timeout=10) as client:
        with client.get_queue_receiver(queue_name=os.environ["SERVICEBUS_QUEUE"],
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK, prefetch_count=0,
                max_wait_time=5) as receiver:
            for message in receiver.receive_messages(max_message_count=1, max_wait_time=5):
                try:
                    process_once(str(message.message_id), json.loads(str(message)))
                except (ValueError, PermissionError, json.JSONDecodeError):
                    receiver.dead_letter_message(message, reason="invalid-contract")
                    continue
                # Other errors propagate without completion. A later delivery reconciles.
                try:
                    receiver.complete_message(message)
                except MessageLockLostError:
                    print("settlement unconfirmed; effect remains durable; reconcile on redelivery")


if __name__ == "__main__":
    main()
