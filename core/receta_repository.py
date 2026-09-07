"""
Repositorio SQL para recetas.
"""

from typing import List, Optional
import json

from core.receta_models import EstadoReceta, IngredienteReceta, Receta
from modules.core.db_manager import DatabaseManager


class RecetaRepository:
    """Repositorio SQL para recetas"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, receta: Receta) -> str:
        """
        Guarda una receta en la base de datos.

        Args:
            receta: Receta a guardar

        Returns:
            str: ID de la receta
        """
        receta_data = {
            "id": receta.id,
            "familia": receta.familia,
            "nombre": receta.nombre,
            "version": receta.version,
            "estado": receta.estado.value,
            "ingredientes_json": json.dumps([i.to_dict() for i in receta.ingredientes]),
            "abv_objetivo": receta.abv_objetivo,
            "tiempo_maceracion_dias": receta.tiempo_maceracion_dias,
            "perfil_sensorial_json": json.dumps(receta.perfil_sensorial_objetivo),
            "notas_batch": receta.notas_batch,
            "fecha_creacion": (
                receta.fecha_creacion.isoformat() if receta.fecha_creacion else None
            ),
        }

        query = """
        INSERT OR REPLACE INTO recetas
        (id, familia, nombre, version, estado, ingredientes_json, abv_objetivo,
         tiempo_maceracion_dias, perfil_sensorial_json, notas_batch, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.ejecutar(query, tuple(receta_data.values()))

        return receta.id

    def get_by_id(self, receta_id: str) -> Optional[Receta]:
        """
        Obtiene una receta por su ID.

        Args:
            receta_id: ID de la receta

        Returns:
            Optional[Receta]: Receta encontrada o None
        """
        query = "SELECT * FROM recetas WHERE id = ?"
        result = self.db.ejecutar_una_fila(query, (receta_id,))

        if not result:
            return None

        return self._fila_a_receta(result)

    def listar(
        self,
        familia: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> List[Receta]:
        """
        Lista recetas con filtros opcionales.

        Args:
            familia: Filtrar por familia ("fernet"/"americano"/"campari")
            estado: Filtrar por estado

        Returns:
            List[Receta]: Lista de recetas
        """
        query = "SELECT * FROM recetas WHERE 1=1"
        params = []

        if familia:
            query += " AND familia = ?"
            params.append(familia)

        if estado:
            query += " AND estado = ?"
            params.append(estado)

        rows = self.db.ejecutar(query, tuple(params))

        return [self._fila_a_receta(row) for row in rows]

    def eliminar(self, receta_id: str) -> bool:
        """
        Elimina una receta (borrado físico).

        Args:
            receta_id: ID de la receta

        Returns:
            bool: True si se eliminó
        """
        filas_eliminadas = self.db.eliminar_filas("recetas", "id = ?", (receta_id,))
        return filas_eliminadas > 0

    def _fila_a_receta(self, row) -> Receta:
        """Reconstruye una Receta desde una fila de la tabla `recetas`."""
        ingredientes_data = json.loads(row["ingredientes_json"] or "[]")
        perfil_sensorial = json.loads(row["perfil_sensorial_json"] or "{}")

        receta = Receta(
            id=row["id"],
            familia=row["familia"],
            nombre=row["nombre"] or "",
            version=row["version"] or "1.0.0",
            estado=EstadoReceta(row["estado"]),
            ingredientes=[IngredienteReceta.from_dict(d) for d in ingredientes_data],
            abv_objetivo=row["abv_objetivo"],
            tiempo_maceracion_dias=row["tiempo_maceracion_dias"],
            perfil_sensorial_objetivo=perfil_sensorial,
            notas_batch=row["notas_batch"] or "",
        )

        if row["fecha_creacion"]:
            from datetime import datetime

            try:
                receta.fecha_creacion = datetime.fromisoformat(row["fecha_creacion"])
            except ValueError:
                pass

        return receta
