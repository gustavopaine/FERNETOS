"""Tests para modules/ensamblaje/calculator.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from families.fernet.calculator import (
    BlendParams,
    ComposicionBlend,
    FernetCalculator,
)
from core.tintura_models import ParametrosExtraccion, Tintura


@pytest.fixture
def calc():
    return FernetCalculator()


def test_calcular_base_alcohol_agua_10l_40_abv(calc):
    params = BlendParams(volumen_objetivo_litros=10.0, abv_objetivo=40.0)

    alcohol_ml, agua_ml = calc.calcular_base_alcohol_agua(params)

    # Balance de alcohol puro: 10000ml * 40% = alcohol_ml * 96%
    assert alcohol_ml == pytest.approx(4166.6667, abs=0.01)
    assert agua_ml == pytest.approx(5833.3333, abs=0.01)
    assert alcohol_ml + agua_ml == pytest.approx(10000.0, abs=0.01)


def test_calcular_base_alcohol_agua_respeta_alcohol_base_distinto(calc):
    params = BlendParams(
        volumen_objetivo_litros=10.0, abv_objetivo=40.0, alcohol_base_abv=95.0
    )

    alcohol_ml, agua_ml = calc.calcular_base_alcohol_agua(params)

    assert alcohol_ml == pytest.approx(4000 / 0.95, abs=0.01)


def test_calcular_abv_blend_solo_alcohol_base(calc):
    composicion = ComposicionBlend(alcohol_base_ml=4166.6667, agua_base_ml=5833.3333)

    abv = FernetCalculator.calcular_abv_blend(composicion, tinturas_data={})

    assert abv == pytest.approx(40.0, abs=0.05)


def test_calcular_abv_blend_con_tintura_conocida(calc):
    tintura = Tintura(
        nombre="Amargos",
        parametros=ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=18),
    )
    composicion = ComposicionBlend(
        alcohol_base_ml=3750.0,
        agua_base_ml=5750.0,
        tinturas={tintura.id: 250.0},
    )

    abv = FernetCalculator.calcular_abv_blend(
        composicion, tinturas_data={tintura.id: tintura}
    )

    # (3750*0.96 + 250*0.70) / (3750+5750+250) * 100
    esperado = (3750 * 0.96 + 250 * 0.70) / (3750 + 5750 + 250) * 100
    assert abv == pytest.approx(esperado, abs=0.01)


def test_calcular_abv_blend_volumen_cero_no_divide_por_cero(calc):
    composicion = ComposicionBlend()

    abv = FernetCalculator.calcular_abv_blend(composicion, tinturas_data={})

    assert abv == 0.0
