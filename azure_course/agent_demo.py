"""Current Microsoft Agent Framework Azure routing; no silent provider fallback."""
import asyncio
import os
from .cloud_guard import require_effects, endpoint
from .cosmos_boundary import lookup_order


async def main() -> None:
    require_effects()
    from azure.identity.aio import ManagedIdentityCredential
    from agent_framework import Agent
    from agent_framework.openai import OpenAIChatClient
    async with ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"]) as credential:
        client = OpenAIChatClient(
            model=os.environ["APPROVED_DEPLOYMENT"],
            azure_endpoint=endpoint("AZURE_OPENAI_ENDPOINT", ".openai.azure.com"),
            credential=credential,
        )
        agent = Agent(client=client, name="orders-assistant",
                      instructions="Report only verified order status. Do not write orders.",
                      tools=[lookup_order])
        # Bounded by outer timeout; do not rerun tool effects after an unknown result.
        async with asyncio.timeout(30):
            response = await agent.run("Read status of order1; state your evidence.")
        print(str(response))


if __name__ == "__main__":
    asyncio.run(main())
