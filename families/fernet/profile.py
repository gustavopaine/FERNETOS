"""
Perfil de Fernet. Rango ABV leído en vivo de config/settings.yaml sección
`parameters:` vía config/settings.py - el mismo config.parameters que
FernetCalculator usa, para que un ajuste de rango en settings.yaml no
pueda desalinearse en silencio de este perfil.
"""

from config.settings import load_settings
from core.perfil_familia import PerfilFamilia

_settings = load_settings()

PERFIL_FERNET = PerfilFamilia(
    nombre="fernet",
    abv_min=_settings.parameters.abv_min,
    abv_max=_settings.parameters.abv_max,
    abv_default=_settings.parameters.abv_default,
    descripcion_sensorial="Amargor profundo, mentolado, especiado",
)
