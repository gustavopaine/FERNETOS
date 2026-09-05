"""Tests para utils/validators.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.tinturas.models import ComposicionBotanica, ParametrosExtraccion
from utils.validators import validar_composicion_botanica, validar_parametros_extraccion


def test_composicion_valida_no_lanza():
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=55, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=45, parte_utilizada="raiz"),
    ]
    validar_composicion_botanica(composicion)


def test_composicion_vacia_no_lanza():
    """Antes de completar el paso 2 del wizard, o al rehidratar desde la BD."""
    validar_composicion_botanica([])


def test_composicion_con_tolerancia_de_redondeo_no_lanza():
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=33.34, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=33.33, parte_utilizada="raiz"),
        ComposicionBotanica(especie="quina", porcentaje=33.33, parte_utilizada="corteza"),
    ]
    validar_composicion_botanica(composicion)


def test_composicion_que_no_suma_100_lanza():
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=55, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=30, parte_utilizada="raiz"),
    ]
    with pytest.raises(ValueError):
        validar_composicion_botanica(composicion)


def test_composicion_con_porcentaje_negativo_lanza():
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=110, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=-10, parte_utilizada="raiz"),
    ]
    with pytest.raises(ValueError):
        validar_composicion_botanica(composicion)


def test_parametros_validos_no_lanza():
    validar_parametros_extraccion(
        ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=18)
    )


@pytest.mark.parametrize("abv", [0, -5, 101])
def test_parametros_con_abv_fuera_de_rango_lanza(abv):
    with pytest.raises(ValueError):
        validar_parametros_extraccion(
            ParametrosExtraccion(abv_objetivo=abv, tiempo_estimado_dias=18)
        )


@pytest.mark.parametrize("tiempo", [0, -1])
def test_parametros_con_tiempo_no_positivo_lanza(tiempo):
    with pytest.raises(ValueError):
        validar_parametros_extraccion(
            ParametrosExtraccion(abv_objetivo=70.0, tiempo_estimado_dias=tiempo)
        )
