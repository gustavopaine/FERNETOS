"""
Punto de entrada único para obtener la calculadora de una familia.
"""

from typing import Optional

from core.validators import FAMILIAS_COMPATIBLES_VALIDAS
from families.fernet.calculator import FernetCalculator
from families.gancia.gancia_calculator import GanciaCalculator
from families.gancia.americano_calculator import AmericanoCalculator
from families.campari.campari_calculator import CampariCalculator


class RecipeEngineFactory:
    """
    "americano" es el nombre público de la familia (ver decisión en
    docs/specs/2026-09-06-americano-variantes-experimentales.md:
    Producto.GANCIA no se renombra internamente, pero la categoría
    pública es "americano"). La familia "americano" tiene dos métodos de
    formulación que coexisten: infusión directa (default, la receta real
    confirmada) y vínica (explícito vía metodo="vinica").
    """

    @staticmethod
    def create(familia: str, metodo: Optional[str] = None):
        if familia == "fernet":
            return FernetCalculator()
        if familia == "americano":
            if metodo == "vinica":
                return GanciaCalculator()
            return AmericanoCalculator()
        if familia == "campari":
            return CampariCalculator()
        raise ValueError(
            f"Familia desconocida: '{familia}'. "
            f"Válidas: {sorted(FAMILIAS_COMPATIBLES_VALIDAS)}"
        )
