from mcp.server.fastmcp import FastMCP

from shared.data import compare_financial_metric

mcp = FastMCP("northstar-finance")

@mcp.tool()
def compare_financials(metric: str, from_period: str, to_period: str) -> str:
    """Compare a reported Northstar bank metric between two periods."""
    return compare_financial_metric(metric, from_period, to_period)

if __name__ == "__main__":
    mcp.run(transport="stdio")
