"""
Repositorio SQL para blends guardados (ver core/blend_models.py).
"""

import json
from datetime import datetime
from typing import List, Optional

from core.blend_models import BlendGuardado
from modules.core.db_manager import DatabaseManager


class BlendRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, blend: BlendGuardado) -> str:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO blends_guardados
            (id, familia, nombre, fecha_guardado, datos_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                blend.id,
                blend.familia,
                blend.nombre,
                blend.fecha_guardado.isoformat(),
                json.dumps(blend.datos),
            ),
        )
        return blend.id

    def get_by_id(self, blend_id: str) -> Optional[BlendGuardado]:
        row = self.db.ejecutar_una_fila(
            "SELECT * FROM blends_guardados WHERE id = ?", (blend_id,)
        )
        return self._fila_a_blend(row) if row else None

    def listar(self, familia: Optional[str] = None) -> List[BlendGuardado]:
        query = "SELECT * FROM blends_guardados WHERE 1=1"
        params = []
        if familia is not None:
            query += " AND familia = ?"
            params.append(familia)
        query += " ORDER BY fecha_guardado DESC"
        rows = self.db.ejecutar(query, tuple(params))
        return [self._fila_a_blend(r) for r in rows]

    def eliminar(self, blend_id: str) -> bool:
        return self.db.eliminar_filas("blends_guardados", "id = ?", (blend_id,)) > 0

    @staticmethod
    def _fila_a_blend(row) -> BlendGuardado:
        return BlendGuardado(
            id=row["id"],
            familia=row["familia"],
            nombre=row["nombre"],
            fecha_guardado=datetime.fromisoformat(row["fecha_guardado"]),
            datos=json.loads(row["datos_json"]),
        )
