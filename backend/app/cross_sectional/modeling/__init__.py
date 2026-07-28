"""Phase 3 cross-sectional modeling package."""

__all__ = [
    "CrossSectionalModelingError",
    "CrossSectionalModelingService",
]


def __getattr__(name: str):
    if name in __all__:
        from app.cross_sectional.modeling.service import (
            CrossSectionalModelingError,
            CrossSectionalModelingService,
        )

        return {
            "CrossSectionalModelingError": CrossSectionalModelingError,
            "CrossSectionalModelingService": CrossSectionalModelingService,
        }[name]
    raise AttributeError(name)
