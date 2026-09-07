"""
Perfiles de la familia Gancia/Americano. Dos métodos de formulación
coexisten (ver families/gancia/gancia_calculator.py y
families/gancia/americano_calculator.py), cada uno con su propio perfil.
"""

from config.settings import load_settings
from core.perfil_familia import PerfilFamilia

_settings = load_settings()

# Base vínica (GanciaCalculator). Rango ABV leído en vivo de
# config/settings.yaml sección `gancia:`, el mismo config.gancia que usa
# GanciaCalculator, para que un ajuste de rango no se desalinee en silencio.
PERFIL_GANCIA_VINICA = PerfilFamilia(
    nombre="americano",
    abv_min=_settings.gancia.abv_min,
    abv_max=_settings.gancia.abv_max,
    abv_default=_settings.gancia.abv_objetivo_default,
    descripcion_sensorial="Dulce-amargo, vainillado, floral, vermú (base vínica)",
)

# Infusión directa (AmericanoCalculator) - la receta real confirmada. No
# tiene rango ABV objetivo configurado en ningún lado del código real (a
# diferencia de la base vínica) - queda en None explícitamente, no se
# inventa un rango.
PERFIL_AMERICANO_INFUSION = PerfilFamilia(
    nombre="americano",
    abv_min=None,
    abv_max=None,
    abv_default=None,
    descripcion_sensorial="Dulce-amargo, herbáceo (genciana/melisa), infusión directa sin vino",
)
