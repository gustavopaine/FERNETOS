"""Tests para modules/ensamblaje/calculator_gancia.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.ensamblaje.calculator_gancia import (
    ComposicionBlendGancia,
    GanciaBlendParams,
    GanciaCalculator,
)
from modules.tinturas.models import ParametrosExtraccion, Producto, Tintura


@pytest.fixture
def calc():
    return GanciaCalculator()


def test_calcular_base_vino_alcohol_10l_78pct_vino_17_abv(calc):
    params = GanciaBlendParams(
        volumen_objetivo_litros=10.0,
        abv_objetivo=17.0,
        vino_pct=0.78,
        vino_abv=12.0,
        alcohol_fortificacion_abv=96.0,
    )

    vino_ml, alcohol_ml, agua_ml = calc.calcular_base_vino_alcohol(params)

    assert vino_ml == pytest.approx(7800.0)
    # alcohol puro faltante: 10000*0.17 - 7800*0.12 = 1700 - 936 = 764
    assert alcohol_ml == pytest.approx(764 / 0.96, abs=0.01)
    assert vino_ml + alcohol_ml + agua_ml == pytest.approx(10000.0, abs=0.01)


def test_calcular_base_vino_alcohol_descuenta_volumen_de_tinturas(calc):
    params = GanciaBlendParams(volumen_objetivo_litros=10.0, vino_pct=0.78)

    vino_ml, alcohol_ml, agua_ml = calc.calcular_base_vino_alcohol(
        params, tinturas_ml_total=200.0
    )

    assert vino_ml + alcohol_ml + agua_ml + 200.0 == pytest.approx(10000.0, abs=0.01)


def test_calcular_abv_blend_solo_vino_y_fortificacion(calc):
    composicion = ComposicionBlendGancia(
        vino_ml=7800.0, alcohol_fortificacion_ml=795.8333, agua_ml=1404.1667
    )

    abv = GanciaCalculator.calcular_abv_blend(
        composicion, tinturas_data={}, vino_abv=12.0, alcohol_fortificacion_abv=96.0
    )

    assert abv == pytest.approx(17.0, abs=0.05)


def test_calcular_abv_blend_con_tintura_conocida(calc):
    tintura = Tintura(
        nombre="Quinado Base",
        producto=Producto.GANCIA,
        parametros=ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=10),
    )
    composicion = ComposicionBlendGancia(
        vino_ml=7800.0,
        alcohol_fortificacion_ml=700.0,
        tinturas={tintura.id: 100.0},
    )

    abv = GanciaCalculator.calcular_abv_blend(
        composicion, tinturas_data={tintura.id: tintura}, vino_abv=12.0, alcohol_fortificacion_abv=96.0
    )

    esperado = (7800 * 0.12 + 700 * 0.96 + 100 * 0.70) / (7800 + 700 + 100) * 100
    assert abv == pytest.approx(esperado, abs=0.01)


def test_calcular_abv_blend_volumen_cero_no_divide_por_cero(calc):
    composicion = ComposicionBlendGancia()

    abv = GanciaCalculator.calcular_abv_blend(
        composicion, tinturas_data={}, vino_abv=12.0, alcohol_fortificacion_abv=96.0
    )

    assert abv == 0.0


@pytest.mark.parametrize("pct_wv,volumen_ml,esperado_g", [(10.0, 10000.0, 1000.0), (8.0, 5000.0, 400.0)])
def test_calcular_azucar_porcentaje_peso_volumen(pct_wv, volumen_ml, esperado_g):
    assert GanciaCalculator.calcular_azucar(pct_wv, volumen_ml) == pytest.approx(esperado_g)


def test_calcular_volumen_con_azucar_agrega_aporte_de_la_azucar():
    # 10000ml sin azúcar + 1000g de azúcar seca * 0.6ml/g = 10600ml reales
    assert GanciaCalculator.calcular_volumen_con_azucar(10000.0, 1000.0) == pytest.approx(
        10600.0
    )
