"""Tests para utils/validators.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.tintura_models import (
    CompatibilidadFamilia,
    ComposicionBotanica,
    GrupoFuncional,
    ParametrosExtraccion,
    Producto,
)
from core.validators import (
    validar_composicion_botanica,
    validar_familia_receta,
    validar_familias_compatibles,
    validar_grupo_funcional_para_producto,
    validar_parametros_extraccion,
)


def test_composicion_valida_no_lanza():
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=55, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=45, parte_utilizada="raiz"),
    ]
    validar_composicion_botanica(composicion)


def test_composicion_vacia_no_lanza():
    """Antes de completar el paso 2 del wizard, o al rehidratar desde la BD."""
    validar_composicion_botanica([])


@pytest.mark.parametrize("total", [99.6, 100.4])
def test_composicion_dentro_de_tolerancia_no_lanza(total):
    """total dista de 100 en 0.4, dentro de PORCENTAJE_TOLERANCIA (0.5)."""
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=total - 50, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=50, parte_utilizada="raiz"),
    ]
    validar_composicion_botanica(composicion)


@pytest.mark.parametrize("total", [99.4, 100.6])
def test_composicion_fuera_de_tolerancia_lanza(total):
    """total dista de 100 en 0.6, fuera de PORCENTAJE_TOLERANCIA (0.5)."""
    composicion = [
        ComposicionBotanica(especie="genciana", porcentaje=total - 50, parte_utilizada="raiz"),
        ComposicionBotanica(especie="ruibarbo", porcentaje=50, parte_utilizada="raiz"),
    ]
    with pytest.raises(ValueError):
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


def test_grupo_none_no_lanza():
    validar_grupo_funcional_para_producto(Producto.FERNET, None)


def test_grupo_fernet_para_producto_fernet_no_lanza():
    validar_grupo_funcional_para_producto(
        Producto.FERNET, GrupoFuncional.AMARGOS_ESTRUCTURALES
    )


def test_grupo_gancia_para_producto_gancia_no_lanza():
    validar_grupo_funcional_para_producto(Producto.GANCIA, GrupoFuncional.QUINADOS)


def test_experimental_valido_para_ambos_productos():
    validar_grupo_funcional_para_producto(Producto.FERNET, GrupoFuncional.EXPERIMENTAL)
    validar_grupo_funcional_para_producto(Producto.GANCIA, GrupoFuncional.EXPERIMENTAL)


def test_grupo_gancia_para_producto_fernet_lanza():
    with pytest.raises(ValueError):
        validar_grupo_funcional_para_producto(Producto.FERNET, GrupoFuncional.QUINADOS)


def test_grupo_fernet_para_producto_gancia_lanza():
    with pytest.raises(ValueError):
        validar_grupo_funcional_para_producto(
            Producto.GANCIA, GrupoFuncional.AMARGOS_ESTRUCTURALES
        )


def test_familias_compatibles_vacia_no_lanza():
    validar_familias_compatibles([])


def test_familias_compatibles_validas_no_lanza():
    validar_familias_compatibles(
        [
            CompatibilidadFamilia(familia="fernet", dosis_min_ml_l=1.0, dosis_max_ml_l=5.0),
            CompatibilidadFamilia(familia="campari", dosis_min_ml_l=2.0, dosis_max_ml_l=8.0),
        ]
    )


def test_familia_compatible_desconocida_lanza():
    with pytest.raises(ValueError):
        validar_familias_compatibles([CompatibilidadFamilia(familia="vermut")])


def test_familia_compatible_duplicada_lanza():
    with pytest.raises(ValueError):
        validar_familias_compatibles(
            [
                CompatibilidadFamilia(familia="campari"),
                CompatibilidadFamilia(familia="campari"),
            ]
        )


@pytest.mark.parametrize("dosis_min, dosis_max", [(-1.0, 5.0), (1.0, -5.0)])
def test_familia_compatible_dosis_negativa_lanza(dosis_min, dosis_max):
    with pytest.raises(ValueError):
        validar_familias_compatibles(
            [
                CompatibilidadFamilia(
                    familia="fernet", dosis_min_ml_l=dosis_min, dosis_max_ml_l=dosis_max
                )
            ]
        )


def test_familia_compatible_rango_dosis_invertido_lanza():
    with pytest.raises(ValueError):
        validar_familias_compatibles(
            [
                CompatibilidadFamilia(
                    familia="fernet", dosis_min_ml_l=20.0, dosis_max_ml_l=2.0
                )
            ]
        )


def test_familia_receta_valida_no_lanza():
    validar_familia_receta("americano")


def test_familia_receta_desconocida_lanza():
    with pytest.raises(ValueError):
        validar_familia_receta("vermut")
