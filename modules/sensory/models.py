# -*- coding: utf-8 -*-
# Archivo en desarrollo
# M�dulo: models.py

"""
Modelos para evaluación sensorial y análisis de atributos.
Define estructuras para capturar y analizar percepciones en cata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import uuid


@dataclass
class AtributoEvaluado:
    """Evaluación de un atributo sensorial específico"""

    nombre: str  # "ataque", "amargor", "dulzor", "persistencia", etc.
    valor: float  # 1-10
    comentario: Optional[str] = None

    def __post_init__(self):
        if self.valor < 1 or self.valor > 10:
            raise ValueError(f"Valor {self.valor} fuera de rango (1-10)")


@dataclass
class EvaluacionSensorial:
    """
    Evaluación completa de una muestra en cata.
    Captura todos los atributos relevantes para fernet.
    """

    id: str = field(
        default_factory=lambda: f"EV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
    )
    muestra_id: str = ""  # ID del blend o tintura evaluado
    muestra_descripcion: str = ""
    fecha: datetime = field(default_factory=datetime.now)
    catador: str = ""

    # Atributos principales (1-10)
    ataque: float = 5.0  # Impacto inicial (primeros 3 segundos)
    complejidad: float = 5.0  # Variedad de notas
    equilibrio: float = 5.0  # Balance general
    persistencia: float = 5.0  # Duración post-deglución
    amargor: float = 5.0  # Intensidad de amargor
    dulzor: float = 5.0  # Percepción de dulzor
    astringencia: float = 5.0  # Sequedad en boca
    alcohol_sensacion: float = 5.0  # Calor/agresividad del alcohol

    # Notas específicas (presencia 0-10)
    notas_herbaceas: float = 0.0
    notas_especiadas: float = 0.0
    notas_citricas: float = 0.0
    notas_medicinales: float = 0.0
    notas_balsamicas: float = 0.0

    # Observaciones cualitativas
    observaciones: str = ""
    defectos: List[str] = field(
        default_factory=list
    )  # "oxidado", "turbio", "clavo_dominante", etc.

    # Comparativas
    referencia_comparada: Optional[str] = None  # "branca", etc.
    preferencia_vs_referencia: Optional[str] = None  # "nuestra", "referencia", "empate"

    @property
    def puntaje_total(self) -> float:
        """Puntaje ponderado para ranking"""
        # Pesos para competencia
        pesos = {
            "ataque": 0.2,
            "complejidad": 0.2,
            "equilibrio": 0.25,
            "persistencia": 0.2,
            "amargor": 0.15,
        }

        total = (
            pesos["ataque"] * self.ataque
            + pesos["complejidad"] * self.complejidad
            + pesos["equilibrio"] * self.equilibrio
            + pesos["persistencia"] * self.persistencia
            + pesos["amargor"] * self.amargor
        )

        return round(total, 2)

    @property
    def perfil_aromático(self) -> Dict[str, float]:
        """Perfil de notas aromáticas"""
        return {
            "herbaceo": self.notas_herbaceas,
            "especiado": self.notas_especiadas,
            "citrico": self.notas_citricas,
            "medicinal": self.notas_medicinales,
            "balsamico": self.notas_balsamicas,
        }

    def to_dict(self) -> Dict:
        """Exporta a diccionario"""
        return {
            "id": self.id,
            "muestra_id": self.muestra_id,
            "fecha": self.fecha.isoformat(),
            "catador": self.catador,
            "atributos": {
                "ataque": self.ataque,
                "complejidad": self.complejidad,
                "equilibrio": self.equilibrio,
                "persistencia": self.persistencia,
                "amargor": self.amargor,
                "dulzor": self.dulzor,
                "astringencia": self.astringencia,
                "alcohol": self.alcohol_sensacion,
            },
            "notas_especificas": self.perfil_aromático,
            "puntaje_total": self.puntaje_total,
            "observaciones": self.observaciones,
            "defectos": self.defectos,
            "referencia_comparada": self.referencia_comparada,
            "preferencia": self.preferencia_vs_referencia,
        }


class SensoryAnalyzer:
    """
    Analizador de evaluaciones sensoriales.
    Procesa múltiples catas y extrae conclusiones.
    """

    def __init__(self):
        self.evaluaciones: List[EvaluacionSensorial] = []

    def agregar_evaluacion(self, evaluacion: EvaluacionSensorial):
        """Añade una evaluación a la base"""
        self.evaluaciones.append(evaluacion)

    def analizar_muestra(self, muestra_id: str) -> Dict:
        """
        Analiza todas las evaluaciones de una muestra.

        Args:
            muestra_id: ID de la muestra a analizar

        Returns:
            Dict: Estadísticas de la muestra
        """
        evals = [e for e in self.evaluaciones if e.muestra_id == muestra_id]

        if not evals:
            return {"mensaje": "No hay evaluaciones para esta muestra"}

        # Promedios por atributo
        promedios = {
            "ataque": sum(e.ataque for e in evals) / len(evals),
            "complejidad": sum(e.complejidad for e in evals) / len(evals),
            "equilibrio": sum(e.equilibrio for e in evals) / len(evals),
            "persistencia": sum(e.persistencia for e in evals) / len(evals),
            "amargor": sum(e.amargor for e in evals) / len(evals),
            "puntaje_total": sum(e.puntaje_total for e in evals) / len(evals),
        }

        # Perfil aromático promedio
        perfil = {
            "herbaceo": sum(e.notas_herbaceas for e in evals) / len(evals),
            "especiado": sum(e.notas_especiadas for e in evals) / len(evals),
            "citrico": sum(e.notas_citricas for e in evals) / len(evals),
            "medicinal": sum(e.notas_medicinales for e in evals) / len(evals),
            "balsamico": sum(e.notas_balsamicas for e in evals) / len(evals),
        }

        # Defectos más comunes
        defectos = {}
        for e in evals:
            for d in e.defectos:
                defectos[d] = defectos.get(d, 0) + 1

        return {
            "muestra_id": muestra_id,
            "num_evaluaciones": len(evals),
            "promedios": promedios,
            "perfil_aromatico": perfil,
            "defectos": defectos,
            "consistencia": {
                "std_ataque": self._std([e.ataque for e in evals]),
                "std_total": self._std([e.puntaje_total for e in evals]),
            },
        }

    def comparar_muestras(self, muestra_ids: List[str]) -> Dict:
        """
        Compara múltiples muestras entre sí.

        Args:
            muestra_ids: Lista de IDs a comparar

        Returns:
            Dict: Comparativa de muestras
        """
        resultados = {}

        for mid in muestra_ids:
            resultados[mid] = self.analizar_muestra(mid)

        # Ranking por puntaje total
        ranking = sorted(
            [
                (mid, res["promedios"]["puntaje_total"])
                for mid, res in resultados.items()
                if "promedios" in res
            ],
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "muestras": resultados,
            "ranking": [{"muestra": r[0], "puntaje": r[1]} for r in ranking],
        }

    def _std(self, valores: List[float]) -> float:
        """Desviación estándar simple"""
        if len(valores) < 2:
            return 0.0
        media = sum(valores) / len(valores)
        var = sum((v - media) ** 2 for v in valores) / (len(valores) - 1)
        return var**0.5
