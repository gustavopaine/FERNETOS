"""
Tests para evaluation/blind_coding.py: orden de cata aleatorizado por
jurado (roadmap seccion 5.3 - "cada jurado recibe las muestras en un
orden distinto"). TDD: escritos antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.blind_coding import orden_cata_para_jurado
from evaluation.models import Muestra


def _muestras(n):
    return [Muestra(categoria_id="CAT-1") for _ in range(n)]


def test_orden_vacio_no_lanza():
    assert orden_cata_para_jurado([], jurado_id="J-1") == []


def test_orden_es_permutacion_de_las_muestras():
    muestras = _muestras(6)
    orden = orden_cata_para_jurado(muestras, jurado_id="J-1")

    assert len(orden) == len(muestras)
    assert {m.id for m in orden} == {m.id for m in muestras}


def test_orden_no_muta_la_lista_original():
    muestras = _muestras(6)
    original = list(muestras)

    orden_cata_para_jurado(muestras, jurado_id="J-1")

    assert muestras == original


def test_orden_es_deterministico_para_el_mismo_jurado():
    muestras = _muestras(8)

    orden_a = orden_cata_para_jurado(muestras, jurado_id="J-1")
    orden_b = orden_cata_para_jurado(muestras, jurado_id="J-1")

    assert [m.id for m in orden_a] == [m.id for m in orden_b]


def test_ordenes_distintos_para_jurados_distintos():
    muestras = _muestras(8)

    orden_j1 = orden_cata_para_jurado(muestras, jurado_id="J-1")
    orden_j2 = orden_cata_para_jurado(muestras, jurado_id="J-2")

    assert [m.id for m in orden_j1] != [m.id for m in orden_j2]
