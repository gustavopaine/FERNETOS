"""
Tests para modules/ensamblaje/calculator_americano.py: receta base de
Americano (ex-Gancia casero, infusión directa) + capa de variantes
experimentales para probar contra el Gancia comercial y otras marcas.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.ensamblaje.calculator_americano import (
    INGREDIENTES_CORE,
    INGREDIENTES_CORE_SECUNDARIOS,
    INGREDIENTES_OPCIONALES,
    AmericanoCalculator,
    ComposicionAmericano,
    VarianteExperimental,
)
from modules.tinturas.models import ComposicionBotanica


def _ingrediente(especie, parte="cascara"):
    return ComposicionBotanica(especie=especie, porcentaje=0, parte_utilizada=parte)


def _composicion_base(ingredientes_variante=None):
    return ComposicionAmericano(
        alcohol_ml=500.0,
        alcohol_abv=96.0,
        agua_ml=3000.0,
        azucar_g=900.0,
        ingredientes_base=[
            _ingrediente("genciana", "raiz"),
            _ingrediente("melisa", "hoja"),
            _ingrediente("canela"),
            _ingrediente("anis_estrellado"),
            _ingrediente("angelica", "raiz"),
            _ingrediente("enebro"),
            _ingrediente("pomelo"),
            _ingrediente("limon"),
            _ingrediente("naranja"),
        ],
        ingredientes_variante=ingredientes_variante or [],
    )


# --- ABV: infusión directa (alcohol + agua, sin base vínica) ---
# 500ml de alcohol 96° + botánicos (no aportan alcohol) + agua (3-5L) +
# azúcar. El ABV sale solo de diluir el alcohol en el agua total.


def test_calcular_abv_500ml_alcohol_96_en_3l_agua():
    composicion = _composicion_base()
    composicion.agua_ml = 3000.0
    abv = AmericanoCalculator.calcular_abv(composicion)
    assert abv == pytest.approx(13.7, abs=0.05)


def test_calcular_abv_500ml_alcohol_96_en_5l_agua():
    composicion = _composicion_base()
    composicion.agua_ml = 5000.0
    abv = AmericanoCalculator.calcular_abv(composicion)
    assert abv == pytest.approx(8.7, abs=0.05)


def test_calcular_abv_sin_agua_es_el_grado_del_alcohol():
    composicion = _composicion_base()
    composicion.agua_ml = 0.0
    abv = AmericanoCalculator.calcular_abv(composicion)
    assert abv == pytest.approx(96.0)


# --- Banco de botánicos ---


def test_banco_de_botanicos_no_se_superpone():
    """genciana/melisa son intocables; un ingrediente no puede estar en
    dos categorías a la vez (evita que alguien lo mueva por error)."""
    assert set(INGREDIENTES_CORE) & set(INGREDIENTES_CORE_SECUNDARIOS) == set()
    assert set(INGREDIENTES_CORE) & set(INGREDIENTES_OPCIONALES) == set()
    assert set(INGREDIENTES_CORE_SECUNDARIOS) & set(INGREDIENTES_OPCIONALES) == set()


def test_banco_de_botanicos_contiene_los_ingredientes_reales():
    assert {"genciana", "melisa"} <= set(INGREDIENTES_CORE)
    assert {"canela", "anis_estrellado", "angelica", "enebro", "pomelo", "limon", "naranja"} <= set(
        INGREDIENTES_CORE_SECUNDARIOS
    )
    assert {"clavo_de_olor", "galanga", "paico", "romero"} <= set(INGREDIENTES_OPCIONALES)


# --- VarianteExperimental: batch tracking + protección del core ---


def test_variante_experimental_base_no_lanza():
    variante = VarianteExperimental(
        batch_id="AMERICANO_BASE_v1",
        composicion=_composicion_base(),
    )
    assert variante.batch_id == "AMERICANO_BASE_v1"


def test_variante_experimental_con_opcional_no_lanza():
    variante = VarianteExperimental(
        batch_id="AMERICANO_CLAVO_v1",
        composicion=_composicion_base([_ingrediente("clavo_de_olor")]),
    )
    assert len(variante.composicion.ingredientes_variante) == 1


def test_variante_experimental_con_ingrediente_core_en_variante_lanza():
    """El core (genciana/melisa) no se toca - ni siquiera vía variante."""
    with pytest.raises(ValueError):
        VarianteExperimental(
            batch_id="AMERICANO_ROTO_v1",
            composicion=_composicion_base([_ingrediente("genciana", "raiz")]),
        )


def test_variante_experimental_con_ingrediente_core_secundario_en_variante_lanza():
    """Los core-secundarios se cambian editando ingredientes_base (una
    receta distinta), no vía ingredientes_variante."""
    with pytest.raises(ValueError):
        VarianteExperimental(
            batch_id="AMERICANO_ROTO_v2",
            composicion=_composicion_base([_ingrediente("canela")]),
        )


def test_variante_experimental_con_ingrediente_desconocido_lanza():
    with pytest.raises(ValueError):
        VarianteExperimental(
            batch_id="AMERICANO_ROTO_v3",
            composicion=_composicion_base([_ingrediente("jengibre")]),
        )


def test_variante_experimental_referencia_comercial_es_opcional():
    variante = VarianteExperimental(
        batch_id="AMERICANO_ROMERO_v1",
        composicion=_composicion_base([_ingrediente("romero")]),
        referencia_comercial="Más herbal que Gancia comercial, menos dulce",
    )
    assert "Gancia" in variante.referencia_comercial


def test_variante_experimental_sin_referencia_comercial_es_none():
    variante = VarianteExperimental(
        batch_id="AMERICANO_BASE_v1",
        composicion=_composicion_base(),
    )
    assert variante.referencia_comercial is None
