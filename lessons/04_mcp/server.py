import os
import sys
import logging
import warnings
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
os.environ.setdefault("FASTMCP_SHOW_SERVER_BANNER", "false")
os.environ.setdefault("FASTMCP_CHECK_FOR_UPDATES", "off")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

warnings.filterwarnings("ignore", message="authlib.jose module is deprecated")
logging.disable(logging.CRITICAL)
logging.getLogger("fastmcp").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)

from fastmcp import FastMCP

from shared.data import compare_financial_metric

mcp = FastMCP("northstar-finance")

@mcp.tool()
def compare_financials(metric: str, from_period: str, to_period: str) -> str:
    """Compare a reported Northstar bank metric between two periods."""
    return compare_financial_metric(metric, from_period, to_period)

if __name__ == "__main__":
    mcp.run(transport="stdio")
