"""
Tests para evaluation/progreso.py: cuantos puntajes faltan para poder
cerrar la ronda de una categoria (roadmap, seccion 5.4, "planilla de
puntajes en vivo"). TDD: escritos antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.models import Jurado, Muestra, Puntaje, RolJurado
from evaluation.progreso import calcular_progreso_categoria


def _muestra():
    return Muestra(categoria_id="CAT-1")


def _jurado(jurado_id):
    return Jurado(id=jurado_id, nombre=jurado_id, rol=RolJurado.SOMMELIER)


def _puntaje(muestra_id, jurado_id):
    return Puntaje(muestra_id=muestra_id, jurado_id=jurado_id, visual=5, aroma=5, sabor_boca=5)


def test_categoria_sin_muestras_ni_jurados_no_espera_nada():
    progreso = calcular_progreso_categoria([], [], [])
    assert progreso.puntajes_esperados == 0
    assert progreso.puntajes_cargados == 0
    assert progreso.pendientes == []


def test_categoria_sin_ningun_puntaje_todo_pendiente():
    m1, m2 = _muestra(), _muestra()
    j1, j2 = _jurado("J-1"), _jurado("J-2")

    progreso = calcular_progreso_categoria([m1, m2], [j1, j2], [])

    assert progreso.puntajes_esperados == 4
    assert progreso.puntajes_cargados == 0
    assert set(progreso.pendientes) == {
        (m1.id, "J-1"), (m1.id, "J-2"), (m2.id, "J-1"), (m2.id, "J-2"),
    }


def test_categoria_parcialmente_puntuada():
    m1, m2 = _muestra(), _muestra()
    j1, j2 = _jurado("J-1"), _jurado("J-2")
    puntajes = [_puntaje(m1.id, "J-1")]

    progreso = calcular_progreso_categoria([m1, m2], [j1, j2], puntajes)

    assert progreso.puntajes_esperados == 4
    assert progreso.puntajes_cargados == 1
    assert set(progreso.pendientes) == {(m1.id, "J-2"), (m2.id, "J-1"), (m2.id, "J-2")}


def test_categoria_completa_sin_pendientes():
    m1 = _muestra()
    j1, j2 = _jurado("J-1"), _jurado("J-2")
    puntajes = [_puntaje(m1.id, "J-1"), _puntaje(m1.id, "J-2")]

    progreso = calcular_progreso_categoria([m1], [j1, j2], puntajes)

    assert progreso.puntajes_esperados == 2
    assert progreso.puntajes_cargados == 2
    assert progreso.pendientes == []


def test_puntaje_de_jurado_no_reconocido_no_cuenta_como_cargado():
    """Un Puntaje que referencia un jurado_id fuera de la lista de
    jurados de la categoria (dato inconsistente) no debe contarse como
    progreso valido - la fuente de verdad de "quien deberia puntuar"
    es la lista de jurados, no los puntajes ya cargados."""
    m1 = _muestra()
    j1 = _jurado("J-1")
    puntajes = [_puntaje(m1.id, "J-FANTASMA")]

    progreso = calcular_progreso_categoria([m1], [j1], puntajes)

    assert progreso.puntajes_cargados == 0
    assert progreso.pendientes == [(m1.id, "J-1")]
