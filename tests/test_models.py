"""Tests de integración: validación conectada a Tintura.__post_init__."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.tinturas.models import (
    ComposicionBotanica,
    GrupoFuncional,
    ParametrosExtraccion,
    Producto,
    Tintura,
    grupos_disponibles_para,
)


def test_tintura_con_composicion_valida_no_lanza():
    Tintura(
        nombre="Amargos",
        composicion=[
            ComposicionBotanica(especie="genciana", porcentaje=100, parte_utilizada="raiz")
        ],
        parametros=ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=18),
    )


def test_tintura_sin_composicion_no_lanza():
    """El estado que usa repository_sql.get_by_id antes de anexar filas."""
    Tintura(nombre="Placeholder")


def test_tintura_con_composicion_invalida_lanza():
    with pytest.raises(ValueError):
        Tintura(
            nombre="Amargos",
            composicion=[
                ComposicionBotanica(especie="genciana", porcentaje=55, parte_utilizada="raiz")
            ],
        )


def test_tintura_con_abv_invalido_lanza():
    with pytest.raises(ValueError):
        Tintura(
            nombre="Amargos",
            parametros=ParametrosExtraccion(abv_objetivo=150.0, tiempo_estimado_dias=18),
        )


def test_tintura_default_producto_es_fernet():
    t = Tintura(nombre="Amargos")
    assert t.producto == Producto.FERNET


def test_tintura_gancia_con_grupo_gancia_no_lanza():
    Tintura(
        nombre="Quinado Base",
        producto=Producto.GANCIA,
        grupo_funcional=GrupoFuncional.QUINADOS,
    )


def test_tintura_gancia_con_grupo_fernet_lanza():
    with pytest.raises(ValueError):
        Tintura(
            nombre="Quinado Base",
            producto=Producto.GANCIA,
            grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
        )


def test_tintura_fernet_con_grupo_gancia_lanza():
    with pytest.raises(ValueError):
        Tintura(
            nombre="Amargos",
            producto=Producto.FERNET,
            grupo_funcional=GrupoFuncional.QUINADOS,
        )


def test_tintura_to_dict_incluye_producto():
    t = Tintura(nombre="Quinado Base", producto=Producto.GANCIA)
    assert t.to_dict()["producto"] == "gancia"


def test_grupos_disponibles_para_fernet():
    grupos = grupos_disponibles_para("fernet")
    assert "amargos_estructurales" in grupos
    assert "quinados" not in grupos


def test_grupos_disponibles_para_gancia():
    grupos = grupos_disponibles_para("gancia")
    assert "quinados" in grupos
    assert "amargos_estructurales" not in grupos


@pytest.mark.parametrize("valor", ["Todos", None])
def test_grupos_disponibles_para_todos_o_none_incluye_ambos_sin_duplicar_experimental(valor):
    grupos = grupos_disponibles_para(valor)
    assert "amargos_estructurales" in grupos
    assert "quinados" in grupos
    assert grupos.count("experimental") == 1
