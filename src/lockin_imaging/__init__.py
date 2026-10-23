"""General-purpose lock-in imaging; public examples use synthetic data only."""

from .core import DemodulationResult, LockinConfig, QualityFlag, demodulate

__version__ = "0.2.0"
__all__ = ["DemodulationResult", "LockinConfig", "QualityFlag", "demodulate"]
