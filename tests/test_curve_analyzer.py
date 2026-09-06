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

from modules.curvas.analyzer import CurveAnalyzer
from modules.tinturas.models import GrupoFuncional, Producto, RegistroExtraccion, Tintura


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
