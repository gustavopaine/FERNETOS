"""
Tests para modules/ensamblaje/calculator_campari.py: receta real de
Campari casero (batch de referencia 1.5L), cuarto producto del sistema
(Fernet, Gancia, Americano, Campari). Sin capa de variantes - solo la
receta base con cantidades exactas, a diferencia de Americano.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.ensamblaje.calculator_campari import (
    CampariCalculator,
    ComposicionCampari,
)
from modules.tinturas.models import ComposicionBotanica, ControlCalidad


def _ingrediente(especie, gramos, parte="raiz"):
    # porcentaje no aplica acá (la receta se define en gramos absolutos,
    # no en % de materia seca) - se deja en 0, ComposicionBotanica no lo
    # exige distinto de cero.
    return ComposicionBotanica(especie=especie, porcentaje=gramos, parte_utilizada=parte)


def _composicion_base():
    return ComposicionCampari(
        alcohol_ml=1000.0,
        alcohol_abv=40.0,
        agua_ml=500.0,
        azucar_g=225.0,
        ingredientes_maceracion=[
            _ingrediente("ajenjo", 10, "hoja"),
            _ingrediente("quina", 5, "corteza"),
            _ingrediente("genciana", 5, "raiz"),
            _ingrediente("angelica", 5, "raiz"),
            _ingrediente("ruibarbo", 2, "raiz"),
            _ingrediente("chips_de_roble", 5, "madera"),
            ComposicionBotanica(especie="naranja", porcentaje=1, parte_utilizada="cascara"),
            ComposicionBotanica(especie="pomelo", porcentaje=1, parte_utilizada="cascara"),
            ComposicionBotanica(especie="limon", porcentaje=1, parte_utilizada="cascara"),
        ],
        ingredientes_incorporacion_tardia=[
            _ingrediente("hibiscus", 10, "flor"),
        ],
    )


# --- ABV: 1000ml de vodka/alcohol de cereal a 40° diluido a 1500ml final ---


def test_calcular_abv_1000ml_40_grados_en_1500ml_final():
    composicion = _composicion_base()
    abv = CampariCalculator.calcular_abv(composicion)
    # 1000ml * 40% / 1500ml final = 26.666...%
    assert abv == pytest.approx(26.7, abs=0.05)


def test_calcular_abv_no_depende_de_azucar_ni_botanicos():
    """El azúcar y los botánicos no aportan alcohol - cambiarlos no debe
    mover el ABV calculado."""
    composicion = _composicion_base()
    composicion.azucar_g = 999.0
    composicion.ingredientes_maceracion = []
    abv = CampariCalculator.calcular_abv(composicion)
    assert abv == pytest.approx(26.7, abs=0.05)


# --- Azúcar: 225g/1.5L debe ser consistente con el ratio de 150g/L ---


def test_azucar_efectiva_150_gpl_consistente_con_la_fuente():
    gpl = CampariCalculator.calcular_azucar_efectiva_gpl(
        azucar_g=225.0, volumen_final_ml=1500.0
    )
    assert gpl == pytest.approx(150.0)


# --- Densidad: dato de control de calidad medido, no calculado ---


def test_densidad_objetivo_se_registra_tal_cual_sin_recalcular():
    """1060 es un valor de densímetro (gravedad específica x1000) que el
    usuario ingresa después de medir - no se deriva de la receta."""
    composicion = _composicion_base()
    resultado = CampariCalculator.calcular_blend(
        composicion, control_calidad=ControlCalidad(densidad=1060)
    )
    assert resultado.control_calidad.densidad == 1060
    # Cambiar cualquier cantidad de la receta no debe alterar la densidad
    # ingresada - es un dato medido, no derivado.
    composicion.azucar_g = 500.0
    resultado2 = CampariCalculator.calcular_blend(
        composicion, control_calidad=ControlCalidad(densidad=1060)
    )
    assert resultado2.control_calidad.densidad == 1060


def test_calcular_blend_sin_control_calidad_es_none():
    composicion = _composicion_base()
    resultado = CampariCalculator.calcular_blend(composicion)
    assert resultado.control_calidad is None


def test_calcular_blend_arma_resultado_completo():
    composicion = _composicion_base()
    resultado = CampariCalculator.calcular_blend(composicion)

    assert resultado.abv_calculado == pytest.approx(26.7, abs=0.05)
    assert resultado.azucar_efectiva_gpl == pytest.approx(150.0)
    assert resultado.composicion is composicion
