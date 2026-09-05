#!/usr/bin/env python3
"""
Test básico del módulo de tinturas.
"""

import os
import sys
import tempfile

# Asegurar que Python encuentra los módulos desde la raíz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tinturas.models import (
    Tintura,
    GrupoFuncional,
    ComposicionBotanica,
    ParametrosExtraccion,
)
from modules.tinturas.repository import TinturaRepository


def test_tinturas():
    """Prueba creación y persistencia de tinturas"""
    print("=" * 50)
    print("🧪 TEST: Módulo de Tinturas")
    print("=" * 50)

    # Crear repositorio temporal
    temp_dir = tempfile.mkdtemp()
    print(f"\n📁 Directorio temporal: {temp_dir}")

    repo = TinturaRepository(data_dir=temp_dir)

    # Crear tintura de prueba
    print("\n🔬 Creando tintura de prueba...")

    t = Tintura(
        nombre="Test Genciana",
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
        composicion=[
            ComposicionBotanica(
                especie="genciana",
                porcentaje=100,
                parte_utilizada="raiz",
                lote_origen="LOTE-2025-001",
            )
        ],
        peso_total_materia_seca_g=100,
        volumen_alcohol_ml=500,
        parametros=ParametrosExtraccion(
            abv_objetivo=70.0, ratio_planta_alcohol=0.2, tiempo_estimado_dias=18
        ),
    )

    # Guardar
    id_guardado = repo.guardar(t)
    print(f"✅ Tintura guardada con ID: {id_guardado}")

    # Recuperar
    t_recuperada = repo.get_by_id(t.id)
    print(f"✅ Tintura recuperada: {t_recuperada.nombre if t_recuperada else 'None'}")

    # Verificar
    if t_recuperada:
        print(f"\n📊 Datos recuperados:")
        print(f"   ID: {t_recuperada.id}")
        print(f"   Nombre: {t_recuperada.nombre}")
        print(f"   Grupo: {t_recuperada.grupo_funcional.value}")
        print(f"   ABV: {t_recuperada.parametros.abv_objetivo}%")
        print(f"   Ratio: 1:{1/t_recuperada.parametros.ratio_planta_alcohol:.0f}")
        print(f"   Composición: {len(t_recuperada.composicion)} especies")

    print("\n✅ Test completado exitosamente")
    return True


if __name__ == "__main__":
    test_tinturas()
