"""Tests de integración: validación conectada a Tintura.__post_init__."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.tinturas.models import (
    ComposicionBotanica,
    ParametrosExtraccion,
    Tintura,
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
