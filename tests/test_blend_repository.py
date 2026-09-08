"""
Tests de integracion para BlendRepository (persistencia real de
blends calculados - roadmap Fase 4, reemplaza el placeholder de
"Historial de Blends" descubierto en Fase 3 (3/N)). TDD: escritos
antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from core.blend_models import BlendGuardado
from core.blend_repository import BlendRepository


@pytest.fixture
def repo(tmp_path):
    db = DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )
    return BlendRepository(db)


def _blend_fernet(**overrides):
    defaults = dict(
        familia="fernet",
        nombre="Fernet Competencia v1",
        datos={
            "abv_calculado": 40.09,
            "composicion": {"tinturas": [{"nombre": "Ajenjo", "ml": 30.0}]},
        },
    )
    defaults.update(overrides)
    return BlendGuardado(**defaults)


def test_guardar_y_recuperar_por_id(repo):
    blend = _blend_fernet()

    repo.guardar(blend)
    recuperado = repo.get_by_id(blend.id)

    assert recuperado is not None
    assert recuperado.familia == "fernet"
    assert recuperado.nombre == "Fernet Competencia v1"
    assert recuperado.datos["abv_calculado"] == pytest.approx(40.09)


def test_get_by_id_inexistente_es_none(repo):
    assert repo.get_by_id("BG-NOEXISTE") is None


def test_nombre_es_opcional(repo):
    blend = _blend_fernet(nombre=None)

    repo.guardar(blend)
    recuperado = repo.get_by_id(blend.id)

    assert recuperado.nombre is None


def test_listar_filtra_por_familia(repo):
    fernet = _blend_fernet()
    gancia = _blend_fernet(familia="gancia", nombre="Gancia v1")
    repo.guardar(fernet)
    repo.guardar(gancia)

    assert [b.id for b in repo.listar(familia="fernet")] == [fernet.id]
    assert [b.id for b in repo.listar(familia="gancia")] == [gancia.id]


def test_listar_sin_familia_devuelve_todos(repo):
    fernet = _blend_fernet()
    gancia = _blend_fernet(familia="gancia")
    repo.guardar(fernet)
    repo.guardar(gancia)

    assert {b.id for b in repo.listar()} == {fernet.id, gancia.id}


def test_listar_ordena_del_mas_reciente_al_mas_antiguo(repo):
    import time

    primero = _blend_fernet(nombre="Primero")
    repo.guardar(primero)
    time.sleep(0.01)
    segundo = _blend_fernet(nombre="Segundo")
    repo.guardar(segundo)

    resultado = repo.listar(familia="fernet")

    assert [b.id for b in resultado] == [segundo.id, primero.id]


def test_eliminar(repo):
    blend = _blend_fernet()
    repo.guardar(blend)

    eliminado = repo.eliminar(blend.id)

    assert eliminado is True
    assert repo.get_by_id(blend.id) is None


def test_eliminar_inexistente_devuelve_false(repo):
    assert repo.eliminar("BG-NOEXISTE") is False
