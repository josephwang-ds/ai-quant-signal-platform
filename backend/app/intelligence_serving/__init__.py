"""Read-only intelligence query serving layer (Phase 4.5)."""

from app.intelligence_serving.deps import get_intelligence_service
from app.intelligence_serving.service import IntelligenceService

__all__ = [
    "IntelligenceService",
    "get_intelligence_service",
]
