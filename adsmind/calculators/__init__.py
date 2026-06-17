"""
Calculator backend abstraction module.

This module provides a unified interface for different atomistic simulation calculators
(MACE, OpenMD, DeePMD-kit, etc.) while preserving ASE compatibility.

Usage:
    from adsmind.calculators import get_backend, CalculatorConfig

    backend = get_backend("mace")  # or from env: os.getenv("ADSMIND_BACKEND", "mace")
    config = CalculatorConfig(device="cpu", model="small")
    calc = backend.get_calculator(config)
"""

from adsmind.calculators.base import BaseBackend, CalculatorConfig
from adsmind.calculators.factory import get_backend, get_available_backends

__all__ = [
    "BaseBackend",
    "CalculatorConfig",
    "get_backend",
    "get_available_backends",
]
