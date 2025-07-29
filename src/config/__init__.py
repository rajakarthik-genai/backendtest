"""Compatibility shim for legacy imports in tests.
Exports `settings` from new `src.core.config` so old code/tests importing
`from src.core.config import settings` continue to work.
This can be removed once all references are updated.
"""

from src.core.config import settings

__all__ = ["settings"]
