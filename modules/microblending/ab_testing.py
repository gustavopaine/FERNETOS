"""
Módulo de pruebas A/B y triangulares para evaluación comparativa.
Permite realizar catas ciegas sistemáticas contra referencias.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import random
import uuid
import json
import os

from modules.sensory.models import EvaluacionSensorial, AtributoEvaluado


@dataclass
class ResultadoPrueba:
    """Resultado de una prueba comparativa"""

    prueba_id: str
    tipo: str  # "ab", "triangular", "preferencia"
    muestras: Dict[str, Any]  # código -> descripción
    seleccionado: str  # código de la muestra seleccionada
    correcto: Optional[bool] = None  # Para pruebas con respuesta conocida
    preferencia: Optional[str] = None  # Para pruebas A/B
    atributos_destacados: List[str] = field(default_factory=list)
    notas: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    catador: str = ""


@dataclass
class ComparativaReferencia:
    """Resultado de comparación contra referencia de mercado"""

    referencia: str  # "branca", "vittone", etc.
    nuestro_codigo: str
    referencia_codigo: str
    atributos_ganados: List[str] = field(
        default_factory=list
    )  # Atributos donde ganamos
    atributos_perdidos: List[str] = field(default_factory=list)
    puntaje_diferencial: float = 0.0  # Positivo = ganamos
    superioridad_detectada: bool = False
    confianza: float = 0.0  # 0-1


class ABTesting:
    """
    Sistema de pruebas A/B y triangulares para evaluación comparativa.
    Permite realizar catas ciegas con trazabilidad completa.
    """

    def __init__(self, output_dir: str = "data/sensory/tests"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.pruebas: List[ResultadoPrueba] = []

    def generar_codigos(self, n: int, prefijo: str = "M") -> List[str]:
        """
        Genera códigos aleatorios de 3 dígitos para muestras ciegas.

        Args:
            n: Número de códigos a generar
            prefijo: Prefijo para los códigos

        Returns:
            List[str]: Lista de códigos
        """
        codigos = []
        for _ in range(n):
            codigo = f"{prefijo}{random.randint(100, 999)}"
            codigos.append(codigo)
        return codigos

    def preparar_prueba_ab(
        self,
        muestra_a: Any,
        muestra_b: Any,
        desc_a: str = "Nuestra fórmula",
        desc_b: str = "Referencia",
        ciego: bool = True,
    ) -> Dict:
        """
        Prepara una prueba A/B con codificación ciega.

        Args:
            muestra_a: Primera muestra
            muestra_b: Segunda muestra
            desc_a: Descripción de muestra A
            desc_b: Descripción de muestra B
            ciego: Si es ciega (True) o abierta (False)

        Returns:
            Dict: Configuración de la prueba
        """
        codigos = self.generar_codigos(2)

        if ciego:
            # Asignación aleatoria de códigos
            mapeo = {
                codigos[0]: {"muestra": muestra_a, "desc": desc_a},
                codigos[1]: {"muestra": muestra_b, "desc": desc_b},
            }
            # Mezclar para que el orden no influya
            if random.choice([True, False]):
                mapeo = {
                    codigos[1]: {"muestra": muestra_a, "desc": desc_a},
                    codigos[0]: {"muestra": muestra_b, "desc": desc_b},
                }
        else:
            mapeo = {
                "A": {"muestra": muestra_a, "desc": desc_a},
                "B": {"muestra": muestra_b, "desc": desc_b},
            }
            codigos = ["A", "B"]

        return {
            "prueba_id": f"AB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "tipo": "ab",
            "ciego": ciego,
            "codigos": codigos,
            "mapeo": mapeo,
            "fecha": datetime.now().isoformat(),
        }

    def preparar_prueba_triangular(
        self,
        muestra_correcta: Any,
        muestra_incorrecta: Any,
        desc_correcta: str = "Nuestra fórmula",
        desc_incorrecta: str = "Otra",
    ) -> Dict:
        """
        Prepara una prueba triangular (2 iguales, 1 diferente).

        Args:
            muestra_correcta: Muestra que se repite (2 veces)
            muestra_incorrecta: Muestra diferente (1 vez)
            desc_correcta: Descripción de la muestra correcta
            desc_incorrecta: Descripción de la muestra diferente

        Returns:
            Dict: Configuración de la prueba
        """
        codigos = self.generar_codigos(3)

        # Decidir aleatoriamente qué código es el diferente
        idx_diferente = random.randint(0, 2)

        mapeo = {}
        for i, codigo in enumerate(codigos):
            if i == idx_diferente:
                mapeo[codigo] = {
                    "muestra": muestra_incorrecta,
                    "desc": desc_incorrecta,
                    "es_diferente": True,
                }
            else:
                mapeo[codigo] = {
                    "muestra": muestra_correcta,
                    "desc": desc_correcta,
                    "es_diferente": False,
                }

        return {
            "prueba_id": f"TRI-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "tipo": "triangular",
            "codigos": codigos,
            "codigo_diferente": codigos[idx_diferente],
            "mapeo": mapeo,
            "fecha": datetime.now().isoformat(),
        }

    def registrar_resultado_ab(
        self,
        prueba_config: Dict,
        codigo_seleccionado: str,
        preferencia: Optional[str] = None,
        atributos: List[str] = None,
        notas: str = "",
        catador: str = "",
    ) -> ResultadoPrueba:
        """
        Registra el resultado de una prueba A/B.

        Args:
            prueba_config: Configuración de la prueba
            codigo_seleccionado: Código de la muestra seleccionada
            preferencia: "A", "B" o None
            atributos: Atributos destacados
            notas: Notas adicionales
            catador: Nombre del catador

        Returns:
            ResultadoPrueba: Resultado registrado
        """
        # Determinar si la selección es correcta (para pruebas con referencia conocida)
        correcto = None
        if not prueba_config["ciego"]:
            # En prueba abierta, "A" y "B" son los códigos
            pass
        elif "referencia" in str(prueba_config):
            # Lógica para determinar corrección
            pass

        resultado = ResultadoPrueba(
            prueba_id=prueba_config["prueba_id"],
            tipo=prueba_config["tipo"],
            muestras=prueba_config["mapeo"],
            seleccionado=codigo_seleccionado,
            correcto=correcto,
            preferencia=preferencia,
            atributos_destacados=atributos or [],
            notas=notas,
            catador=catador,
        )

        self.pruebas.append(resultado)
        self._guardar_resultado(resultado)

        return resultado

    def registrar_resultado_triangular(
        self,
        prueba_config: Dict,
        codigo_seleccionado: str,
        notas: str = "",
        catador: str = "",
    ) -> ResultadoPrueba:
        """
        Registra el resultado de una prueba triangular.

        Args:
            prueba_config: Configuración de la prueba
            codigo_seleccionado: Código de la muestra identificada como diferente
            notas: Notas adicionales
            catador: Nombre del catador

        Returns:
            ResultadoPrueba: Resultado registrado
        """
        correcto = codigo_seleccionado == prueba_config["codigo_diferente"]

        resultado = ResultadoPrueba(
            prueba_id=prueba_config["prueba_id"],
            tipo=prueba_config["tipo"],
            muestras=prueba_config["mapeo"],
            seleccionado=codigo_seleccionado,
            correcto=correcto,
            notas=notas + (f" CORRECTO: {correcto}" if correcto is not None else ""),
            catador=catador,
        )

        self.pruebas.append(resultado)
        self._guardar_resultado(resultado)

        return resultado

    def _guardar_resultado(self, resultado: ResultadoPrueba):
        """Guarda resultado en archivo"""
        filepath = os.path.join(self.output_dir, f"{resultado.prueba_id}.json")

        with open(filepath, "w") as f:
            json.dump(
                {
                    "prueba_id": resultado.prueba_id,
                    "tipo": resultado.tipo,
                    "seleccionado": resultado.seleccionado,
                    "correcto": resultado.correcto,
                    "preferencia": resultado.preferencia,
                    "atributos": resultado.atributos_destacados,
                    "notas": resultado.notas,
                    "timestamp": resultado.timestamp.isoformat(),
                    "catador": resultado.catador,
                },
                f,
                indent=2,
            )

    def analizar_resultados(self, prueba_ids: List[str] = None) -> Dict:
        """
        Analiza resultados de pruebas.

        Args:
            prueba_ids: Lista de IDs a analizar (None = todas)

        Returns:
            Dict: Estadísticas de las pruebas
        """
        pruebas = self.pruebas
        if prueba_ids:
            pruebas = [p for p in self.pruebas if p.prueba_id in prueba_ids]

        if not pruebas:
            return {"mensaje": "No hay pruebas para analizar"}

        # Estadísticas generales
        total = len(pruebas)
        ab_pruebas = [p for p in pruebas if p.tipo == "ab"]
        tri_pruebas = [p for p in pruebas if p.tipo == "triangular"]

        # Análisis de pruebas triangulares
        triangulares_correctas = sum(1 for p in tri_pruebas if p.correcto)
        triangulares_total = len(tri_pruebas)
        tasa_aciertos = (
            triangulares_correctas / triangulares_total if triangulares_total > 0 else 0
        )

        # Análisis de preferencias en A/B
        preferencias = {}
        for p in ab_pruebas:
            if p.preferencia:
                preferencias[p.preferencia] = preferencias.get(p.preferencia, 0) + 1

        # Atributos más mencionados
        atributos = {}
        for p in pruebas:
            for attr in p.atributos_destacados:
                atributos[attr] = atributos.get(attr, 0) + 1

        return {
            "total_pruebas": total,
            "triangulares": {
                "total": triangulares_total,
                "correctas": triangulares_correctas,
                "tasa_aciertos": tasa_aciertos,
                "significativo": tasa_aciertos > 0.5,  # Simple
            },
            "ab_preferencias": preferencias,
            "atributos_destacados": dict(
                sorted(atributos.items(), key=lambda x: x[1], reverse=True)
            ),
            "pruebas_recientes": sorted(
                pruebas, key=lambda p: p.timestamp, reverse=True
            )[:5],
        }


class CompetitiveAnalyzer:
    """
    Analizador de competitividad contra referencias de mercado.
    Evalúa qué atributos superan a la competencia.
    """

    def __init__(self):
        self.referencias = {
            "branca": {
                "nombre": "Fernet Branca",
                "perfil": "dulce_pesado",
                "azucar_gpl": 200,
                "amargor": 8,
                "ataque": "herbaceo_medio",
            },
            "vittone": {
                "nombre": "Fernet Vittone",
                "perfil": "seco_herbal",
                "azucar_gpl": 170,
                "amargor": 9,
                "ataque": "intenso_mentolado",
            },
            "1882": {
                "nombre": "Fernet 1882",
                "perfil": "equilibrado",
                "azucar_gpl": 185,
                "amargor": 7.5,
                "ataque": "citrico_herbal",
            },
        }

    def comparar_con_referencia(
        self,
        evaluacion_nuestra: EvaluacionSensorial,
        referencia: str,
        pesos: Dict[str, float] = None,
    ) -> ComparativaReferencia:
        """
        Compara nuestra fórmula con una referencia de mercado.

        Args:
            evaluacion_nuestra: Evaluación de nuestra fórmula
            referencia: Nombre de la referencia ("branca", etc.)
            pesos: Pesos para cada atributo

        Returns:
            ComparativaReferencia: Resultado de la comparativa
        """
        if referencia not in self.referencias:
            raise ValueError(f"Referencia {referencia} no encontrada")

        if pesos is None:
            pesos = {
                "ataque": 0.3,
                "complejidad": 0.25,
                "equilibrio": 0.25,
                "persistencia": 0.2,
            }

        ref_data = self.referencias[referencia]

        # Simular evaluación de referencia (en implementación real, tendríamos datos)
        # Esto es una simplificación
        eval_ref = {
            "ataque": 7.5,
            "complejidad": 8.0,
            "equilibrio": 8.0,
            "persistencia": 8.5,
        }

        # Calcular puntajes ponderados
        puntaje_nuestro = sum(
            pesos.get(attr, 0) * getattr(evaluacion_nuestra, attr, 5) for attr in pesos
        )

        puntaje_ref = sum(pesos.get(attr, 0) * eval_ref.get(attr, 5) for attr in pesos)

        diferencial = puntaje_nuestro - puntaje_ref

        # Determinar atributos ganados/perdidos
        atributos_ganados = []
        atributos_perdidos = []

        for attr in pesos:
            val_nuestro = getattr(evaluacion_nuestra, attr, 5)
            val_ref = eval_ref.get(attr, 5)

            if val_nuestro > val_ref + 0.5:
                atributos_ganados.append(attr)
            elif val_nuestro < val_ref - 0.5:
                atributos_perdidos.append(attr)

        # Confianza basada en número de atributos ganados
        confianza = len(atributos_ganados) / len(pesos)

        return ComparativaReferencia(
            referencia=referencia,
            nuestro_codigo=evaluacion_nuestra.id,
            referencia_codigo=f"REF-{referencia}",
            atributos_ganados=atributos_ganados,
            atributos_perdidos=atributos_perdidos,
            puntaje_diferencial=diferencial,
            superioridad_detectada=diferencial > 0.5,
            confianza=confianza,
        )

    def recomendar_ajustes(self, comparativa: ComparativaReferencia) -> List[str]:
        """
        Recomienda ajustes basados en comparativa.

        Args:
            comparativa: Resultado de comparativa

        Returns:
            List[str]: Recomendaciones de ajuste
        """
        recomendaciones = []

        if "ataque" in comparativa.atributos_perdidos:
            recomendaciones.append(
                "Aumentar tintura cítrica o aromática de alto impacto (+0.2-0.5ml)"
            )

        if "persistencia" in comparativa.atributos_perdidos:
            recomendaciones.append(
                "Incrementar ruibarbo o reducir quina para más persistencia"
            )

        if "equilibrio" in comparativa.atributos_perdidos:
            recomendaciones.append(
                "Revisar balance amargor/dulzor - ajustar azúcar ±5g/L"
            )

        if "complejidad" in comparativa.atributos_perdidos:
            recomendaciones.append(
                "Añadir microdosis de tintura de clavo controlado o azafrán"
            )

        return recomendaciones
