"""Registry of mutation strategies. Add new strategy modules here to wire
them into the CLI's --strategies flag without touching the engine.
"""
from .base import MutationStrategy, MutationContext
from .session_swap import SessionSwapStrategy
from .object_id_swap import ObjectIdSwapStrategy

STRATEGIES: dict[str, type[MutationStrategy]] = {
    SessionSwapStrategy.name: SessionSwapStrategy,
    ObjectIdSwapStrategy.name: ObjectIdSwapStrategy,
}

__all__ = ["MutationStrategy", "MutationContext", "STRATEGIES"]
