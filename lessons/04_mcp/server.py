from mcp.server.fastmcp import FastMCP

from shared.data import revenue_growth

mcp = FastMCP("northstar-finance")

@mcp.tool()
def compare_revenue(from_period: str, to_period: str) -> str:
    """Compare Northstar revenue between two periods."""
    return revenue_growth(from_period, to_period)

if __name__ == "__main__":
    mcp.run(transport="stdio")
