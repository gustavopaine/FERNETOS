"""
Tests de integración para RecetaRepository.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from core.receta_models import EstadoReceta, IngredienteReceta, Receta
from core.receta_repository import RecetaRepository


@pytest.fixture
def repo(tmp_path):
    db = DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )
    return RecetaRepository(db)


def _receta_fernet():
    return Receta(
        familia="fernet",
        nombre="Fernet Competencia v1",
        estado=EstadoReceta.TESTING,
        ingredientes=[
            IngredienteReceta(tintura_id="T-AMARGOS", porcentaje=40.0),
            IngredienteReceta(tintura_id="T-CITRICOS", porcentaje=15.0),
            IngredienteReceta(tintura_id="T-ESPECIAS", ml=50.0),
        ],
        abv_objetivo=40.0,
        tiempo_maceracion_dias=90,
        perfil_sensorial_objetivo={"amargor": 8.0, "dulzor": 3.0},
        notas_batch="Batch de referencia",
    )


def test_guardar_y_recuperar_receta(repo):
    receta = _receta_fernet()

    repo.guardar(receta)
    recuperada = repo.get_by_id(receta.id)

    assert recuperada is not None
    assert recuperada.familia == "fernet"
    assert recuperada.nombre == "Fernet Competencia v1"
    assert recuperada.estado == EstadoReceta.TESTING
    assert recuperada.abv_objetivo == 40.0
    assert recuperada.tiempo_maceracion_dias == 90
    assert recuperada.perfil_sensorial_objetivo == {"amargor": 8.0, "dulzor": 3.0}
    assert recuperada.notas_batch == "Batch de referencia"

    assert len(recuperada.ingredientes) == 3
    por_tintura = {i.tintura_id: i for i in recuperada.ingredientes}
    assert por_tintura["T-AMARGOS"].porcentaje == 40.0
    assert por_tintura["T-ESPECIAS"].ml == 50.0


def test_listar_filtra_por_familia(repo):
    fernet = _receta_fernet()
    campari = Receta(familia="campari", nombre="Campari Casero v1")

    repo.guardar(fernet)
    repo.guardar(campari)

    solo_fernet = repo.listar(familia="fernet")
    assert [r.id for r in solo_fernet] == [fernet.id]

    solo_campari = repo.listar(familia="campari")
    assert [r.id for r in solo_campari] == [campari.id]


def test_listar_filtra_por_estado(repo):
    borrador = Receta(familia="americano", nombre="Americano Borrador")
    testing = _receta_fernet()

    repo.guardar(borrador)
    repo.guardar(testing)

    solo_testing = repo.listar(estado="testing")
    assert [r.id for r in solo_testing] == [testing.id]


def test_eliminar_receta(repo):
    receta = _receta_fernet()
    repo.guardar(receta)

    assert repo.eliminar(receta.id) is True
    assert repo.get_by_id(receta.id) is None


def test_receta_con_familia_invalida_lanza():
    with pytest.raises(ValueError):
        Receta(familia="invalida", nombre="Algo raro")
