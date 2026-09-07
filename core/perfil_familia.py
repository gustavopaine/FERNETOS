"""
Perfil técnico y sensorial objetivo de una familia de producto.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PerfilFamilia:
    """Rango técnico y perfil sensorial objetivo de una familia de producto."""

    nombre: str
    abv_min: Optional[float]
    abv_max: Optional[float]
    abv_default: Optional[float]
    descripcion_sensorial: str
