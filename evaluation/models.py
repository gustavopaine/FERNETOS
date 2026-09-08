"""
Entidades del modulo de evaluacion/torneo (cata a ciegas).

Ver fernetos-diseño-y-roadmap.md, seccion 5, para el diseño completo:
Evento > Categoria > Muestra, Jurado independiente, Puntaje por
muestra/jurado con la rubrica de la seccion 5.2, Ranking por categoria.

Este modulo solo define las entidades y su validacion basica; la
persistencia (repositorio SQL), la codificacion ciega con aleatorizacion
de orden de cata, y el calculo de ranking (media recortada) son slices
siguientes de la Fase 2, todavia no implementados.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from core.validators import validar_familia_receta

PUNTAJE_MIN = 1
PUNTAJE_MAX = 10

# Pesos de la rubrica de cata (roadmap, seccion 5.2).
PESO_VISUAL = 0.15
PESO_AROMA = 0.30
PESO_SABOR_BOCA = 0.55


class SubModalidad(Enum):
    PURO = "puro"
    CON_COLA = "con_cola"
    CON_SODA = "con_soda"
    CON_TONICA = "con_tonica"


class RolJurado(Enum):
    SOMMELIER = "sommelier"
    BARTENDER = "bartender"
    PRODUCTOR = "productor"
    PUBLICO = "publico"


def _nuevo_id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


@dataclass
class Evento:
    """Un torneo/edicion de competencia."""

    nombre: str
    fecha: str
    sede: str
    edicion_numero: int
    id: str = field(default_factory=lambda: _nuevo_id("EVT"))


@dataclass
class Categoria:
    """Una categoria de cata dentro de un evento (familia + submodalidad)."""

    evento_id: str
    familia: str
    submodalidad: SubModalidad
    id: str = field(default_factory=lambda: _nuevo_id("CAT"))

    def __post_init__(self):
        validar_familia_receta(self.familia)


@dataclass
class Muestra:
    """
    Una muestra cargada a una categoria, identificada solo por su
    codigo_ciego mientras la ronda esta abierta. `receta_id_interna` y
    `productor_id` existen en el modelo pero quedan en None salvo que se
    seteen explicitamente: la ocultacion real (quien puede leerlos antes
    del cierre de la ronda) es responsabilidad de la capa que los
    persista/exponga, no de este dataclass.
    """

    categoria_id: str
    id: str = field(default_factory=lambda: _nuevo_id("MST"))
    # 6 hex chars (~16.7M combinaciones) para que la probabilidad de
    # colision sea despreciable a la escala de una competencia real. Esto
    # NO reemplaza una restriccion UNIQUE a nivel de repositorio/schema
    # (pendiente, ver spec) - un dataclass no tiene forma de chequear
    # contra otras Muestra ya creadas.
    codigo_ciego: str = field(default_factory=lambda: f"M-{uuid.uuid4().hex[:6].upper()}")
    receta_id_interna: Optional[str] = None
    productor_id: Optional[str] = None


@dataclass
class Jurado:
    """Un jurado de la competencia."""

    nombre: str
    rol: RolJurado
    id: str = field(default_factory=lambda: _nuevo_id("JUR"))
    peso_voto: float = 1.0

    def __post_init__(self):
        if self.peso_voto <= 0:
            raise ValueError(f"'peso_voto' debe ser positivo: {self.peso_voto}")


@dataclass
class Puntaje:
    """
    Puntaje de un jurado a una muestra, segun la rubrica de la seccion
    5.2 del roadmap (visual/aroma/sabor_boca, 1-10 cada uno).
    """

    muestra_id: str
    jurado_id: str
    visual: float
    aroma: float
    sabor_boca: float
    comentario_libre: str = ""
    id: str = field(default_factory=lambda: _nuevo_id("PTJ"))
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        for nombre, valor in (
            ("visual", self.visual),
            ("aroma", self.aroma),
            ("sabor_boca", self.sabor_boca),
        ):
            if not (PUNTAJE_MIN <= valor <= PUNTAJE_MAX):
                raise ValueError(
                    f"'{nombre}' fuera de rango [{PUNTAJE_MIN}, {PUNTAJE_MAX}]: {valor}"
                )

    def puntaje_ponderado(self) -> float:
        return (
            self.visual * PESO_VISUAL
            + self.aroma * PESO_AROMA
            + self.sabor_boca * PESO_SABOR_BOCA
        )


@dataclass
class Ranking:
    """Posicion final de una muestra dentro de su categoria."""

    categoria_id: str
    muestra_id: str
    puntaje_final: float
    posicion: int
