"""Send one bounded synthetic teaching command with an attached managed identity."""
import json
import os
from .cloud_guard import require_effects

def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
    namespace = os.environ["SERVICEBUS_FQDN"]
    if not namespace.endswith(".servicebus.windows.net") or "/" in namespace:
        raise ValueError("invalid namespace")
    message_id = os.environ.get("COURSE_MESSAGE_ID", "lab14-one")
    if not message_id.isalnum() and not all(c.isalnum() or c == "-" for c in message_id):
        raise ValueError("invalid message ID")
    if not 1 <= len(message_id) <= 64:
        raise ValueError("bounded message ID required")
    payload = {"id": message_id, "tenant": os.environ["COURSE_TENANT"],
               "operation": "reserve", "saga_id": "lab14"}
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    with ServiceBusClient(namespace, credential, retry_total=2, try_timeout=10) as client:
        with client.get_queue_sender(queue_name=os.environ["SERVICEBUS_QUEUE"]) as sender:
            sender.send_messages(ServiceBusMessage(json.dumps(payload),
                message_id=message_id, content_type="application/json"))
    print("broker send accepted; this does not prove worker completion")

if __name__ == "__main__":
    main()

