"""
Perfil de Campari. Rango ABV objetivo pendiente de confirmar - no está
definido en config/settings.yaml ni en
families/campari/campari_calculator.py (que solo tiene alcohol_abv, la
graduación del alcohol de entrada, no un rango objetivo del blend final).
"""

from core.perfil_familia import PerfilFamilia

PERFIL_CAMPARI = PerfilFamilia(
    nombre="campari",
    abv_min=None,
    abv_max=None,
    abv_default=None,
    descripcion_sensorial=(
        "Amargo-cítrico, rojo intenso (pendiente de confirmar rango ABV "
        "objetivo - no está en config/settings.yaml ni en campari_calculator.py)"
    ),
)
