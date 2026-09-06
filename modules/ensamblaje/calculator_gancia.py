"""
Motor de cálculo para ensamblaje de Gancia.
Base vínica real (vino + fortificación con alcohol neutro), estructura
paralela a FernetCalculator pero sin heredar de él: los parámetros no
comparten forma (vino+fortificación vs alcohol+agua). Comparten únicamente
el balance de alcohol puro, vía modules.ensamblaje.common.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple
from datetime import datetime
import uuid

from modules.tinturas.models import Tintura
from modules.ensamblaje.common import abv_resultante


@dataclass
class GanciaBlendParams:
    """Parámetros base para un blend de Gancia"""

    volumen_objetivo_litros: float
    abv_objetivo: float = 17.0  # rango 15-18
    vino_pct: float = 0.78  # rango 0.75-0.80
    vino_abv: float = 12.0
    alcohol_fortificacion_abv: float = 96.0
    azucar_pct_wv: float = 10.0  # rango 8-12, gramos por 100ml
    acido_citrico_g_l: float = 0.0
    caramelo_ml: float = 0.0

    def __post_init__(self):
        self.volumen_objetivo_ml = self.volumen_objetivo_litros * 1000


@dataclass
class ComposicionBlendGancia:
    """Composición de un blend de Gancia"""

    vino_ml: float = 0.0
    alcohol_fortificacion_ml: float = 0.0
    tinturas: Dict[str, float] = field(default_factory=dict)  # tintura_id: ml
    agua_ml: float = 0.0  # remanente para completar el volumen objetivo
    azucar_g: float = 0.0
    acido_citrico_g: float = 0.0
    caramelo_ml: float = 0.0

    @property
    def volumen_total_ml(self) -> float:
        return (
            self.vino_ml
            + self.alcohol_fortificacion_ml
            + sum(self.tinturas.values())
            + self.agua_ml
        )


@dataclass
class GanciaBlendResult:
    """Resultado de un cálculo de blend de Gancia"""

    id: str = field(
        default_factory=lambda: f"G-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    )
    version: str = "1.0.0"
    params: GanciaBlendParams = None
    composicion: ComposicionBlendGancia = field(default_factory=ComposicionBlendGancia)
    abv_calculado: float = 0.0
    azucar_efectiva_g_l: float = 0.0
    fecha_calculo: datetime = field(default_factory=datetime.now)

    @property
    def volumen_real_ml(self) -> float:
        return self.composicion.volumen_total_ml + (self.composicion.azucar_g * 0.6)


class GanciaCalculator:
    """
    Calculadora principal para ensamblaje de Gancia.
    Base vínica: vino como componente mayoritario (75-80% del volumen),
    fortificado con alcohol neutro hasta alcanzar el ABV objetivo.
    """

    def calcular_base_vino_alcohol(
        self, params: GanciaBlendParams, tinturas_ml_total: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Calcula las proporciones de vino, alcohol de fortificación y agua.

        El vino se fija como porcentaje directo del volumen objetivo (no se
        deriva del ABV, a diferencia del alcohol de fortificación). El agua
        es el remanente una vez descontados vino, fortificación y tinturas
        - puede dar 0 o, si vino_pct + tinturas ya exceden el volumen antes
        de fortificar, negativo (se muestra tal cual, mismo criterio que
        FernetCalculator: sin validación dura, el usuario ajusta vino_pct).

        Args:
            params: Parámetros del blend
            tinturas_ml_total: Volumen total ya comprometido en tinturas

        Returns:
            Tuple[float, float, float]: (vino_ml, alcohol_fortificacion_ml, agua_ml)
        """
        volumen_total_ml = params.volumen_objetivo_ml
        vino_ml = volumen_total_ml * params.vino_pct

        alcohol_puro_necesario = volumen_total_ml * (params.abv_objetivo / 100)
        alcohol_puro_vino = vino_ml * (params.vino_abv / 100)
        alcohol_puro_faltante = max(0.0, alcohol_puro_necesario - alcohol_puro_vino)
        alcohol_fortificacion_ml = alcohol_puro_faltante / (
            params.alcohol_fortificacion_abv / 100
        )

        agua_ml = volumen_total_ml - vino_ml - alcohol_fortificacion_ml - tinturas_ml_total

        return vino_ml, alcohol_fortificacion_ml, agua_ml

    @staticmethod
    def calcular_abv_blend(
        composicion: ComposicionBlendGancia,
        tinturas_data: Dict[str, Tintura],
        vino_abv: float,
        alcohol_fortificacion_abv: float,
    ) -> float:
        """
        Calcula el ABV final de un blend de Gancia (sin azúcar).

        Args:
            composicion: Composición del blend
            tinturas_data: Diccionario con datos de tinturas (id -> Tintura)
            vino_abv: ABV del vino base utilizado
            alcohol_fortificacion_abv: ABV del alcohol de fortificación

        Returns:
            float: ABV calculado
        """
        componentes = [
            (composicion.vino_ml, vino_abv),
            (composicion.alcohol_fortificacion_ml, alcohol_fortificacion_abv),
        ]

        for tid, ml in composicion.tinturas.items():
            if tid in tinturas_data and tinturas_data[tid].parametros:
                componentes.append((ml, tinturas_data[tid].parametros.abv_objetivo))
            else:
                # Si no tenemos datos, asumimos 70% (default para tinturas)
                componentes.append((ml, 70.0))

        return abv_resultante(componentes, composicion.volumen_total_ml)

    @staticmethod
    def calcular_azucar(azucar_pct_wv: float, volumen_lote_ml: float) -> float:
        """
        Calcula los gramos de azúcar necesarios a partir de un porcentaje
        peso/volumen (gramos por 100ml) - azúcar seca, sin almíbar.

        Args:
            azucar_pct_wv: Porcentaje p/v objetivo (ej. 10.0 = 10g/100ml)
            volumen_lote_ml: Volumen del lote en ml

        Returns:
            float: Gramos de azúcar necesarios
        """
        return (azucar_pct_wv / 100) * volumen_lote_ml

    @staticmethod
    def calcular_volumen_con_azucar(volumen_sin_azucar_ml: float, azucar_g: float) -> float:
        """
        Calcula el volumen final considerando el aporte del azúcar.
        Misma aproximación que FernetCalculator: 1g de azúcar seca aporta
        ~0.6ml de volumen (sin modelar almíbar, según lo acordado).

        Returns:
            float: Volumen final en ml
        """
        return volumen_sin_azucar_ml + (azucar_g * 0.6)

    @staticmethod
    def calcular_abv_infusion(
        alcohol_ml: float, alcohol_abv: float, agua_ml: float
    ) -> float:
        """
        Calcula el ABV de una Gancia casera hecha por infusión directa:
        alcohol + cáscaras/hierbas macerando junto con agua, sin base
        vínica ni fortificación por separado (a diferencia de
        calcular_abv_blend, que sí asume vino). Azúcar y sólidos (cáscaras,
        hierbas) no aportan alcohol y no entran en este cálculo - solo
        diluyen el ABV al sumar volumen, lo cual ya queda reflejado al
        usar agua_ml como el volumen de dilución.

        Args:
            alcohol_ml: Volumen de alcohol puro utilizado (ej. 500ml de 96°)
            alcohol_abv: Graduación del alcohol (ej. 96.0)
            agua_ml: Volumen de agua agregado

        Returns:
            float: ABV resultante
        """
        return abv_resultante([(alcohol_ml, alcohol_abv)], alcohol_ml + agua_ml)
