"""Business logic layer for NexaTel.

This package contains deterministic business rules that sit between
the application handlers and the database query layer.

Business logic must:
- operate only on verified backend data,
- never call the LLM,
- never construct SQL,
- never make authorization decisions based on LLM output,
- remain deterministic and testable.
"""