"""
Modelo de receta: formulación nombrada y versionada de una familia de
producto, independiente del cálculo de blend en sí.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid


class EstadoReceta(Enum):
    BORRADOR = "borrador"
    TESTING = "testing"
    LISTA_PARA_TORNEO = "lista_para_torneo"


@dataclass
class IngredienteReceta:
    """Un ingrediente (tintura) dentro de una receta, con su proporción."""

    tintura_id: str
    porcentaje: Optional[float] = None  # % del total, si la receta usa porcentajes
    ml: Optional[float] = None  # cantidad absoluta en ml, si la receta usa cantidades fijas

    def to_dict(self) -> Dict:
        return {"tintura_id": self.tintura_id, "porcentaje": self.porcentaje, "ml": self.ml}

    @classmethod
    def from_dict(cls, data: Dict) -> "IngredienteReceta":
        return cls(
            tintura_id=data["tintura_id"],
            porcentaje=data.get("porcentaje"),
            ml=data.get("ml"),
        )


@dataclass
class Receta:
    """Formulación nombrada y versionada de una familia de producto."""

    id: str = field(
        default_factory=lambda: f"R-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    )
    familia: str = ""  # "fernet" | "americano" | "campari"
    nombre: str = ""
    version: str = "1.0.0"
    estado: EstadoReceta = EstadoReceta.BORRADOR
    ingredientes: List[IngredienteReceta] = field(default_factory=list)
    abv_objetivo: Optional[float] = None
    tiempo_maceracion_dias: Optional[int] = None
    perfil_sensorial_objetivo: Dict[str, float] = field(default_factory=dict)
    notas_batch: str = ""
    fecha_creacion: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        from core.validators import validar_familia_receta

        validar_familia_receta(self.familia)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "familia": self.familia,
            "nombre": self.nombre,
            "version": self.version,
            "estado": self.estado.value,
            "ingredientes": [i.to_dict() for i in self.ingredientes],
            "abv_objetivo": self.abv_objetivo,
            "tiempo_maceracion_dias": self.tiempo_maceracion_dias,
            "perfil_sensorial_objetivo": self.perfil_sensorial_objetivo,
            "notas_batch": self.notas_batch,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }
