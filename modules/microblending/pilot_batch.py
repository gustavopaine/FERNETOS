"""
Módulo de gestión de lotes piloto para microblending iterativo.
Permite crear y ajustar lotes de 500ml con precisión de 0.1ml.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import copy
import json
import uuid

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from families.fernet.calculator import (
    FernetCalculator,
    BlendResult,
    BlendParams,
    ComposicionBlend,
)
from core.tintura_models import Tintura
from modules.sensory.models import EvaluacionSensorial


@dataclass
class MicroAjuste:
    """Registro de un microajuste en el proceso iterativo"""

    id: str = field(
        default_factory=lambda: f"AJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    timestamp: datetime = field(default_factory=datetime.now)
    tintura_id: str = ""
    incremento_ml: float = 0.0  # Puede ser negativo
    observacion: str = ""
    razon_ajuste: str = ""  # "ataque_insuficiente", "exceso_amargor", etc.

    @property
    def delta_ml_formateado(self) -> str:
        return f"{self.incremento_ml:+.2f}"


@dataclass
class IteracionPiloto:
    """Una iteración completa del proceso de microblending"""

    numero: int
    blend: Any  # BlendResult de Fernet u otro producto (GanciaBlendResult, etc.)
    ajustes: List[MicroAjuste] = field(default_factory=list)
    evaluacion: Optional["EvaluacionSensorial"] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def resumen(self) -> str:
        ajustes_str = ", ".join(
            [f"{a.tintura_id[-4:]}: {a.delta_ml_formateado}" for a in self.ajustes]
        )
        return f"Iter {self.numero}: {ajustes_str}"


class PilotBatch:
    """
    Gestor de lotes piloto de 500ml para microblending iterativo.
    Permite crear, ajustar y evaluar versiones sucesivas con trazabilidad.
    """

    def __init__(
        self,
        nombre: str,
        blend_base: Any,
        tinturas_data: Dict[str, Tintura],
        volumen_piloto_ml: float = 500.0,
        calculator: Optional[Any] = None,
    ):
        """
        Inicializa un lote piloto.

        Args:
            nombre: Nombre identificativo del piloto
            blend_base: Blend base a escalar (cualquier objeto con
                .params.volumen_objetivo_litros y .composicion - no tiene
                que ser específicamente BlendResult de Fernet)
            tinturas_data: Datos de tinturas disponibles
            volumen_piloto_ml: Volumen del lote piloto (default: 500ml)
            calculator: Calculador a usar para escalar el blend base (debe
                exponer .escalar_blend(blend_result, nuevo_volumen_litros)).
                Por defecto FernetCalculator, para no romper el uso
                existente - se puede inyectar GanciaCalculator u otro para
                reutilizar este mismo pipeline con otros productos.
        """
        self.nombre = nombre
        self.id = f"PB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
        self.blend_base = blend_base
        self.tinturas_data = tinturas_data
        self.volumen_piloto_ml = volumen_piloto_ml
        self.calculator = calculator or FernetCalculator(tinturas_repo=None)

        self.iteraciones: List[IteracionPiloto] = []
        self.ajustes_acumulados: Dict[str, float] = {}  # tintura_id: ml total ajustado
        self.fecha_creacion = datetime.now()
        self.activo = True

        # Crear iteración inicial
        self._crear_iteracion_inicial()

    def _crear_iteracion_inicial(self):
        """Crea la iteración 0 (blend base escalado a piloto)"""
        blend_piloto = self.calculator.escalar_blend(
            self.blend_base, self.volumen_piloto_ml / 1000
        )

        iteracion = IteracionPiloto(numero=0, blend=blend_piloto, ajustes=[])

        self.iteraciones.append(iteracion)

    def crear_lote_piloto_desde_base(self) -> Any:
        """Retorna el blend escalado a volumen piloto (iteración actual)"""
        return self.iteraciones[-1].blend

    def aplicar_ajuste(
        self,
        tintura_id: str,
        incremento_ml: float,
        razon: str = "",
        observacion: str = "",
    ) -> Any:
        """
        Aplica un microajuste a la última iteración y crea una nueva.

        Args:
            tintura_id: ID de la tintura a ajustar
            incremento_ml: Incremento en ml (puede ser negativo)
            razon: Razón del ajuste
            observacion: Observación adicional

        Returns:
            BlendResult: Nuevo blend resultante
        """
        if not self.activo:
            raise ValueError("El lote piloto está cerrado")

        ultima_iter = self.iteraciones[-1]

        # Crear ajuste
        ajuste = MicroAjuste(
            tintura_id=tintura_id,
            incremento_ml=incremento_ml,
            razon_ajuste=razon,
            observacion=observacion,
        )

        # Aplicar al blend
        nuevo_blend = copy.deepcopy(ultima_iter.blend)

        if tintura_id in nuevo_blend.composicion.tinturas:
            nuevo_blend.composicion.tinturas[tintura_id] += incremento_ml
        else:
            nuevo_blend.composicion.tinturas[tintura_id] = incremento_ml

        # Actualizar ID y versión
        nuevo_blend.id = f"{ultima_iter.blend.id}-IT{len(self.iteraciones)}"
        nuevo_blend.version = self._incrementar_version(
            ultima_iter.blend.version, "ajuste"
        )

        # Crear nueva iteración
        nueva_iter = IteracionPiloto(
            numero=len(self.iteraciones), blend=nuevo_blend, ajustes=[ajuste]
        )

        self.iteraciones.append(nueva_iter)

        # Actualizar acumulado
        self.ajustes_acumulados[tintura_id] = (
            self.ajustes_acumulados.get(tintura_id, 0) + incremento_ml
        )

        return nuevo_blend

    def aplicar_ajustes_multiples(
        self, ajustes: List[Tuple[str, float]], razon: str = "ajuste_multiples"
    ) -> Any:
        """
        Aplica múltiples ajustes en una sola iteración.

        Args:
            ajustes: Lista de (tintura_id, incremento_ml)
            razon: Razón global del ajuste

        Returns:
            BlendResult: Nuevo blend
        """
        if not self.activo:
            raise ValueError("El lote piloto está cerrado")

        ultima_iter = self.iteraciones[-1]

        # Crear ajustes
        nuevos_ajustes = []
        nuevo_blend = copy.deepcopy(ultima_iter.blend)

        for tintura_id, incremento_ml in ajustes:
            ajuste = MicroAjuste(
                tintura_id=tintura_id, incremento_ml=incremento_ml, razon_ajuste=razon
            )
            nuevos_ajustes.append(ajuste)

            if tintura_id in nuevo_blend.composicion.tinturas:
                nuevo_blend.composicion.tinturas[tintura_id] += incremento_ml
            else:
                nuevo_blend.composicion.tinturas[tintura_id] = incremento_ml

            self.ajustes_acumulados[tintura_id] = (
                self.ajustes_acumulados.get(tintura_id, 0) + incremento_ml
            )

        # Actualizar ID y versión
        nuevo_blend.id = f"{ultima_iter.blend.id}-IT{len(self.iteraciones)}"
        nuevo_blend.version = self._incrementar_version(
            ultima_iter.blend.version, "ajuste"
        )

        # Crear nueva iteración
        nueva_iter = IteracionPiloto(
            numero=len(self.iteraciones), blend=nuevo_blend, ajustes=nuevos_ajustes
        )

        self.iteraciones.append(nueva_iter)

        return nuevo_blend

    def registrar_evaluacion(
        self, evaluacion: EvaluacionSensorial, iteracion_numero: int = -1
    ):
        """
        Asocia una evaluación sensorial a una iteración.

        Args:
            evaluacion: Evaluación sensorial realizada
            iteracion_numero: Número de iteración (por defecto la última)
        """
        if iteracion_numero == -1:
            iteracion_numero = len(self.iteraciones) - 1

        if 0 <= iteracion_numero < len(self.iteraciones):
            self.iteraciones[iteracion_numero].evaluacion = evaluacion

    def get_iteracion(self, numero: int) -> Optional[IteracionPiloto]:
        """Obtiene una iteración por su número"""
        if 0 <= numero < len(self.iteraciones):
            return self.iteraciones[numero]
        return None

    def get_ultima_iteracion(self) -> IteracionPiloto:
        """Obtiene la última iteración"""
        return self.iteraciones[-1]

    def get_mejor_iteracion(
        self, criterio: str = "puntaje_total"
    ) -> Optional[IteracionPiloto]:
        """
        Encuentra la mejor iteración según criterio de evaluación.

        Args:
            criterio: Atributo de evaluación a maximizar

        Returns:
            Optional[IteracionPiloto]: Mejor iteración o None
        """
        iteraciones_con_eval = [
            i
            for i in self.iteraciones
            if i.evaluacion is not None and hasattr(i.evaluacion, criterio)
        ]

        if not iteraciones_con_eval:
            return None

        return max(
            iteraciones_con_eval, key=lambda i: getattr(i.evaluacion, criterio, 0)
        )

    def get_historial_ajustes(self) -> List[Dict]:
        """Retorna historial completo de ajustes"""
        historial = []

        for iteracion in self.iteraciones[1:]:  # Saltar iteración 0
            for ajuste in iteracion.ajustes:
                historial.append(
                    {
                        "iteracion": iteracion.numero,
                        "timestamp": ajuste.timestamp.isoformat(),
                        "tintura_id": ajuste.tintura_id,
                        "incremento_ml": ajuste.incremento_ml,
                        "razon": ajuste.razon_ajuste,
                        "observacion": ajuste.observacion,
                    }
                )

        return historial

    def reset_a_iteracion(self, numero: int) -> bool:
        """
        Resetea el piloto a una iteración anterior.

        Args:
            numero: Número de iteración a la que volver

        Returns:
            bool: True si se pudo resetear
        """
        if 0 <= numero < len(self.iteraciones):
            # Eliminar iteraciones posteriores
            self.iteraciones = self.iteraciones[: numero + 1]

            # Recalcular ajustes acumulados
            self.ajustes_acumulados = {}
            for i in range(1, len(self.iteraciones)):
                for ajuste in self.iteraciones[i].ajustes:
                    self.ajustes_acumulados[ajuste.tintura_id] = (
                        self.ajustes_acumulados.get(ajuste.tintura_id, 0)
                        + ajuste.incremento_ml
                    )

            return True
        return False

    def cerrar_piloto(self):
        """Marca el piloto como cerrado (no más ajustes)"""
        self.activo = False

    def generar_reporte(self) -> Dict:
        """Genera reporte completo del proceso de microblending"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "volumen_piloto_ml": self.volumen_piloto_ml,
            "iteraciones_totales": len(self.iteraciones) - 1,  # Restar iter 0
            "activo": self.activo,
            "blend_base_id": self.blend_base.id,
            "blend_base_version": self.blend_base.version,
            "mejor_iteracion": (
                self.get_mejor_iteracion().numero
                if self.get_mejor_iteracion()
                else None
            ),
            "ajustes_acumulados": self.ajustes_acumulados,
            "historial_ajustes": self.get_historial_ajustes(),
            "iteraciones": [
                {
                    "numero": i.numero,
                    "blend_id": i.blend.id,
                    "blend_version": i.blend.version,
                    "num_ajustes": len(i.ajustes),
                    "evaluacion_id": i.evaluacion.id if i.evaluacion else None,
                }
                for i in self.iteraciones
            ],
        }

    def _incrementar_version(self, version: str, tipo: str) -> str:
        """Incrementa versión semántica"""
        major, minor, patch = map(int, version.split("."))

        if tipo == "major":
            return f"{major+1}.0.0"
        elif tipo == "minor":
            return f"{major}.{minor+1}.0"
        else:  # patch o ajuste
            return f"{major}.{minor}.{patch+1}"

    def guardar(self, directorio: str = "data/batches/pilotos") -> str:
        """Guarda el estado del piloto en archivo JSON"""
        os.makedirs(directorio, exist_ok=True)

        filepath = os.path.join(directorio, f"{self.id}_{self.nombre}.json")

        with open(filepath, "w") as f:
            json.dump(self.generar_reporte(), f, indent=2)

        return filepath
