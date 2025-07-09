"""
Expose routers so parent package can import them easily.
"""

from .chat import router as chat            # noqa: F401
from .expert_opinion import router as expert_opinion   # noqa: F401
from .upload import router as upload        # noqa: F401
from .timeline import router as timeline    # noqa: F401
from .anatomy import router as anatomy      # noqa: F401
from .events import router as events        # noqa: F401
from .tools import router as tools          # noqa: F401
from .openai_compat import router as openai_compat  # noqa: F401
from .openai_compatible import router as openai_compatible  # noqa: F401
