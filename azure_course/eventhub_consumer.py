"""Process before checkpoint; duplicate effects remain a sink responsibility."""
import os
from threading import Timer
from .cloud_guard import require_effects, endpoint


def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.eventhub import EventHubConsumerClient
    from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    store = BlobCheckpointStore(blob_account_url=endpoint("CHECKPOINT_BLOB_URL", ".blob.core.windows.net"),
                                container_name="checkpoints", credential=credential)
    client = EventHubConsumerClient(fully_qualified_namespace=os.environ["EVENTHUB_FQDN"],
            eventhub_name="telemetry", consumer_group="course-audit", credential=credential,
            checkpoint_store=store)

    def on_event(context, event) -> None:
        if event is None:
            return
        # Demonstration sink is a print; neither atomic nor durable business state.
        # A production sink commits event-ID dedup and effect before this call.
        print(context.partition_id, event.sequence_number)  # No event body logging.
        context.update_checkpoint(event)

    stop = Timer(60, client.close)  # Future runner must verify close/termination.
    stop.daemon = True
    try:
        with client:
            stop.start()
            client.receive(on_event=on_event, starting_position="-1", max_wait_time=5)
    finally:
        stop.cancel()
        client.close()


if __name__ == "__main__":
    main()
