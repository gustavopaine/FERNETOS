"""
Tests para evaluation/scoring.py: agregacion de puntajes de varios
jurados en un puntaje final por muestra, con poda opcional de outliers
(media recortada, roadmap seccion 5.3) y peso por jurado (peso_voto).
TDD: escritos antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from evaluation.models import Jurado, Puntaje, RolJurado
from evaluation.scoring import puntaje_final_muestra


def _puntaje(jurado_id, visual, aroma, sabor_boca):
    return Puntaje(
        muestra_id="M-1", jurado_id=jurado_id, visual=visual, aroma=aroma, sabor_boca=sabor_boca
    )


def _jurado(jurado_id, peso_voto=1.0):
    return Jurado(id=jurado_id, nombre=jurado_id, rol=RolJurado.SOMMELIER, peso_voto=peso_voto)


def test_puntaje_final_sin_puntajes_lanza():
    with pytest.raises(ValueError):
        puntaje_final_muestra([], jurados=[])


def test_puntaje_final_jurado_desconocido_lanza():
    puntajes = [_puntaje("J-1", 10, 10, 10)]
    with pytest.raises(ValueError):
        puntaje_final_muestra(puntajes, jurados=[])


def test_puntaje_final_sin_poda_es_promedio_ponderado_por_peso_voto():
    puntajes = [_puntaje("J-1", 10, 10, 10), _puntaje("J-2", 2, 2, 2)]
    jurados = [_jurado("J-1", peso_voto=2.0), _jurado("J-2", peso_voto=1.0)]

    resultado = puntaje_final_muestra(puntajes, jurados, podar_outliers=False)

    # J-1 pondera 10.0, J-2 pondera 2.0; peso 2 y 1 -> (10*2 + 2*1) / 3
    assert resultado == pytest.approx((10.0 * 2 + 2.0 * 1) / 3)


def test_puntaje_final_con_menos_de_3_puntajes_no_poda_aunque_se_pida():
    puntajes = [_puntaje("J-1", 10, 10, 10), _puntaje("J-2", 2, 2, 2)]
    jurados = [_jurado("J-1"), _jurado("J-2")]

    resultado = puntaje_final_muestra(puntajes, jurados, podar_outliers=True)

    assert resultado == pytest.approx((10.0 + 2.0) / 2)


def test_puntaje_final_con_poda_descarta_el_mas_alto_y_el_mas_bajo():
    puntajes = [
        _puntaje("J-1", 1, 1, 1),  # ponderado 1.0 - mas bajo, se descarta
        _puntaje("J-2", 5, 5, 5),  # ponderado 5.0
        _puntaje("J-3", 6, 6, 6),  # ponderado 6.0
        _puntaje("J-4", 10, 10, 10),  # ponderado 10.0 - mas alto, se descarta
    ]
    jurados = [_jurado(f"J-{i}") for i in range(1, 5)]

    resultado = puntaje_final_muestra(puntajes, jurados, podar_outliers=True)

    assert resultado == pytest.approx((5.0 + 6.0) / 2)


def test_puntaje_final_poda_es_el_default():
    puntajes = [
        _puntaje("J-1", 1, 1, 1),
        _puntaje("J-2", 5, 5, 5),
        _puntaje("J-3", 6, 6, 6),
        _puntaje("J-4", 10, 10, 10),
    ]
    jurados = [_jurado(f"J-{i}") for i in range(1, 5)]

    assert puntaje_final_muestra(puntajes, jurados) == pytest.approx((5.0 + 6.0) / 2)
