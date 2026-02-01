"""DAN Memory v2 package (Neo4j-backed).

This package implements the v2 design described in `memory/arc.md`.
Reflection features are intentionally out of scope here.
"""

from .constants import ATOM_LABEL, LINK_REL_TYPE

__all__ = ["ATOM_LABEL", "LINK_REL_TYPE"]
