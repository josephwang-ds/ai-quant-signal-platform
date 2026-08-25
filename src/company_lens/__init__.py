"""Source-backed company intelligence for ordinary investors.

The package deliberately keeps calculation, document extraction, and explanation
separate.  Numbers come from deterministic code; an LLM is an optional renderer.
"""

from company_lens.snapshots.builder import build_snapshot, build_snapshots

__all__ = ["build_snapshot", "build_snapshots"]
