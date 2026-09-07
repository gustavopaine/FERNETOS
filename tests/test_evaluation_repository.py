"""
Tests de integracion para evaluation/repository.py (persistencia SQL de
las entidades de evaluacion/torneo). TDD: escritos antes que la
implementacion, por decision explicita del usuario para este modulo.

Las tablas tienen FOREIGN KEY reales (mismo patron que el resto del
esquema, con PRAGMA foreign_keys=ON) asi que los tests crean la cadena
evento -> categoria -> muestra / jurado antes de ejercitar cada
repositorio hijo.
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from evaluation.models import (
    Categoria,
    Evento,
    Jurado,
    Muestra,
    Puntaje,
    Ranking,
    RolJurado,
    SubModalidad,
)
from evaluation.repository import (
    CategoriaRepository,
    EventoRepository,
    JuradoRepository,
    MuestraRepository,
    PuntajeRepository,
    RankingRepository,
)


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )


def _crear_categoria(db, familia="fernet", submodalidad=SubModalidad.PURO) -> Categoria:
    evento = Evento(nombre="E1", fecha="2026-11-15", sede="X", edicion_numero=1)
    EventoRepository(db).guardar(evento)
    categoria = Categoria(evento_id=evento.id, familia=familia, submodalidad=submodalidad)
    CategoriaRepository(db).guardar(categoria)
    return categoria


def _crear_muestra(db, categoria_id=None, **kwargs) -> Muestra:
    if categoria_id is None:
        categoria_id = _crear_categoria(db).id
    muestra = Muestra(categoria_id=categoria_id, **kwargs)
    MuestraRepository(db).guardar(muestra)
    return muestra


def _crear_jurado(db, **kwargs) -> Jurado:
    jurado = Jurado(nombre=kwargs.pop("nombre", "Ana"), rol=kwargs.pop("rol", RolJurado.SOMMELIER), **kwargs)
    JuradoRepository(db).guardar(jurado)
    return jurado


def test_evento_guardar_y_recuperar(db):
    repo = EventoRepository(db)
    evento = Evento(nombre="Torneo Regional", fecha="2026-11-15", sede="Club X", edicion_numero=2)

    repo.guardar(evento)
    recuperado = repo.get_by_id(evento.id)

    assert recuperado is not None
    assert recuperado.nombre == "Torneo Regional"
    assert recuperado.edicion_numero == 2
    assert [e.id for e in repo.listar()] == [evento.id]


def test_categoria_guardar_recuperar_y_listar_por_evento(db):
    repo = CategoriaRepository(db)
    evento = Evento(nombre="E1", fecha="2026-11-15", sede="X", edicion_numero=1)
    EventoRepository(db).guardar(evento)

    cat = Categoria(evento_id=evento.id, familia="campari", submodalidad=SubModalidad.CON_SODA)
    repo.guardar(cat)

    recuperada = repo.get_by_id(cat.id)
    assert recuperada.familia == "campari"
    assert recuperada.submodalidad == SubModalidad.CON_SODA

    assert [c.id for c in repo.listar(evento_id=evento.id)] == [cat.id]
    assert repo.listar(evento_id="EVT-INEXISTENTE") == []


def test_muestra_guardar_y_recuperar_con_campos_ocultos(db):
    categoria = _crear_categoria(db)
    repo = MuestraRepository(db)
    muestra = Muestra(categoria_id=categoria.id, receta_id_interna="R-1", productor_id="P-1")

    repo.guardar(muestra)
    recuperada = repo.get_by_id(muestra.id)

    assert recuperada.codigo_ciego == muestra.codigo_ciego
    assert recuperada.receta_id_interna == "R-1"
    assert recuperada.productor_id == "P-1"
    assert [m.id for m in repo.listar(categoria_id=categoria.id)] == [muestra.id]


def test_muestra_codigo_ciego_duplicado_en_misma_categoria_lanza(db):
    categoria = _crear_categoria(db)
    repo = MuestraRepository(db)
    m1 = Muestra(categoria_id=categoria.id)
    m2 = Muestra(categoria_id=categoria.id, codigo_ciego=m1.codigo_ciego)

    repo.guardar(m1)
    with pytest.raises(sqlite3.IntegrityError):
        repo.guardar(m2)


def test_jurado_guardar_y_recuperar(db):
    repo = JuradoRepository(db)
    jurado = Jurado(nombre="Ana", rol=RolJurado.SOMMELIER, peso_voto=1.5)

    repo.guardar(jurado)
    recuperado = repo.get_by_id(jurado.id)

    assert recuperado.nombre == "Ana"
    assert recuperado.rol == RolJurado.SOMMELIER
    assert recuperado.peso_voto == 1.5
    assert [j.id for j in repo.listar()] == [jurado.id]


def test_puntaje_guardar_y_recuperar(db):
    muestra = _crear_muestra(db)
    jurado = _crear_jurado(db)
    repo = PuntajeRepository(db)
    puntaje = Puntaje(
        muestra_id=muestra.id, jurado_id=jurado.id, visual=8, aroma=7, sabor_boca=9,
        comentario_libre="Buen balance",
    )

    repo.guardar(puntaje)
    recuperado = repo.get_by_id(puntaje.id)

    assert recuperado.visual == 8
    assert recuperado.aroma == 7
    assert recuperado.sabor_boca == 9
    assert recuperado.comentario_libre == "Buen balance"
    assert [p.id for p in repo.listar(muestra_id=muestra.id)] == [puntaje.id]
    assert [p.id for p in repo.listar(jurado_id=jurado.id)] == [puntaje.id]


def test_puntaje_re_guardado_del_mismo_jurado_actualiza_no_duplica(db):
    """Un jurado puede corregir su puntaje antes del cierre de la ronda:
    debe reemplazar el anterior, no duplicarlo (UNIQUE(muestra_id, jurado_id))."""
    muestra = _crear_muestra(db)
    jurado = _crear_jurado(db)
    repo = PuntajeRepository(db)
    primero = Puntaje(muestra_id=muestra.id, jurado_id=jurado.id, visual=5, aroma=5, sabor_boca=5)
    repo.guardar(primero)

    corregido = Puntaje(muestra_id=muestra.id, jurado_id=jurado.id, visual=9, aroma=9, sabor_boca=9)
    repo.guardar(corregido)

    puntajes = repo.listar(muestra_id=muestra.id)
    assert len(puntajes) == 1
    assert puntajes[0].visual == 9


def test_ranking_guardar_listar_y_actualizar(db):
    categoria = _crear_categoria(db)
    m1 = _crear_muestra(db, categoria_id=categoria.id)
    m2 = _crear_muestra(db, categoria_id=categoria.id)
    repo = RankingRepository(db)

    repo.guardar(Ranking(categoria_id=categoria.id, muestra_id=m1.id, puntaje_final=8.5, posicion=1))
    repo.guardar(Ranking(categoria_id=categoria.id, muestra_id=m2.id, puntaje_final=7.0, posicion=2))

    resultado = repo.listar(categoria_id=categoria.id)
    assert [(r.muestra_id, r.posicion) for r in resultado] == [(m1.id, 1), (m2.id, 2)]

    # Recalcular el ranking de una categoria debe actualizar, no duplicar
    repo.guardar(Ranking(categoria_id=categoria.id, muestra_id=m1.id, puntaje_final=9.0, posicion=1))
    resultado = repo.listar(categoria_id=categoria.id)
    assert len(resultado) == 2
    assert resultado[0].puntaje_final == pytest.approx(9.0)
