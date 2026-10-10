"""Lab14 bounded worker: persist through Dapr, then settle queue delivery."""
import json
import os
import time
from urllib.request import Request, urlopen
from .cloud_guard import require_effects


def save_state(key: str, payload: str) -> None:
    body = json.dumps([{"key": key, "value": payload}]).encode()
    store = os.environ["DAPR_STATE_STORE"]
    if not store or not all(c.isalnum() or c == "-" for c in store):
        raise ValueError("invalid dedicated Dapr store")
    request = Request(f"http://127.0.0.1:3500/v1.0/state/{store}", data=body,
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        if response.status != 204:
            raise RuntimeError("state save unconfirmed")


def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    with ServiceBusClient(os.environ["SERVICEBUS_FQDN"], credential,
                          retry_total=2, try_timeout=10) as client:
        with client.get_queue_receiver(queue_name="tasks", prefetch_count=0,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK, max_wait_time=5) as receiver:
            # Container Apps can restart the process; idle scaler still controls replicas.
            stop = time.monotonic() + 300
            while time.monotonic() < stop:
                for message in receiver.receive_messages(max_message_count=1, max_wait_time=5):
                    if not message.message_id or len(str(message)) > 4096:
                        receiver.dead_letter_message(message, reason="invalid-contract")
                        continue
                    try:
                        payload = json.loads(str(message))
                        if (set(payload) != {"id", "tenant", "operation", "saga_id"}
                                or payload["tenant"] != os.environ["COURSE_TENANT"]
                                or payload["id"] != str(message.message_id)
                                or payload["operation"] != "reserve"):
                            raise ValueError("invalid teaching command")
                    except (ValueError, TypeError):
                        receiver.dead_letter_message(message, reason="invalid-contract")
                        continue
                    save_state(str(message.message_id), str(message))
                    receiver.complete_message(message)
                    print("saved-and-settled", str(message.message_id))
            # Idempotent Dapr key overwrites are this lab's whole effect. Later labs
            # require payload-conflict refusal and durable business idempotency.


if __name__ == "__main__":
    main()
