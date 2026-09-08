"""
Tests para evaluation/ranking.py: calcula el Ranking de una categoria a
partir de los Puntaje de sus muestras. TDD: escritos antes que la
implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from evaluation.models import Jurado, Puntaje, RolJurado
from evaluation.ranking import calcular_ranking


def _puntaje(muestra_id, jurado_id, valor):
    return Puntaje(
        muestra_id=muestra_id, jurado_id=jurado_id, visual=valor, aroma=valor, sabor_boca=valor
    )


def _jurado(jurado_id):
    return Jurado(id=jurado_id, nombre=jurado_id, rol=RolJurado.SOMMELIER)


def test_calcular_ranking_categoria_sin_muestras_devuelve_lista_vacia():
    assert calcular_ranking("CAT-1", puntajes_por_muestra={}, jurados=[]) == []


def test_calcular_ranking_ordena_de_mayor_a_menor_y_asigna_posiciones():
    jurados = [_jurado("J-1"), _jurado("J-2")]
    puntajes_por_muestra = {
        "M-BAJA": [_puntaje("M-BAJA", "J-1", 3), _puntaje("M-BAJA", "J-2", 3)],
        "M-ALTA": [_puntaje("M-ALTA", "J-1", 9), _puntaje("M-ALTA", "J-2", 9)],
        "M-MEDIA": [_puntaje("M-MEDIA", "J-1", 6), _puntaje("M-MEDIA", "J-2", 6)],
    }

    ranking = calcular_ranking("CAT-1", puntajes_por_muestra, jurados)

    assert [r.muestra_id for r in ranking] == ["M-ALTA", "M-MEDIA", "M-BAJA"]
    assert [r.posicion for r in ranking] == [1, 2, 3]
    assert all(r.categoria_id == "CAT-1" for r in ranking)
    assert ranking[0].puntaje_final > ranking[1].puntaje_final > ranking[2].puntaje_final


def test_calcular_ranking_muestra_sin_puntajes_lanza_identificandola():
    jurados = [_jurado("J-1")]
    puntajes_por_muestra = {
        "M-CON-PUNTAJES": [_puntaje("M-CON-PUNTAJES", "J-1", 8)],
        "M-SIN-PUNTAJES": [],
    }

    with pytest.raises(ValueError, match="M-SIN-PUNTAJES"):
        calcular_ranking("CAT-1", puntajes_por_muestra, jurados)


def test_calcular_ranking_propaga_podar_outliers():
    jurados = [_jurado(f"J-{i}") for i in range(1, 5)]
    # M-1: consistente en 5 (promedio 5.0 con o sin poda). M-2: tres
    # jurados en 4 mas un jurado muy indulgente en 10 -> promedio sin
    # podar 5.5 (gana), promedio podado (se descartan el min y el max)
    # 4.0 (pierde).
    puntajes_por_muestra = {
        "M-1": [_puntaje("M-1", f"J-{i}", 5) for i in range(1, 5)],
        "M-2": [
            _puntaje("M-2", "J-1", 4),
            _puntaje("M-2", "J-2", 4),
            _puntaje("M-2", "J-3", 4),
            _puntaje("M-2", "J-4", 10),
        ],
    }

    con_poda = calcular_ranking("CAT-1", puntajes_por_muestra, jurados, podar_outliers=True)
    sin_poda = calcular_ranking("CAT-1", puntajes_por_muestra, jurados, podar_outliers=False)

    assert con_poda[0].muestra_id == "M-1"  # poda descarta el 10 atipico de M-2
    assert sin_poda[0].muestra_id == "M-2"  # sin poda, el 10 atipico infla el promedio
