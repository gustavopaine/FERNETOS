"""
Tests para evaluation/reportes.py: salidas exportables del modulo de
evaluacion (roadmap, seccion 5.5) - planilla de resultados por
categoria y ficha de cata por muestra. TDD: escritos antes que la
implementacion.

La preparacion de filas (orden, resolucion de nombres, deteccion de
referencias invalidas) se testea directo sobre los helpers puros; el
render a PDF en si solo se verifica como "produce un PDF valido" -
parsear el contenido de un binario PDF no vale la pena para esto.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from evaluation.models import Categoria, Jurado, Muestra, Puntaje, Ranking, RolJurado, SubModalidad
from evaluation.reportes import (
    _filas_ficha_cata,
    _filas_planilla,
    generar_ficha_cata_muestra,
    generar_planilla_resultados_categoria,
)


def _categoria():
    return Categoria(evento_id="EVT-1", familia="fernet", submodalidad=SubModalidad.PURO)


def _muestra(**kwargs):
    return Muestra(categoria_id="CAT-1", **kwargs)


def _jurado(jurado_id, nombre):
    return Jurado(id=jurado_id, nombre=nombre, rol=RolJurado.SOMMELIER)


def _puntaje(muestra_id, jurado_id, valor, comentario=""):
    return Puntaje(
        muestra_id=muestra_id, jurado_id=jurado_id, visual=valor, aroma=valor,
        sabor_boca=valor, comentario_libre=comentario,
    )


# --- _filas_planilla ---------------------------------------------------


def test_filas_planilla_ordena_por_posicion_aunque_el_ranking_venga_desordenado():
    m1, m2 = _muestra(), _muestra()
    ranking = [
        Ranking(categoria_id="CAT-1", muestra_id=m1.id, puntaje_final=5.0, posicion=2),
        Ranking(categoria_id="CAT-1", muestra_id=m2.id, puntaje_final=9.0, posicion=1),
    ]

    filas = _filas_planilla([m1, m2], ranking)

    assert [f[0] for f in filas] == [1, 2]
    assert [f[1] for f in filas] == [m2.codigo_ciego, m1.codigo_ciego]


def test_filas_planilla_muestra_desconocida_en_ranking_lanza_identificandola():
    m1 = _muestra()
    ranking = [Ranking(categoria_id="CAT-1", muestra_id="MST-FANTASMA", puntaje_final=5.0, posicion=1)]

    with pytest.raises(ValueError, match="MST-FANTASMA"):
        _filas_planilla([m1], ranking)


def test_filas_planilla_categoria_sin_ranking_devuelve_vacio():
    assert _filas_planilla([], []) == []


# --- _filas_ficha_cata ---------------------------------------------------


def test_filas_ficha_cata_resuelve_nombre_de_jurado():
    jurados = [_jurado("J-1", "Ana")]
    puntajes = [_puntaje("M-1", "J-1", 8, comentario="Buen balance")]

    filas = _filas_ficha_cata(puntajes, jurados)

    assert filas[0][0] == "Ana"
    assert filas[0][1:4] == (8, 8, 8)
    assert filas[0][5] == "Buen balance"


def test_filas_ficha_cata_jurado_desconocido_usa_el_id_como_fallback():
    puntajes = [_puntaje("M-1", "J-FANTASMA", 5)]

    filas = _filas_ficha_cata(puntajes, jurados=[])

    assert filas[0][0] == "J-FANTASMA"


def test_filas_ficha_cata_sin_puntajes_devuelve_vacio():
    assert _filas_ficha_cata([], jurados=[]) == []


# --- generar_planilla_resultados_categoria / generar_ficha_cata_muestra ---


def test_generar_planilla_resultados_produce_pdf_valido():
    categoria = _categoria()
    m1, m2 = _muestra(), _muestra()
    ranking = [
        Ranking(categoria_id=categoria.id, muestra_id=m1.id, puntaje_final=9.0, posicion=1),
        Ranking(categoria_id=categoria.id, muestra_id=m2.id, puntaje_final=5.0, posicion=2),
    ]

    pdf = generar_planilla_resultados_categoria(categoria, [m1, m2], ranking)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_generar_planilla_resultados_categoria_sin_muestras_no_lanza():
    pdf = generar_planilla_resultados_categoria(_categoria(), [], [])
    assert pdf.startswith(b"%PDF")


def test_generar_ficha_cata_muestra_produce_pdf_valido():
    muestra = _muestra()
    jurados = [_jurado("J-1", "Ana"), _jurado("J-2", "Beto")]
    puntajes = [
        _puntaje(muestra.id, "J-1", 8, comentario="Rico"),
        _puntaje(muestra.id, "J-2", 6),
    ]

    pdf = generar_ficha_cata_muestra(muestra, puntajes, jurados, puntaje_final=7.1)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500
