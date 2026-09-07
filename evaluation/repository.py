"""
Repositorios SQL para las entidades de evaluacion/torneo.

Un repositorio por entidad, mismo patron que core/tintura_repository.py
y core/receta_repository.py: guardar() hace upsert (INSERT OR REPLACE),
get_by_id()/listar() reconstruyen el dataclass, eliminar() borra.
"""

from datetime import datetime
from typing import List, Optional

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
from modules.core.db_manager import DatabaseManager


class EventoRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, evento: Evento) -> str:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO eventos (id, nombre, fecha, sede, edicion_numero)
            VALUES (?, ?, ?, ?, ?)
            """,
            (evento.id, evento.nombre, evento.fecha, evento.sede, evento.edicion_numero),
        )
        return evento.id

    def get_by_id(self, evento_id: str) -> Optional[Evento]:
        row = self.db.ejecutar_una_fila("SELECT * FROM eventos WHERE id = ?", (evento_id,))
        return self._fila_a_evento(row) if row else None

    def listar(self) -> List[Evento]:
        rows = self.db.ejecutar("SELECT * FROM eventos")
        return [self._fila_a_evento(r) for r in rows]

    def eliminar(self, evento_id: str) -> bool:
        return self.db.eliminar_filas("eventos", "id = ?", (evento_id,)) > 0

    @staticmethod
    def _fila_a_evento(row) -> Evento:
        return Evento(
            id=row["id"],
            nombre=row["nombre"],
            fecha=row["fecha"],
            sede=row["sede"],
            edicion_numero=row["edicion_numero"],
        )


class CategoriaRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, categoria: Categoria) -> str:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO categorias (id, evento_id, familia, submodalidad)
            VALUES (?, ?, ?, ?)
            """,
            (categoria.id, categoria.evento_id, categoria.familia, categoria.submodalidad.value),
        )
        return categoria.id

    def get_by_id(self, categoria_id: str) -> Optional[Categoria]:
        row = self.db.ejecutar_una_fila("SELECT * FROM categorias WHERE id = ?", (categoria_id,))
        return self._fila_a_categoria(row) if row else None

    def listar(self, evento_id: Optional[str] = None) -> List[Categoria]:
        query = "SELECT * FROM categorias WHERE 1=1"
        params = []
        if evento_id is not None:
            query += " AND evento_id = ?"
            params.append(evento_id)
        rows = self.db.ejecutar(query, tuple(params))
        return [self._fila_a_categoria(r) for r in rows]

    def eliminar(self, categoria_id: str) -> bool:
        return self.db.eliminar_filas("categorias", "id = ?", (categoria_id,)) > 0

    @staticmethod
    def _fila_a_categoria(row) -> Categoria:
        return Categoria(
            id=row["id"],
            evento_id=row["evento_id"],
            familia=row["familia"],
            submodalidad=SubModalidad(row["submodalidad"]),
        )


class MuestraRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, muestra: Muestra) -> str:
        # Upsert explicito por id (no INSERT OR REPLACE): esta tabla tiene
        # un UNIQUE secundario (categoria_id, codigo_ciego) que protege el
        # anonimato de la cata. INSERT OR REPLACE resuelve CUALQUIER
        # conflicto de UNIQUE borrando la fila existente e insertando la
        # nueva - con codigo_ciego eso borraria en silencio una muestra
        # distinta que ya tenia ese codigo, exactamente el escenario de
        # colision que el modulo existe para evitar. Con ON CONFLICT(id)
        # una colision de codigo_ciego entre dos ids distintos sigue
        # lanzando IntegrityError en vez de pisar datos.
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO muestras (id, categoria_id, codigo_ciego, receta_id_interna, productor_id)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    categoria_id = excluded.categoria_id,
                    codigo_ciego = excluded.codigo_ciego,
                    receta_id_interna = excluded.receta_id_interna,
                    productor_id = excluded.productor_id
                """,
                (
                    muestra.id,
                    muestra.categoria_id,
                    muestra.codigo_ciego,
                    muestra.receta_id_interna,
                    muestra.productor_id,
                ),
            )
            conn.commit()
        return muestra.id

    def get_by_id(self, muestra_id: str) -> Optional[Muestra]:
        row = self.db.ejecutar_una_fila("SELECT * FROM muestras WHERE id = ?", (muestra_id,))
        return self._fila_a_muestra(row) if row else None

    def listar(self, categoria_id: Optional[str] = None) -> List[Muestra]:
        query = "SELECT * FROM muestras WHERE 1=1"
        params = []
        if categoria_id is not None:
            query += " AND categoria_id = ?"
            params.append(categoria_id)
        rows = self.db.ejecutar(query, tuple(params))
        return [self._fila_a_muestra(r) for r in rows]

    def eliminar(self, muestra_id: str) -> bool:
        return self.db.eliminar_filas("muestras", "id = ?", (muestra_id,)) > 0

    @staticmethod
    def _fila_a_muestra(row) -> Muestra:
        return Muestra(
            id=row["id"],
            categoria_id=row["categoria_id"],
            codigo_ciego=row["codigo_ciego"],
            receta_id_interna=row["receta_id_interna"],
            productor_id=row["productor_id"],
        )


class JuradoRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, jurado: Jurado) -> str:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO jurados (id, nombre, rol, peso_voto)
            VALUES (?, ?, ?, ?)
            """,
            (jurado.id, jurado.nombre, jurado.rol.value, jurado.peso_voto),
        )
        return jurado.id

    def get_by_id(self, jurado_id: str) -> Optional[Jurado]:
        row = self.db.ejecutar_una_fila("SELECT * FROM jurados WHERE id = ?", (jurado_id,))
        return self._fila_a_jurado(row) if row else None

    def listar(self) -> List[Jurado]:
        rows = self.db.ejecutar("SELECT * FROM jurados")
        return [self._fila_a_jurado(r) for r in rows]

    def eliminar(self, jurado_id: str) -> bool:
        return self.db.eliminar_filas("jurados", "id = ?", (jurado_id,)) > 0

    @staticmethod
    def _fila_a_jurado(row) -> Jurado:
        return Jurado(
            id=row["id"],
            nombre=row["nombre"],
            rol=RolJurado(row["rol"]),
            peso_voto=row["peso_voto"],
        )


class PuntajeRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, puntaje: Puntaje) -> str:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO puntajes
            (id, muestra_id, jurado_id, visual, aroma, sabor_boca, comentario_libre, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                puntaje.id,
                puntaje.muestra_id,
                puntaje.jurado_id,
                puntaje.visual,
                puntaje.aroma,
                puntaje.sabor_boca,
                puntaje.comentario_libre,
                puntaje.timestamp.isoformat(),
            ),
        )
        return puntaje.id

    def get_by_id(self, puntaje_id: str) -> Optional[Puntaje]:
        row = self.db.ejecutar_una_fila("SELECT * FROM puntajes WHERE id = ?", (puntaje_id,))
        return self._fila_a_puntaje(row) if row else None

    def listar(
        self, muestra_id: Optional[str] = None, jurado_id: Optional[str] = None
    ) -> List[Puntaje]:
        query = "SELECT * FROM puntajes WHERE 1=1"
        params = []
        if muestra_id is not None:
            query += " AND muestra_id = ?"
            params.append(muestra_id)
        if jurado_id is not None:
            query += " AND jurado_id = ?"
            params.append(jurado_id)
        rows = self.db.ejecutar(query, tuple(params))
        return [self._fila_a_puntaje(r) for r in rows]

    def eliminar(self, puntaje_id: str) -> bool:
        return self.db.eliminar_filas("puntajes", "id = ?", (puntaje_id,)) > 0

    @staticmethod
    def _fila_a_puntaje(row) -> Puntaje:
        return Puntaje(
            id=row["id"],
            muestra_id=row["muestra_id"],
            jurado_id=row["jurado_id"],
            visual=row["visual"],
            aroma=row["aroma"],
            sabor_boca=row["sabor_boca"],
            comentario_libre=row["comentario_libre"] or "",
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )


class RankingRepository:
    """
    Ranking no tiene id propio: su clave natural es (categoria_id,
    muestra_id), asi que guardar() siempre actualiza la posicion/puntaje
    de esa muestra en esa categoria en vez de duplicarla.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, ranking: Ranking) -> None:
        self.db.ejecutar(
            """
            INSERT OR REPLACE INTO rankings (categoria_id, muestra_id, puntaje_final, posicion)
            VALUES (?, ?, ?, ?)
            """,
            (ranking.categoria_id, ranking.muestra_id, ranking.puntaje_final, ranking.posicion),
        )

    def listar(self, categoria_id: str) -> List[Ranking]:
        rows = self.db.ejecutar(
            "SELECT * FROM rankings WHERE categoria_id = ? ORDER BY posicion ASC",
            (categoria_id,),
        )
        return [
            Ranking(
                categoria_id=r["categoria_id"],
                muestra_id=r["muestra_id"],
                puntaje_final=r["puntaje_final"],
                posicion=r["posicion"],
            )
            for r in rows
        ]

    def eliminar(self, categoria_id: str, muestra_id: str) -> bool:
        return (
            self.db.eliminar_filas(
                "rankings", "categoria_id = ? AND muestra_id = ?", (categoria_id, muestra_id)
            )
            > 0
        )
