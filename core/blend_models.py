"""
Modelo de un blend calculado y guardado (roadmap Fase 4: reemplaza el
placeholder de "Historial de Blends" - los blends de Fernet/Gancia/
Campari/Americano no se persistian en ningun lado, ver Fase 3 (3/N)).

Un `BlendGuardado` no reemplaza `core.receta_models.Receta` (una
formulacion nombrada/versionada, sin resultado calculado): esto guarda
el resultado real de UN calculo puntual (ABV/azucar/etc. que realmente
dio, no un target), y su `datos` es de forma libre porque la
composicion difiere demasiado entre familias (Fernet/Gancia usan
tinturas de stock, Campari/Americano botanicos por nombre).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import uuid


@dataclass
class BlendGuardado:
    """Un blend calculado, guardado en el historial."""

    familia: str  # "fernet" | "gancia" | "campari" | "americano"
    datos: Dict  # forma libre, especifica de la familia - ver core/blend_snapshot.py
    nombre: Optional[str] = None
    id: str = field(default_factory=lambda: f"BG-{uuid.uuid4().hex[:8].upper()}")
    fecha_guardado: datetime = field(default_factory=datetime.now)
