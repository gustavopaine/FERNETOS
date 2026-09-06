"""
Motor de cálculo para Campari casero: receta real de referencia (batch de
1.5L), cuarto producto del sistema (Fernet, Gancia, Americano, Campari).
Estructura paralela a calculator_americano.py (infusión directa: alcohol
+ agua, sin base vínica) - comparten únicamente el balance de alcohol
puro vía modules.ensamblaje.common, no una clase base.

A diferencia de Americano, esta receta no tiene capa de variantes
experimentales todavía: es la receta base con cantidades exactas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from modules.tinturas.models import ComposicionBotanica, ControlCalidad
from modules.ensamblaje.common import abv_resultante


@dataclass
class ComposicionCampari:
    """Composición de un lote de Campari (infusión directa + dilución)"""

    alcohol_ml: float = 0.0
    alcohol_abv: float = 40.0
    agua_ml: float = 0.0
    azucar_g: float = 0.0
    ingredientes_maceracion: List[ComposicionBotanica] = field(default_factory=list)
    # Hibiscus u otros botánicos que se suman recién en los últimos días
    # de maceración (aporte de color, no se maceran todo el tiempo).
    ingredientes_incorporacion_tardia: List[ComposicionBotanica] = field(
        default_factory=list
    )

    @property
    def volumen_final_ml(self) -> float:
        return self.alcohol_ml + self.agua_ml


@dataclass
class CampariBlendResult:
    """Resultado de un cálculo de blend de Campari"""

    composicion: ComposicionCampari
    abv_calculado: float = 0.0
    azucar_efectiva_gpl: float = 0.0
    control_calidad: Optional[ControlCalidad] = None
    fecha_calculo: datetime = field(default_factory=datetime.now)


class CampariCalculator:
    """
    Calculadora para Campari por infusión directa. Igual que Americano:
    todo el alcohol viene de una sola fuente (vodka/alcohol de cereal a
    40°), sin fortificación por separado ni base vínica.
    """

    @staticmethod
    def calcular_abv(composicion: ComposicionCampari) -> float:
        """
        ABV de la infusión: alcohol diluido en el volumen final (alcohol +
        agua). Azúcar y botánicos (maceración e incorporación tardía) no
        aportan alcohol y no entran en este cálculo.

        Returns:
            float: ABV resultante
        """
        return abv_resultante(
            [(composicion.alcohol_ml, composicion.alcohol_abv)],
            composicion.volumen_final_ml,
        )

    @staticmethod
    def calcular_azucar_efectiva_gpl(azucar_g: float, volumen_final_ml: float) -> float:
        """
        Gramos de azúcar por litro del blend final, para verificar contra
        un ratio de referencia conocido (ej. 150 g/L).

        Returns:
            float: g/L. 0.0 si volumen_final_ml es 0.
        """
        if volumen_final_ml == 0:
            return 0.0
        return azucar_g / (volumen_final_ml / 1000)

    @staticmethod
    def calcular_blend(
        composicion: ComposicionCampari,
        control_calidad: Optional[ControlCalidad] = None,
    ) -> CampariBlendResult:
        """
        Arma el resultado completo de un blend de Campari.

        control_calidad es un dato medido (ej. densidad con densímetro),
        no algo que se derive de la receta - se guarda tal cual se pasa,
        nunca se recalcula a partir de alcohol/azúcar/botánicos.

        Returns:
            CampariBlendResult
        """
        return CampariBlendResult(
            composicion=composicion,
            abv_calculado=CampariCalculator.calcular_abv(composicion),
            azucar_efectiva_gpl=CampariCalculator.calcular_azucar_efectiva_gpl(
                composicion.azucar_g, composicion.volumen_final_ml
            ),
            control_calidad=control_calidad,
        )
