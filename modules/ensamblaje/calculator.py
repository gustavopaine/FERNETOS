"""
Motor de cálculo para ensamblaje de fernet.
Gestiona todos los aspectos cuantitativos del blending.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import copy
import json
import os
import sys

# Ajuste de ruta para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.tinturas.models import Tintura, GrupoFuncional
from modules.ensamblaje.common import abv_resultante
from config.settings import load_settings

# Cargar configuración global
settings = load_settings()


@dataclass
class BlendParams:
    """Parámetros base para un blend"""

    volumen_objetivo_litros: float
    abv_objetivo: float = 40.0
    azucar_objetivo_gpl: int = 195
    alcohol_base_abv: float = 96.0
    ph_objetivo: float = 5.2

    def __post_init__(self):
        self.volumen_objetivo_ml = self.volumen_objetivo_litros * 1000


@dataclass
class ComposicionBlend:
    """Composición de un blend"""

    alcohol_base_ml: float = 0.0
    agua_base_ml: float = 0.0
    tinturas: Dict[str, float] = field(default_factory=dict)  # tintura_id: ml
    azucar_g: float = 0.0

    @property
    def volumen_total_ml(self) -> float:
        return self.alcohol_base_ml + self.agua_base_ml + sum(self.tinturas.values())

    @property
    def volumen_sin_azucar_ml(self) -> float:
        return self.volumen_total_ml


@dataclass
class BlendResult:
    """Resultado de un cálculo de blend"""

    id: str = field(
        default_factory=lambda: f"B-{datetime.now().strftime('%Y%m%d')}-{str(datetime.now().microsecond)[:4]}"
    )
    version: str = "1.0.0"
    params: BlendParams = field(default_factory=BlendParams)
    composicion: ComposicionBlend = field(default_factory=ComposicionBlend)
    abv_calculado: float = 0.0
    azucar_efectiva_gpl: int = 0
    ph_estimado: float = 5.2
    margen_error_ml: float = 0.0
    fecha_calculo: datetime = field(default_factory=datetime.now)

    @property
    def volumen_real_ml(self) -> float:
        return self.composicion.volumen_total_ml + (
            self.composicion.azucar_g * 0.6
        )  # Aprox volumen del azúcar


class FernetCalculator:
    """
    Calculadora principal para ensamblaje de fernet.
    Proporciona métodos para cálculos de ABV, azúcar, escalado y simulaciones.
    """

    def __init__(self, tinturas_repo=None):
        """
        Inicializa la calculadora.

        Args:
            tinturas_repo: Repositorio para acceder a datos de tinturas (opcional)
        """
        self.tinturas_repo = tinturas_repo
        self.settings = settings

    def calcular_base_alcohol_agua(self, params: BlendParams) -> Tuple[float, float]:
        """
        Calcula las proporciones de alcohol base y agua necesarias.

        Args:
            params: Parámetros del blend

        Returns:
            Tuple[float, float]: (alcohol_base_ml, agua_base_ml)
        """
        volumen_total_ml = params.volumen_objetivo_litros * 1000

        # Ecuación de balance de alcohol puro
        # Volumen_total * ABV_objetivo = alcohol_base * ABV_base
        alcohol_puro_necesario = volumen_total_ml * (params.abv_objetivo / 100)
        alcohol_base_ml = alcohol_puro_necesario / (params.alcohol_base_abv / 100)

        # El resto es agua (asumiendo que las tinturas aportan volumen pero su ABV se considera después)
        # Por ahora, calculamos base asumiendo que las tinturas reemplazarán parte del agua
        agua_base_ml = volumen_total_ml - alcohol_base_ml

        return alcohol_base_ml, agua_base_ml

    @staticmethod
    def calcular_abv_blend(
        composicion: ComposicionBlend, tinturas_data: Dict[str, Tintura]
    ) -> float:
        """
        Calcula el ABV final de un blend (sin azúcar).

        Args:
            composicion: Composición del blend
            tinturas_data: Diccionario con datos de tinturas (id -> Tintura)

        Returns:
            float: ABV calculado
        """
        # Componentes que aportan alcohol: (volumen_ml, abv_pct). El agua no
        # se incluye porque su ABV es 0 y no cambia la suma ponderada.
        componentes = [(composicion.alcohol_base_ml, 96.0)]  # alcohol base

        for tid, ml in composicion.tinturas.items():
            if tid in tinturas_data:
                tintura = tinturas_data[tid]
                componentes.append((ml, tintura.parametros.abv_objetivo))
            else:
                # Si no tenemos datos, asumimos 70% (default para tinturas)
                componentes.append((ml, 70.0))

        return abv_resultante(componentes, composicion.volumen_total_ml)

    @staticmethod
    def calcular_azucar(azucar_gpl: int, volumen_lote_ml: float) -> float:
        """
        Calcula los gramos de azúcar necesarios.

        Args:
            azucar_gpl: Gramos de azúcar por litro objetivo
            volumen_lote_ml: Volumen del lote en ml

        Returns:
            float: Gramos de azúcar necesarios
        """
        return (azucar_gpl * volumen_lote_ml) / 1000

    @staticmethod
    def calcular_volumen_con_azucar(
        volumen_sin_azucar_ml: float, azucar_g: float
    ) -> float:
        """
        Calcula el volumen final considerando el aporte del azúcar.
        Aproximación: 1g de azúcar aporta ~0.6 ml de volumen.

        Returns:
            float: Volumen final en ml
        """
        return volumen_sin_azucar_ml + (azucar_g * 0.6)

    def crear_blend_base(
        self, params: BlendParams, reservar_espacio_tinturas_ml: float = 0.0
    ) -> ComposicionBlend:
        """
        Crea una composición base (alcohol + agua) con espacio reservado para tinturas.

        Args:
            params: Parámetros del blend
            reservar_espacio_tinturas_ml: Volumen a reservar para tinturas

        Returns:
            ComposicionBlend: Composición base
        """
        volumen_total_ml = params.volumen_objetivo_litros * 1000

        # El volumen para tinturas reduce el espacio para agua
        volumen_base_ml = volumen_total_ml - reservar_espacio_tinturas_ml

        # Calcular alcohol y agua para ese volumen base
        alcohol_puro_necesario = volumen_base_ml * (params.abv_objetivo / 100)
        alcohol_base_ml = alcohol_puro_necesario / (params.alcohol_base_abv / 100)
        agua_base_ml = volumen_base_ml - alcohol_base_ml

        return ComposicionBlend(
            alcohol_base_ml=alcohol_base_ml, agua_base_ml=agua_base_ml
        )

    def calcular_blend_completo(
        self,
        params: BlendParams,
        tinturas_dict: Dict[str, float],
        tinturas_data: Dict[str, Tintura],
    ) -> BlendResult:
        """
        Calcula un blend completo con tinturas incluidas.

        Args:
            params: Parámetros del blend
            tinturas_dict: Diccionario {tintura_id: ml}
            tinturas_data: Datos completos de las tinturas

        Returns:
            BlendResult: Resultado completo del cálculo
        """
        # Volumen total de tinturas
        volumen_tinturas = sum(tinturas_dict.values())

        # Crear base con espacio para tinturas
        composicion = self.crear_blend_base(params, volumen_tinturas)
        composicion.tinturas = tinturas_dict.copy()

        # Calcular ABV
        abv = self.calcular_abv_blend(composicion, tinturas_data)

        # Calcular azúcar
        azucar_g = self.calcular_azucar(
            params.azucar_objetivo_gpl, params.volumen_objetivo_ml
        )
        composicion.azucar_g = azucar_g

        # Volumen final real
        volumen_final = self.calcular_volumen_con_azucar(
            composicion.volumen_total_ml, azucar_g
        )
        margen_error = volumen_final - params.volumen_objetivo_ml

        return BlendResult(
            params=params,
            composicion=composicion,
            abv_calculado=abv,
            azucar_efectiva_gpl=params.azucar_objetivo_gpl,
            ph_estimado=params.ph_objetivo,
            margen_error_ml=margen_error,
        )

    def escalar_blend(
        self, blend_result: BlendResult, nuevo_volumen_litros: float
    ) -> BlendResult:
        """
        Escala un blend a un nuevo volumen manteniendo proporciones.

        Args:
            blend_result: Blend original
            nuevo_volumen_litros: Nuevo volumen objetivo

        Returns:
            BlendResult: Blend escalado
        """
        # Factor de escala
        factor = nuevo_volumen_litros / blend_result.params.volumen_objetivo_litros

        # Crear nuevos parámetros
        nuevos_params = copy.deepcopy(blend_result.params)
        nuevos_params.volumen_objetivo_litros = nuevo_volumen_litros

        # Escalar composición
        nueva_composicion = ComposicionBlend(
            alcohol_base_ml=blend_result.composicion.alcohol_base_ml * factor,
            agua_base_ml=blend_result.composicion.agua_base_ml * factor,
            azucar_g=blend_result.composicion.azucar_g * factor,
        )

        # Escalar tinturas
        for tid, ml in blend_result.composicion.tinturas.items():
            nueva_composicion.tinturas[tid] = ml * factor

        # Nuevo resultado
        nuevo_result = BlendResult(
            id=f"{blend_result.id}-ESC",
            version=self._incrementar_version(blend_result.version, "scale"),
            params=nuevos_params,
            composicion=nueva_composicion,
            abv_calculado=blend_result.abv_calculado,  # Debería mantenerse
            azucar_efectiva_gpl=blend_result.azucar_efectiva_gpl,
            ph_estimado=blend_result.ph_estimado,
            margen_error_ml=0.0,  # Recalcular después
        )

        # Recalcular volumen final
        volumen_final = self.calcular_volumen_con_azucar(
            nueva_composicion.volumen_total_ml, nueva_composicion.azucar_g
        )
        nuevo_result.margen_error_ml = volumen_final - (nuevo_volumen_litros * 1000)

        return nuevo_result

    def _incrementar_version(self, version: str, tipo_cambio: str) -> str:
        """Incrementa versión según tipo de cambio"""
        major, minor, patch = map(int, version.split("."))

        if tipo_cambio == "major":
            return f"{major+1}.0.0"
        elif tipo_cambio == "minor":
            return f"{major}.{minor+1}.0"
        else:  # patch o scale
            return f"{major}.{minor}.{patch+1}"

    @staticmethod
    def calcular_porcentaje_tinturas(composicion: ComposicionBlend) -> Dict[str, float]:
        """
        Calcula el porcentaje que representa cada tintura sobre el total.

        Returns:
            Dict[str, float]: {tintura_id: porcentaje}
        """
        total = composicion.volumen_total_ml
        if total == 0:
            return {}

        return {tid: (ml / total) * 100 for tid, ml in composicion.tinturas.items()}


class ImpactSimulator:
    """
    Simulador de impacto de modificaciones en blends.
    Especialmente útil para microblending en lotes piloto.
    """

    def __init__(self, calculator: FernetCalculator):
        self.calculator = calculator

    def simular_incremento_tintura(
        self,
        blend: BlendResult,
        tintura_id: str,
        incremento_ml: float,
        batch_ml: int = 500,
    ) -> BlendResult:
        """
        Simula el efecto de añadir X ml de una tintura en un lote piloto.

        Args:
            blend: Blend original
            tintura_id: ID de la tintura a modificar
            incremento_ml: Incremento en ml (puede ser negativo)
            batch_ml: Tamaño del lote piloto en ml (default: 500ml)

        Returns:
            BlendResult: Blend modificado
        """
        # Escalar el blend al tamaño del lote piloto
        factor_piloto = batch_ml / blend.composicion.volumen_total_ml

        # Crear blend piloto
        blend_piloto = self.calculator.escalar_blend(blend, batch_ml / 1000)

        # Aplicar incremento
        if tintura_id in blend_piloto.composicion.tinturas:
            blend_piloto.composicion.tinturas[tintura_id] += incremento_ml
        else:
            blend_piloto.composicion.tinturas[tintura_id] = incremento_ml

        # Ajustar base para mantener volumen (opcional)
        # Por simplicidad, no ajustamos base, el volumen total cambiará

        # Recalcular ABV (necesitaríamos tinturas_data, aquí simplificamos)
        # En implementación real, se necesitaría acceso a repositorio

        return blend_piloto

    def simular_ajuste_azucar(
        self, blend: BlendResult, nuevo_azucar_gpl: int, batch_ml: int = 500
    ) -> BlendResult:
        """
        Simula cambio en nivel de azúcar.

        Args:
            blend: Blend original
            nuevo_azucar_gpl: Nuevo nivel de azúcar en g/L
            batch_ml: Tamaño del lote piloto

        Returns:
            BlendResult: Blend con nuevo azúcar
        """
        # Escalar a piloto
        blend_piloto = self.calculator.escalar_blend(blend, batch_ml / 1000)

        # Actualizar azúcar
        blend_piloto.params.azucar_objetivo_gpl = nuevo_azucar_gpl
        blend_piloto.azucar_efectiva_gpl = nuevo_azucar_gpl
        blend_piloto.composicion.azucar_g = self.calculator.calcular_azucar(
            nuevo_azucar_gpl, batch_ml
        )

        return blend_piloto

    def comparar_escenarios(
        self, blend_base: BlendResult, modificaciones: List[Tuple[str, float]]
    ) -> Dict[str, BlendResult]:
        """
        Genera múltiples escenarios para comparación.

        Args:
            blend_base: Blend base
            modificaciones: Lista de (tintura_id, incremento_ml)

        Returns:
            Dict[str, BlendResult]: Escenarios con nombres
        """
        escenarios = {"base": blend_base}

        for i, (tid, inc) in enumerate(modificaciones):
            nombre = f"escenario_{i+1}_{tid.replace('-', '')}_{inc:+.1f}"
            escenarios[nombre] = self.simular_incremento_tintura(blend_base, tid, inc)

        return escenarios


class SugarOptimizer:
    """
    Optimizador de niveles de azúcar para competencia.
    """

    def __init__(self, calculator: FernetCalculator):
        self.calculator = calculator

    def probar_rangos(
        self, blend_base: BlendResult, rangos: List[int], batch_ml: int = 500
    ) -> List[BlendResult]:
        """
        Genera blends con diferentes niveles de azúcar.

        Args:
            blend_base: Blend base
            rangos: Lista de valores g/L a probar
            batch_ml: Tamaño del lote piloto

        Returns:
            List[BlendResult]: Blends con diferentes azúcares
        """
        resultados = []

        for azucar in rangos:
            blend_mod = copy.deepcopy(blend_base)
            blend_mod.params.azucar_objetivo_gpl = azucar
            blend_mod.azucar_efectiva_gpl = azucar
            blend_mod.composicion.azucar_g = self.calculator.calcular_azucar(
                azucar, batch_ml
            )
            blend_mod.id = f"{blend_base.id}-SUG{azucar}"
            resultados.append(blend_mod)

        return resultados

    def elegir_competitivo(
        self,
        blends: List[BlendResult],
        referencia: str = "branca",
        preferencias: Dict[str, float] = None,
    ) -> BlendResult:
        """
        Selecciona el blend más competitivo basado en criterios.

        Args:
            blends: Lista de blends a evaluar
            referencia: Referencia de mercado
            preferencias: Dict con pesos para atributos

        Returns:
            BlendResult: Blend seleccionado
        """
        if preferencias is None:
            preferencias = {"ataque": 0.3, "equilibrio": 0.4, "persistencia": 0.3}

        # En implementación real, esto usaría datos de catas
        # Por ahora, seleccionamos el del medio (lógica placeholder)
        mid_index = len(blends) // 2
        return blends[mid_index]
