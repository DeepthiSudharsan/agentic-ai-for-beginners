from functools import lru_cache

@lru_cache(maxsize=128)
def cached_answer(question: str, context_version: str = "finance-v1") -> str:
    """Cache only approved-safe answers; include context version in the key."""
    print("Computing answer once...")
    return f"Cached placeholder for: {question} ({context_version})"

if __name__ == "__main__":
    print(cached_answer("What was Q2 revenue?"))
    print(cached_answer("What was Q2 revenue?"))
