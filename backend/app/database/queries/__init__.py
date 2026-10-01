"""Database query package for NexaTel.

Query modules are intentionally imported directly by handlers.

Keeping this package initializer free of eager imports prevents
unrelated domain-query modules from breaking one another when
their public query APIs evolve between implementation phases.
"""

__all__: list[str] = []