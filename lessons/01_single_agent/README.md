# 01 — One agent

This is the smallest useful agent: one `Agent`, one instruction block, and one local model. It has no tools and cannot look up facts, so its main job is to explain why agents need access to reliable context.

The terminal loop is in `shared/cli.py`; the input is entered at runtime. Ask a question followed by a follow-up to see multi-turn history.
