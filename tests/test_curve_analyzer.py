"""
Tests para modules/curvas/analyzer.py: heurística de día de corte.

Fase 2 dejó pendiente una heurística real para los grupos de Gancia (sin
inventar días sin datos propios). El usuario aportó el dato real de su
receta de Gancia casero: 40 días de maceración, agitación cada 2 días.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.curve_analysis import CurveAnalyzer
from core.tintura_models import GrupoFuncional, Producto, RegistroExtraccion, Tintura


def _tintura_gancia(grupo):
    return Tintura(
        nombre="Gancia Casero",
        producto=Producto.GANCIA,
        grupo_funcional=grupo,
    )


def _con_un_registro(tintura, dia, intensidad=40):
    tintura.agregar_registro_extraccion(
        RegistroExtraccion(
            dia=dia,
            fecha=datetime.now(),
            intensidad_estimada=intensidad,
            notas_sensoriales="",
            compuestos_detectados=[],
        )
    )
    return tintura


def test_sugerir_dia_corte_gancia_antes_de_40_dias_sugiere_40():
    tintura = _con_un_registro(_tintura_gancia(GrupoFuncional.CITRICOS_AMARGOS), dia=10)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 40


def test_sugerir_dia_corte_gancia_despues_de_40_dias_sugiere_dia_actual():
    tintura = _con_un_registro(_tintura_gancia(GrupoFuncional.BOTANICOS_AROMATICOS), dia=45)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 45


def test_sugerir_dia_corte_gancia_aplica_a_especiado_suave():
    tintura = _con_un_registro(_tintura_gancia(GrupoFuncional.ESPECIADO_SUAVE), dia=5)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 40


def test_sugerir_dia_corte_gancia_exactamente_40_dias_sugiere_40():
    tintura = _con_un_registro(_tintura_gancia(GrupoFuncional.CITRICOS_AMARGOS), dia=40)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 40


# --- Grupos compartidos entre productos (Campari reutiliza taxonomía de
# Fernet/Gancia): la heurística tuneada para un producto no debe
# aplicarse a otro solo porque el grupo coincide. ---


def test_sugerir_dia_corte_fernet_con_amargos_sigue_igual():
    """Guardrail de regresión: el fix para no confundir productos no debe
    romper la heurística real de Fernet."""
    tintura = Tintura(
        nombre="Amargos Fernet",
        producto=Producto.FERNET,
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
    )
    _con_un_registro(tintura, dia=10)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 12  # min(21, 10+2)


def test_analizar_completo_maneja_dia_optimo_cero():
    """Regresión: un chequeo truthy trataba día 0 (día de corte legítimo)
    como "sin día sugerido" y saltaba el cálculo de intensidad_optima y
    tiempo_estabilizacion. Campari no tiene estrategia de día de corte
    registrada, así que con un único registro en día 0 el fallback de
    sugerir_dia_corte() devuelve 0."""
    tintura = Tintura(
        nombre="Campari sin heurística propia",
        producto=Producto.CAMPARI,
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
    )
    _con_un_registro(tintura, dia=0, intensidad=15)
    analyzer = CurveAnalyzer(tintura)

    analisis = analyzer.analizar_completo()

    assert analisis.dia_optimo_sugerido == 0
    assert analisis.intensidad_optima == 15
    assert analisis.tiempo_estabilizacion == 15


def test_sugerir_dia_corte_campari_con_amargos_no_usa_heuristica_de_fernet():
    """AMARGOS_ESTRUCTURALES es compartido con Campari - el timing 16-21
    días es específico de Fernet y no debe aplicarse acá."""
    tintura = Tintura(
        nombre="Amargos Campari",
        producto=Producto.CAMPARI,
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
    )
    _con_un_registro(tintura, dia=10)
    analyzer = CurveAnalyzer(tintura)
    # Sin dato real de maceración para Campari todavía: cae al fallback
    # genérico (día del último registro), no a min(21, 10+2)=12 de Fernet.
    assert analyzer.sugerir_dia_corte() == 10


def test_sugerir_dia_corte_campari_con_citricos_amargos_no_usa_heuristica_de_gancia():
    """CITRICOS_AMARGOS es compartido con Gancia - los 40 días de la
    receta de Gancia casero no deben aplicarse a Campari."""
    tintura = Tintura(
        nombre="Cítricos Campari",
        producto=Producto.CAMPARI,
        grupo_funcional=GrupoFuncional.CITRICOS_AMARGOS,
    )
    _con_un_registro(tintura, dia=10)
    analyzer = CurveAnalyzer(tintura)
    assert analyzer.sugerir_dia_corte() == 10
