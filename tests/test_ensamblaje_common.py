"""Tests para modules/ensamblaje/common.py: helper de balance de alcohol
compartido entre FernetCalculator y GanciaCalculator."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.ensamblaje.common import abv_resultante, alcohol_puro_total


def test_alcohol_puro_total_un_componente():
    assert alcohol_puro_total([(1000.0, 40.0)]) == pytest.approx(400.0)


def test_alcohol_puro_total_varios_componentes():
    # 3750ml al 96% + 250ml al 70%
    assert alcohol_puro_total([(3750.0, 96.0), (250.0, 70.0)]) == pytest.approx(
        3750 * 0.96 + 250 * 0.70
    )


def test_alcohol_puro_total_sin_componentes_es_cero():
    assert alcohol_puro_total([]) == 0.0


def test_abv_resultante_calcula_porcentaje():
    # 4166.67ml al 96% + 5833.33ml de agua (0%) -> ~40% ABV en 10000ml
    componentes = [(4166.6667, 96.0), (5833.3333, 0.0)]
    assert abv_resultante(componentes, 10000.0) == pytest.approx(40.0, abs=0.01)


def test_abv_resultante_volumen_cero_no_divide_por_cero():
    assert abv_resultante([(100.0, 40.0)], 0.0) == 0.0
