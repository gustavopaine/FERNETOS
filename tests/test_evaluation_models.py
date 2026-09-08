"""
Tests para evaluation/models.py: entidades del modulo de evaluacion/torneo
(Fase 2 de fernetos-diseño-y-roadmap.md, seccion 5).

TDD: estos tests se escribieron antes de evaluation/models.py, por
decision explicita del usuario para la logica de este modulo (puntaje
ponderado, codificacion ciega, ranking).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from evaluation.models import (
    Categoria,
    Evento,
    Jurado,
    Muestra,
    Puntaje,
    Ranking,
    RolJurado,
    SubModalidad,
)


def test_evento_defaults():
    evento = Evento(nombre="Torneo Regional", fecha="2026-11-15", sede="Club X", edicion_numero=1)
    assert evento.id
    assert evento.nombre == "Torneo Regional"
    assert evento.edicion_numero == 1


def test_categoria_familia_valida_no_lanza():
    Categoria(evento_id="E-1", familia="campari", submodalidad=SubModalidad.PURO)


def test_categoria_familia_invalida_lanza():
    with pytest.raises(ValueError):
        Categoria(evento_id="E-1", familia="vermut", submodalidad=SubModalidad.PURO)


@pytest.mark.parametrize(
    "submodalidad",
    [SubModalidad.PURO, SubModalidad.CON_COLA, SubModalidad.CON_SODA, SubModalidad.CON_TONICA],
)
def test_categoria_submodalidades_validas(submodalidad):
    categoria = Categoria(evento_id="E-1", familia="fernet", submodalidad=submodalidad)
    assert categoria.submodalidad == submodalidad


def test_muestra_codigo_ciego_autogenerado_y_unico():
    m1 = Muestra(categoria_id="C-1")
    m2 = Muestra(categoria_id="C-1")
    assert m1.codigo_ciego
    assert m1.codigo_ciego != m2.codigo_ciego


def test_muestra_receta_y_productor_ocultos_por_defecto():
    """El vinculo receta<->productor no se expone salvo que se setee
    explicitamente (el cierre oficial de la ronda lo revela, no el
    modelo en si - ver seccion 5.3 del roadmap)."""
    muestra = Muestra(categoria_id="C-1")
    assert muestra.receta_id_interna is None
    assert muestra.productor_id is None


def test_jurado_defaults():
    jurado = Jurado(nombre="Ana", rol=RolJurado.SOMMELIER)
    assert jurado.peso_voto == 1.0


def test_jurado_peso_voto_personalizado():
    jurado = Jurado(nombre="Ana", rol=RolJurado.SOMMELIER, peso_voto=1.5)
    assert jurado.peso_voto == 1.5


@pytest.mark.parametrize("peso_voto", [0.0, -1.0])
def test_jurado_peso_voto_no_positivo_lanza(peso_voto):
    with pytest.raises(ValueError):
        Jurado(nombre="Ana", rol=RolJurado.SOMMELIER, peso_voto=peso_voto)


@pytest.mark.parametrize("visual,aroma,sabor_boca", [(1, 1, 1), (10, 10, 10), (5, 7, 8)])
def test_puntaje_subpuntajes_validos_no_lanza(visual, aroma, sabor_boca):
    Puntaje(muestra_id="M-1", jurado_id="J-1", visual=visual, aroma=aroma, sabor_boca=sabor_boca)


@pytest.mark.parametrize("visual,aroma,sabor_boca", [(0, 5, 5), (5, 11, 5), (5, 5, -1)])
def test_puntaje_subpuntaje_fuera_de_rango_lanza(visual, aroma, sabor_boca):
    with pytest.raises(ValueError):
        Puntaje(muestra_id="M-1", jurado_id="J-1", visual=visual, aroma=aroma, sabor_boca=sabor_boca)


def test_puntaje_ponderado_maximo():
    puntaje = Puntaje(muestra_id="M-1", jurado_id="J-1", visual=10, aroma=10, sabor_boca=10)
    assert puntaje.puntaje_ponderado() == pytest.approx(10.0)


def test_puntaje_ponderado_usa_pesos_de_la_rubrica():
    """Rubrica del roadmap (seccion 5.2): visual 15%, aroma 30%, sabor y boca 55%.
    Sub-puntajes van de 1 a 10 (no 0), asi que se aisla cada peso contra el
    piso valido (1) en las otras dos dimensiones en vez de contra 0."""
    puntaje = Puntaje(muestra_id="M-1", jurado_id="J-1", visual=10, aroma=1, sabor_boca=1)
    assert puntaje.puntaje_ponderado() == pytest.approx(10 * 0.15 + 1 * 0.30 + 1 * 0.55)

    puntaje = Puntaje(muestra_id="M-1", jurado_id="J-1", visual=1, aroma=10, sabor_boca=1)
    assert puntaje.puntaje_ponderado() == pytest.approx(1 * 0.15 + 10 * 0.30 + 1 * 0.55)

    puntaje = Puntaje(muestra_id="M-1", jurado_id="J-1", visual=1, aroma=1, sabor_boca=10)
    assert puntaje.puntaje_ponderado() == pytest.approx(1 * 0.15 + 1 * 0.30 + 10 * 0.55)


def test_ranking_creation():
    ranking = Ranking(categoria_id="C-1", muestra_id="M-1", puntaje_final=8.7, posicion=1)
    assert ranking.posicion == 1
    assert ranking.puntaje_final == pytest.approx(8.7)
