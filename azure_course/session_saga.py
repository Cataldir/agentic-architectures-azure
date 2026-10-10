"""Finite Service Bus session/Cosmos teaching saga; no financial effects.

Three named step owners (inventory, payment, fulfillment) record synthetic effects.
Each state transition, effect record and outbox entry live in ONE Cosmos /id row.
Compare-and-swap protects concurrent updates. Service Bus remains a separate effect.
"""
from __future__ import annotations
import json
import os
from typing import Any
from .cloud_guard import require_effects
from .cosmos_boundary import container

OWNERS = {"reserve": "inventory", "charge": "payment", "ship": "fulfillment",
          "undo-charge": "payment", "undo-reserve": "inventory"}

def command(saga_id: str, tenant: str, step: str, number: int) -> dict[str, Any]:
    return {"id": f"{saga_id}-{number}", "saga_id": saga_id, "tenant": tenant,
            "operation": step, "owner": OWNERS[step]}

def initial(saga_id: str, tenant: str, *, failure: str = "ship") -> dict[str, Any]:
    if not saga_id.isascii() or not saga_id.isalnum() or len(saga_id) > 32:
        raise ValueError("bounded saga ID required")
    if failure not in {"none", "ship", "unknown-ship", "undo-charge"}:
        raise ValueError("unsupported teaching injection")
    if not tenant.isascii() or not tenant.isalnum() or len(tenant) > 64:
        raise ValueError("bounded tenant slug required")
    return {"id": saga_id, "tenant": tenant, "revision": 0, "state": "running",
            "failure": failure, "effects": [], "processed": [],
            "outbox": [{"payload": command(saga_id, tenant, "reserve", 1), "sent": False}]}

def apply(row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload) != {"id", "saga_id", "tenant", "operation", "owner"}:
        raise ValueError("invalid command shape")
    if any(not isinstance(value, str) or not 0 < len(value) <= 128
           for value in payload.values()):
        raise ValueError("invalid bounded command fields")
    if payload["saga_id"] != row["id"] or payload["tenant"] != row["tenant"]:
        raise PermissionError("saga/tenant mismatch")
    step = payload["operation"]
    if step not in OWNERS or payload["owner"] != OWNERS[step]:
        raise PermissionError("step owner mismatch")
    matching = [x for x in row["outbox"] if x["payload"]["id"] == payload["id"]]
    if len(matching) != 1 or matching[0]["payload"] != payload:
        raise ValueError("unissued or changed command")
    if payload["id"] in row["processed"]:
        return row
    result = json.loads(json.dumps(row))
    result["processed"].append(payload["id"])
    result["revision"] += 1
    following = None
    if result["state"] == "running":
        if step not in {"reserve", "charge", "ship"}:
            raise ValueError("unexpected compensation")
        if step == "ship" and result["failure"] == "unknown-ship":
            result["state"] = "reconcile"  # No guessed compensation.
        elif step == "ship" and result["failure"] != "none":
            result["state"] = "compensating"
            following = "undo-charge"
        else:
            result["effects"].append(step)
            following = {"reserve": "charge", "charge": "ship"}.get(step)
            if step == "ship":
                result["state"] = "succeeded"
    elif result["state"] == "compensating":
        expected = "undo-" + result["effects"][-1] if result["effects"] else None
        if step != expected:
            raise ValueError("compensation order mismatch")
        if step == "undo-charge" and result["failure"] == "undo-charge":
            result["state"] = "reconcile"
        else:
            result["effects"].pop()
            following = "undo-" + result["effects"][-1] if result["effects"] else None
            if not following:
                result["state"] = "compensated"
    else:
        raise ValueError("terminal saga refuses new effects")
    if following:
        result["outbox"].append({"payload": command(row["id"], row["tenant"],
                                  following, len(result["outbox"]) + 1), "sent": False})
    return result

def save(old: dict[str, Any], new: dict[str, Any]) -> None:
    from azure.core import MatchConditions
    body = {k: v for k, v in new.items() if not k.startswith("_")}
    container().replace_item(old["id"], body, etag=old["_etag"],
                             match_condition=MatchConditions.IfNotModified)
    # A 412 is a stale update, not permission to overwrite.

def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiveMode
    from azure.cosmos.exceptions import CosmosResourceExistsError
    saga_id = os.environ["COURSE_SAGA_ID"]
    tenant = os.environ["COURSE_TENANT"]
    namespace = os.environ["SERVICEBUS_FQDN"]
    if not namespace.endswith(".servicebus.windows.net") or "/" in namespace:
        raise ValueError("invalid namespace")
    queue = "course-sagas"
    store = container()
    seed = initial(saga_id, tenant, failure=os.environ.get("COURSE_FAILURE", "ship"))
    try:
        store.create_item(seed)
    except CosmosResourceExistsError:
        existing = store.read_item(saga_id, partition_key=saga_id)
        if existing["tenant"] != tenant or existing["failure"] != seed["failure"]:
            raise ValueError("changed saga initialization")
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    with ServiceBusClient(namespace, credential, retry_total=2, try_timeout=10) as client:
        with client.get_queue_sender(queue_name=queue) as sender:
            # A session must have a message before a receiver can lock it.
            row = store.read_item(saga_id, partition_key=saga_id)
            for entry in row["outbox"]:
                if not entry["sent"]:
                    payload = entry["payload"]
                    sender.send_messages(ServiceBusMessage(json.dumps(payload),
                        message_id=payload["id"], session_id=saga_id,
                        content_type="application/json"))
                    updated = json.loads(json.dumps(row))
                    for candidate in updated["outbox"]:
                        if candidate["payload"]["id"] == payload["id"]:
                            candidate["sent"] = True
                    save(row, updated)
                    row = store.read_item(saga_id, partition_key=saga_id)
            if row["state"] in {"succeeded", "compensated", "reconcile"}:
                print(json.dumps({k: row[k] for k in ("id", "revision", "state", "effects")}))
                return
            with client.get_queue_receiver(queue_name=queue, session_id=saga_id,
                    receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                    prefetch_count=0, max_wait_time=5) as receiver:
                # Strict finite teaching run. No infinite retry or autonomous escalation.
                for _ in range(12):
                    row = store.read_item(saga_id, partition_key=saga_id)
                    if row["tenant"] != tenant:
                        raise PermissionError("tenant mismatch")
                    for entry in row["outbox"]:
                        if not entry["sent"]:
                            payload = entry["payload"]
                            sender.send_messages(ServiceBusMessage(json.dumps(payload),
                                message_id=payload["id"], session_id=saga_id,
                                content_type="application/json"))
                            # Crash here: resend stable ID; broker duplicate window is bounded.
                            # Durable processed IDs still protect after that window expires.
                            updated = json.loads(json.dumps(row))
                            for candidate in updated["outbox"]:
                                if candidate["payload"]["id"] == payload["id"]:
                                    candidate["sent"] = True
                            save(row, updated)
                            row = store.read_item(saga_id, partition_key=saga_id)
                    if row["state"] in {"succeeded", "compensated", "reconcile"}:
                        print(json.dumps({k: row[k] for k in ("id", "revision", "state", "effects")}))
                        return
                    messages = receiver.receive_messages(max_message_count=1, max_wait_time=5)
                    for message in messages:
                        if len(str(message)) > 4096:
                            receiver.dead_letter_message(message, reason="oversized-command")
                            continue
                        try:
                            payload = json.loads(str(message))
                            if not isinstance(payload, dict) or str(message.message_id) != payload.get("id"):
                                raise ValueError("identity/shape mismatch")
                        except (ValueError, TypeError):
                            receiver.dead_letter_message(message, reason="identity-shape-mismatch")
                            continue
                        old = store.read_item(saga_id, partition_key=saga_id)
                        try:
                            updated = apply(old, payload)
                        except (ValueError, PermissionError):
                            receiver.dead_letter_message(message, reason="invalid-command")
                            continue
                        if updated != old:
                            save(old, updated)
                        # Unknown settlement propagates: durable effects survive redelivery.
                        receiver.complete_message(message)
                raise TimeoutError("finite saga budget exhausted; inspect durable row")

if __name__ == "__main__":
    main()

