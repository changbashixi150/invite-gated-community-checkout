"""Compatibility import for running the repository without installation.

The implementation is kept in ``src``; this module makes the documented
``from onboarding_service import ...`` import work when pytest is run
directly from the repository root.
"""

from src.onboarding_service import *

