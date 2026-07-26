"""Research execution package."""

# Keep package import side-effect free so submodules (e.g. market_data_port)
# can load without pulling the application service and creating import cycles
# with research_reproducibility.
__all__: list[str] = []
