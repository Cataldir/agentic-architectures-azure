"""Pinned official MCP SDK; read-only Cosmos tool, one identity per deployment."""
from .cloud_guard import require_effects
from .cosmos_boundary import lookup_order


def main() -> None:
    require_effects()
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("orders-read", host="0.0.0.0", port=8000,
                  stateless_http=True, json_response=True)

    @mcp.tool()
    def order_status(order_id: str) -> dict[str, str]:
        """Read status from the deployment's own domain; no tenant argument."""
        return lookup_order(order_id)

    # Private ACA ingress plus trusted gateway auth is a deployment precondition.
    # JSON responses deliberately exclude SSE streaming from this first exercise.
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
