"""
Tests para evaluation/cierre_ronda.py: servicio que conecta los
repositorios SQL de evaluacion con el calculo de ranking (roadmap,
seccion 5.3, "cuando el organizador cierra oficialmente la ronda").
TDD: escritos antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from evaluation.models import Categoria, Evento, Jurado, Muestra, Puntaje, RolJurado, SubModalidad
from evaluation.repository import (
    CategoriaRepository,
    EventoRepository,
    JuradoRepository,
    MuestraRepository,
    PuntajeRepository,
    RankingRepository,
)
from evaluation.cierre_ronda import cerrar_ronda_categoria


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )


def _crear_categoria(db) -> Categoria:
    evento = Evento(nombre="E1", fecha="2026-11-15", sede="X", edicion_numero=1)
    EventoRepository(db).guardar(evento)
    categoria = Categoria(evento_id=evento.id, familia="fernet", submodalidad=SubModalidad.PURO)
    CategoriaRepository(db).guardar(categoria)
    return categoria


def _crear_muestra(db, categoria_id) -> Muestra:
    muestra = Muestra(categoria_id=categoria_id)
    MuestraRepository(db).guardar(muestra)
    return muestra


def _crear_jurado(db) -> Jurado:
    jurado = Jurado(nombre="Ana", rol=RolJurado.SOMMELIER)
    JuradoRepository(db).guardar(jurado)
    return jurado


def _puntuar(db, muestra_id, jurado_id, valor):
    puntaje = Puntaje(
        muestra_id=muestra_id, jurado_id=jurado_id, visual=valor, aroma=valor, sabor_boca=valor
    )
    PuntajeRepository(db).guardar(puntaje)


def test_cerrar_ronda_categoria_sin_muestras_devuelve_vacio_y_no_persiste(db):
    categoria = _crear_categoria(db)

    resultado = cerrar_ronda_categoria(
        categoria.id,
        MuestraRepository(db),
        PuntajeRepository(db),
        JuradoRepository(db),
        RankingRepository(db),
    )

    assert resultado == []
    assert RankingRepository(db).listar(categoria.id) == []


def test_cerrar_ronda_categoria_calcula_y_persiste_el_ranking(db):
    categoria = _crear_categoria(db)
    jurado = _crear_jurado(db)
    m_alta = _crear_muestra(db, categoria.id)
    m_baja = _crear_muestra(db, categoria.id)
    _puntuar(db, m_alta.id, jurado.id, 9)
    _puntuar(db, m_baja.id, jurado.id, 3)

    resultado = cerrar_ronda_categoria(
        categoria.id,
        MuestraRepository(db),
        PuntajeRepository(db),
        JuradoRepository(db),
        RankingRepository(db),
    )

    assert [r.muestra_id for r in resultado] == [m_alta.id, m_baja.id]
    assert [r.posicion for r in resultado] == [1, 2]

    persistido = RankingRepository(db).listar(categoria.id)
    assert [(r.muestra_id, r.posicion) for r in persistido] == [(m_alta.id, 1), (m_baja.id, 2)]


def test_cerrar_ronda_categoria_con_muestra_sin_puntajes_lanza_identificandola(db):
    categoria = _crear_categoria(db)
    jurado = _crear_jurado(db)
    m_puntuada = _crear_muestra(db, categoria.id)
    m_sin_puntaje = _crear_muestra(db, categoria.id)
    _puntuar(db, m_puntuada.id, jurado.id, 8)

    with pytest.raises(ValueError, match=m_sin_puntaje.id):
        cerrar_ronda_categoria(
            categoria.id,
            MuestraRepository(db),
            PuntajeRepository(db),
            JuradoRepository(db),
            RankingRepository(db),
        )


def test_cerrar_ronda_categoria_recalculo_actualiza_ranking_persistido(db):
    categoria = _crear_categoria(db)
    jurado = _crear_jurado(db)
    m1 = _crear_muestra(db, categoria.id)
    m2 = _crear_muestra(db, categoria.id)
    _puntuar(db, m1.id, jurado.id, 5)
    _puntuar(db, m2.id, jurado.id, 9)

    repos = (
        MuestraRepository(db),
        PuntajeRepository(db),
        JuradoRepository(db),
        RankingRepository(db),
    )
    cerrar_ronda_categoria(categoria.id, *repos)
    assert [r.muestra_id for r in RankingRepository(db).listar(categoria.id)] == [m2.id, m1.id]

    # Un jurado corrige su puntaje de m1 antes de re-cerrar la ronda.
    _puntuar(db, m1.id, jurado.id, 10)
    cerrar_ronda_categoria(categoria.id, *repos)

    persistido = RankingRepository(db).listar(categoria.id)
    assert len(persistido) == 2
    assert [r.muestra_id for r in persistido] == [m1.id, m2.id]
