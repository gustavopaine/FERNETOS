"""
Tests para RecipeEngineFactory.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.recipe_engine_factory import RecipeEngineFactory
from families.fernet.calculator import FernetCalculator
from families.gancia.gancia_calculator import GanciaCalculator
from families.gancia.americano_calculator import AmericanoCalculator
from families.campari.campari_calculator import CampariCalculator


def test_create_fernet():
    assert isinstance(RecipeEngineFactory.create("fernet"), FernetCalculator)


def test_create_americano_default_es_infusion_directa():
    assert isinstance(RecipeEngineFactory.create("americano"), AmericanoCalculator)


def test_create_americano_metodo_vinica():
    assert isinstance(
        RecipeEngineFactory.create("americano", metodo="vinica"), GanciaCalculator
    )


def test_create_campari():
    assert isinstance(RecipeEngineFactory.create("campari"), CampariCalculator)


def test_create_familia_desconocida_lanza():
    with pytest.raises(ValueError):
        RecipeEngineFactory.create("inexistente")
