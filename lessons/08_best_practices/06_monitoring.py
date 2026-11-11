"""Optional Langfuse wiring, kept out of the core lessons."""
try:
    from langfuse import get_client
except ImportError:
    get_client = None

if __name__ == "__main__":
    if get_client is None:
        print("Langfuse is optional. Install it later with: uv pip install langfuse")
    else:
        print("Langfuse is installed; configure its environment variables only when you are ready.")
