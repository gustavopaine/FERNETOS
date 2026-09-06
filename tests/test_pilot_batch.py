"""
Tests para modules/microblending/pilot_batch.py: PilotBatch generaliza su
dependencia del calculador (antes hardcodeaba FernetCalculator) para que
el mismo "pipeline" de iteraciones/ajustes sirva para cualquier producto -
en particular, para trackear variantes experimentales de Americano.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.ensamblaje.calculator import BlendParams, FernetCalculator
from modules.microblending.pilot_batch import PilotBatch


class CalculadoraFalsa:
    """Stub: registra si se llamó y devuelve el blend sin modificar."""

    def __init__(self):
        self.llamada_con = None

    def escalar_blend(self, blend_result, nuevo_volumen_litros):
        self.llamada_con = (blend_result, nuevo_volumen_litros)
        return blend_result


@pytest.fixture
def blend_fernet():
    calc = FernetCalculator()
    params = BlendParams(volumen_objetivo_litros=10.0, abv_objetivo=40.0)
    return calc.calcular_blend_completo(params, {}, {})


def test_pilot_batch_usa_fernet_calculator_por_defecto(blend_fernet):
    """No pasar calculator no debe romper el comportamiento existente."""
    piloto = PilotBatch(nombre="Test", blend_base=blend_fernet, tinturas_data={})
    assert isinstance(piloto.calculator, FernetCalculator)
    assert len(piloto.iteraciones) == 1


def test_pilot_batch_acepta_calculator_inyectado(blend_fernet):
    calculadora_falsa = CalculadoraFalsa()

    piloto = PilotBatch(
        nombre="Test",
        blend_base=blend_fernet,
        tinturas_data={},
        calculator=calculadora_falsa,
    )

    assert piloto.calculator is calculadora_falsa
    assert calculadora_falsa.llamada_con is not None
    assert calculadora_falsa.llamada_con[0] is blend_fernet


def test_pilot_batch_aplicar_ajuste_no_depende_del_calculator(blend_fernet):
    """aplicar_ajuste solo manipula el dict de tinturas, sea cual sea el
    calculador - confirma que el pipeline es genérico más allá del punto
    de inyección."""
    piloto = PilotBatch(
        nombre="Test",
        blend_base=blend_fernet,
        tinturas_data={},
        calculator=CalculadoraFalsa(),
    )

    nuevo_blend = piloto.aplicar_ajuste("T-001", 0.3, razon="prueba")

    assert nuevo_blend.composicion.tinturas["T-001"] == 0.3
    assert len(piloto.iteraciones) == 2
