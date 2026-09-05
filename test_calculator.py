#!/usr/bin/env python3
"""
Test básico del módulo de cálculos.
"""

import os
import sys

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ensamblaje.calculator import FernetCalculator, BlendParams


def test_calculator():
    """Prueba el motor de cálculos"""
    print("=" * 50)
    print("🧮 TEST: Módulo de Cálculos")
    print("=" * 50)

    # Inicializar calculadora
    calc = FernetCalculator()

    # Probar cálculo base
    print("\n📊 Calculando base para 10L a 40% ABV...")
    params = BlendParams(volumen_objetivo_litros=10.0, abv_objetivo=40.0)

    alcohol, agua = calc.calcular_base_alcohol_agua(params)

    print(f"\n   Resultados:")
    print(f"   Alcohol 96%: {alcohol:.1f} ml")
    print(f"   Agua: {agua:.1f} ml")
    print(f"   Volumen total: {alcohol + agua:.1f} ml")

    # Verificar balance de alcohol puro
    alcohol_puro = alcohol * 0.96
    print(f"\n   Verificación:")
    print(f"   Alcohol puro: {alcohol_puro:.1f} ml")
    print(f"   Objetivo 40% de 10L: {10000 * 0.4:.1f} ml")

    print("\n✅ Test completado exitosamente")
    return True


if __name__ == "__main__":
    test_calculator()
