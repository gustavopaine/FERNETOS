"""
Motor de cálculo para Americano (ex-Gancia casero): receta real de
infusión directa (alcohol + agua + botánicos macerando juntos en un solo
lote), distinta de la base vínica de gancia_calculator.py. Estructura
paralela, sin heredar de GanciaCalculator - comparten únicamente el
balance de alcohol puro vía core.blend_math.

Capa de extensibilidad para variantes experimentales: la receta base
(genciana, melisa, canela, anís estrellado, angélica, enebro, cítricos)
es la validada contra dos transcripciones de la misma fuente y no se
toca. Las variantes solo pueden agregar/reemplazar ingredientes del banco
de opcionales (clavo de olor, galanga, paico, romero), pensadas para
probar y competir contra el Gancia comercial y otras marcas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from core.tintura_models import ComposicionBotanica
from core.blend_math import abv_resultante
from families.gancia.gancia_calculator import GanciaCalculator

# Banco de botánicos. No se superponen entre sí (ver test dedicado) para
# que no haya ambigüedad sobre qué lista protege a cada ingrediente.
INGREDIENTES_CORE = ["genciana", "melisa"]
INGREDIENTES_CORE_SECUNDARIOS = [
    "canela",
    "anis_estrellado",
    "angelica",
    "enebro",
    "pomelo",
    "limon",
    "naranja",
]
INGREDIENTES_OPCIONALES = ["clavo_de_olor", "galanga", "paico", "romero"]


def validar_ingrediente_variante(especie: str) -> None:
    """
    Valida que un ingrediente de ingredientes_variante venga del banco de
    opcionales - ni el core (genciana/melisa, intocable) ni los
    core-secundarios (cambiarlos define una receta distinta, se editan en
    ingredientes_base) entran acá.
    """
    if especie not in INGREDIENTES_OPCIONALES:
        raise ValueError(
            f"'{especie}' no es un ingrediente opcional válido para una "
            f"variante experimental. Opcionales disponibles: {INGREDIENTES_OPCIONALES}"
        )


@dataclass
class ComposicionAmericano:
    """Composición de un lote de Americano (infusión directa)"""

    alcohol_ml: float = 0.0
    alcohol_abv: float = 96.0
    agua_ml: float = 0.0
    azucar_g: float = 0.0
    ingredientes_base: List[ComposicionBotanica] = field(default_factory=list)
    ingredientes_variante: List[ComposicionBotanica] = field(default_factory=list)

    def __post_init__(self):
        for ingrediente in self.ingredientes_variante:
            validar_ingrediente_variante(ingrediente.especie)

    @property
    def volumen_total_ml(self) -> float:
        return self.alcohol_ml + self.agua_ml


@dataclass
class VarianteExperimental:
    """
    Una preparación puntual de Americano: la receta base o una variante
    con algún opcional agregado/cambiado. batch_id identifica cada
    preparación para trackear qué se probó (ej. "AMERICANO_CLAVO_v1").
    """

    batch_id: str
    composicion: ComposicionAmericano
    referencia_comercial: Optional[str] = None  # notas de cata vs. marcas comerciales
    abv_calculado: float = 0.0
    fecha_creacion: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.abv_calculado = AmericanoCalculator.calcular_abv(self.composicion)


class AmericanoCalculator:
    """
    Calculadora para Americano por infusión directa. A diferencia de
    GanciaCalculator (base vínica), acá todo el alcohol viene de una sola
    fuente y no hay fortificación por separado.
    """

    @staticmethod
    def calcular_abv(composicion: ComposicionAmericano) -> float:
        """
        ABV de una infusión directa: alcohol diluido en el agua total.
        Azúcar y sólidos (cáscaras, hierbas) no aportan alcohol y no
        entran en este cálculo.

        Returns:
            float: ABV resultante
        """
        return abv_resultante(
            [(composicion.alcohol_ml, composicion.alcohol_abv)],
            composicion.volumen_total_ml,
        )

    # Azúcar: mismo mecanismo que Gancia (% p/v, azúcar seca sin almíbar) -
    # se reutiliza directamente en vez de duplicar la fórmula.
    calcular_azucar = staticmethod(GanciaCalculator.calcular_azucar)
    calcular_volumen_con_azucar = staticmethod(GanciaCalculator.calcular_volumen_con_azucar)
