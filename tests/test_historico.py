"""
Tests para evaluation/historico.py: trazabilidad de una receta o un
productor a traves de ediciones/eventos (roadmap, seccion 5.5, tercer
item de "Salidas del modulo"). TDD: escritos antes que la
implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from evaluation.models import Categoria, Evento, Muestra, Ranking, SubModalidad
from evaluation.repository import (
    CategoriaRepository,
    EventoRepository,
    MuestraRepository,
    RankingRepository,
)
from evaluation.historico import historico_productor, historico_receta


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )


def _repos(db):
    return MuestraRepository(db), CategoriaRepository(db), EventoRepository(db), RankingRepository(db)


def _crear_evento(db, nombre, fecha, edicion_numero=1) -> Evento:
    evento = Evento(nombre=nombre, fecha=fecha, sede="Club X", edicion_numero=edicion_numero)
    EventoRepository(db).guardar(evento)
    return evento


def _crear_categoria(db, evento_id, familia="fernet") -> Categoria:
    categoria = Categoria(evento_id=evento_id, familia=familia, submodalidad=SubModalidad.PURO)
    CategoriaRepository(db).guardar(categoria)
    return categoria


def _crear_muestra(db, categoria_id, **kwargs) -> Muestra:
    muestra = Muestra(categoria_id=categoria_id, **kwargs)
    MuestraRepository(db).guardar(muestra)
    return muestra


def test_historico_receta_sin_apariciones_devuelve_vacio(db):
    resultado = historico_receta("R-INEXISTENTE", *_repos(db))
    assert resultado == []


def test_historico_receta_valor_none_lanza():
    with pytest.raises(ValueError):
        historico_receta(None, None, None, None, None)


def test_historico_receta_una_aparicion_sin_ronda_cerrada(db):
    evento = _crear_evento(db, "Torneo 2026", "2026-11-15")
    categoria = _crear_categoria(db, evento.id)
    muestra = _crear_muestra(db, categoria.id, receta_id_interna="R-1")

    resultado = historico_receta("R-1", *_repos(db))

    assert len(resultado) == 1
    aparicion = resultado[0]
    assert aparicion.evento_nombre == "Torneo 2026"
    assert aparicion.categoria_familia == "fernet"
    assert aparicion.codigo_ciego == muestra.codigo_ciego
    assert aparicion.posicion is None
    assert aparicion.puntaje_final is None


def test_historico_receta_incluye_ranking_si_la_ronda_fue_cerrada(db):
    evento = _crear_evento(db, "Torneo 2026", "2026-11-15")
    categoria = _crear_categoria(db, evento.id)
    muestra = _crear_muestra(db, categoria.id, receta_id_interna="R-1")
    RankingRepository(db).guardar(
        Ranking(categoria_id=categoria.id, muestra_id=muestra.id, puntaje_final=8.5, posicion=1)
    )

    resultado = historico_receta("R-1", *_repos(db))

    assert resultado[0].posicion == 1
    assert resultado[0].puntaje_final == pytest.approx(8.5)


def test_historico_receta_ordena_cronologicamente_por_fecha_de_evento(db):
    evento_2027 = _crear_evento(db, "Torneo 2027", "2027-05-01")
    evento_2026 = _crear_evento(db, "Torneo 2026", "2026-11-15")
    cat_2027 = _crear_categoria(db, evento_2027.id)
    cat_2026 = _crear_categoria(db, evento_2026.id)
    _crear_muestra(db, cat_2027.id, receta_id_interna="R-1")
    _crear_muestra(db, cat_2026.id, receta_id_interna="R-1")

    resultado = historico_receta("R-1", *_repos(db))

    assert [a.evento_nombre for a in resultado] == ["Torneo 2026", "Torneo 2027"]


def test_historico_receta_ignora_muestras_de_otras_recetas(db):
    evento = _crear_evento(db, "Torneo 2026", "2026-11-15")
    categoria = _crear_categoria(db, evento.id)
    _crear_muestra(db, categoria.id, receta_id_interna="R-1")
    _crear_muestra(db, categoria.id, receta_id_interna="R-OTRA")

    resultado = historico_receta("R-1", *_repos(db))

    assert len(resultado) == 1


def test_historico_productor_sin_apariciones_devuelve_vacio(db):
    assert historico_productor("P-INEXISTENTE", *_repos(db)) == []


def test_historico_productor_valor_none_lanza():
    with pytest.raises(ValueError):
        historico_productor(None, None, None, None, None)


def test_historico_productor_encuentra_sus_apariciones(db):
    evento = _crear_evento(db, "Torneo 2026", "2026-11-15")
    categoria = _crear_categoria(db, evento.id)
    muestra = _crear_muestra(db, categoria.id, productor_id="P-1")

    resultado = historico_productor("P-1", *_repos(db))

    assert len(resultado) == 1
    assert resultado[0].muestra_id == muestra.id
