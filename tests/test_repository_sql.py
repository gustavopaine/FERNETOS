"""
Tests de integración para TinturaSQLRepository: el repositorio real que usa
app.py en producción (a diferencia del legacy repository.py, ya retirado).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager
from modules.tinturas.models import (
    ComposicionBotanica,
    EstadoTintura,
    GrupoFuncional,
    ParametrosExtraccion,
    RegistroExtraccion,
    Tintura,
)
from modules.tinturas.repository_sql import TinturaSQLRepository


@pytest.fixture
def repo(tmp_path):
    db = DatabaseManager(
        db_path=str(tmp_path / "test.db"),
        schema_path=str(tmp_path / "schema" / "schema.sql"),
    )
    return TinturaSQLRepository(db)


def _tintura_amargos():
    return Tintura(
        nombre="Amargos Estructurales Premium",
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
        composicion=[
            ComposicionBotanica(especie="genciana", porcentaje=55, parte_utilizada="raiz"),
            ComposicionBotanica(especie="ruibarbo", porcentaje=35, parte_utilizada="raiz"),
            ComposicionBotanica(especie="quina", porcentaje=10, parte_utilizada="corteza"),
        ],
        peso_total_materia_seca_g=500,
        volumen_alcohol_ml=2500,
        parametros=ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=18),
    )


def test_guardar_y_recuperar_tintura_completa(repo):
    tintura = _tintura_amargos()

    repo.guardar(tintura)
    recuperada = repo.get_by_id(tintura.id)

    assert recuperada is not None
    assert recuperada.nombre == "Amargos Estructurales Premium"
    assert recuperada.grupo_funcional == GrupoFuncional.AMARGOS_ESTRUCTURALES
    assert recuperada.parametros.abv_objetivo == 70.0
    assert len(recuperada.composicion) == 3
    assert {c.especie for c in recuperada.composicion} == {
        "genciana",
        "ruibarbo",
        "quina",
    }


def test_guardar_registros_de_curva_y_recuperarlos(repo):
    tintura = _tintura_amargos()
    tintura.agregar_registro_extraccion(
        RegistroExtraccion(
            dia=1,
            fecha=tintura.fecha_inicio,
            intensidad_estimada=20,
            notas_sensoriales="Aroma leve a raíz",
            compuestos_detectados=["glucosidos"],
        )
    )
    repo.guardar(tintura)

    recuperada = repo.get_by_id(tintura.id)

    assert len(recuperada.registros_extraccion) == 1
    assert recuperada.registros_extraccion[0].dia == 1
    assert recuperada.registros_extraccion[0].compuestos_detectados == ["glucosidos"]


def test_listar_filtra_por_estado_y_grupo(repo):
    t1 = _tintura_amargos()
    t2 = _tintura_amargos()
    t2.nombre = "Aromática Alta Premium"
    t2.grupo_funcional = GrupoFuncional.AROMATICA_ALTA
    t2.estado = EstadoTintura.LISTA
    repo.guardar(t1)
    repo.guardar(t2)

    solo_amargos = repo.listar(grupo=GrupoFuncional.AMARGOS_ESTRUCTURALES.value)
    solo_listas = repo.listar(estado=EstadoTintura.LISTA.value)

    assert [t.id for t in solo_amargos] == [t1.id]
    assert [t.id for t in solo_listas] == [t2.id]


def test_eliminar_borra_tintura_y_no_deja_huerfanos(repo):
    tintura = _tintura_amargos()
    tintura.agregar_registro_extraccion(
        RegistroExtraccion(
            dia=1,
            fecha=tintura.fecha_inicio,
            intensidad_estimada=20,
            notas_sensoriales="",
            compuestos_detectados=["glucosidos"],
        )
    )
    repo.guardar(tintura)

    assert repo.eliminar(tintura.id) is True

    assert repo.get_by_id(tintura.id) is None
    assert repo.db.ejecutar(
        "SELECT * FROM composicion_botanica WHERE tintura_id = ?", (tintura.id,)
    ) == []
    assert repo.db.ejecutar(
        "SELECT * FROM parametros_extraccion WHERE tintura_id = ?", (tintura.id,)
    ) == []
    assert repo.db.ejecutar(
        "SELECT * FROM registros_curva WHERE tintura_id = ?", (tintura.id,)
    ) == []
