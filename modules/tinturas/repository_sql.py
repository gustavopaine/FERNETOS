"""
Repositorio SQL para tinturas.
Reemplaza la versión JSON con persistencia real.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from modules.tinturas.models import (
    Tintura,
    GrupoFuncional,
    ComposicionBotanica,
    ParametrosExtraccion,
    RegistroExtraccion,
    EstadoTintura,
    ControlCalidad,
)
from modules.core.db_manager import DatabaseManager


class TinturaSQLRepository:
    """Repositorio SQL para tinturas"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def guardar(self, tintura: Tintura) -> str:
        """
        Guarda una tintura en la base de datos.

        Args:
            tintura: Tintura a guardar

        Returns:
            str: ID de la tintura
        """
        # Insertar tintura principal
        tintura_data = {
            "id": tintura.id,
            "nombre": tintura.nombre,
            "grupo_funcional": (
                tintura.grupo_funcional.value if tintura.grupo_funcional else None
            ),
            "version": tintura.version,
            "peso_materia_seca_g": tintura.peso_total_materia_seca_g,
            "volumen_alcohol_ml": tintura.volumen_alcohol_ml,
            "fecha_inicio": (
                tintura.fecha_inicio.isoformat() if tintura.fecha_inicio else None
            ),
            "fecha_corte_estimada": (
                tintura.fecha_corte_estimada.isoformat()
                if tintura.fecha_corte_estimada
                else None
            ),
            "fecha_corte_real": (
                tintura.fecha_corte_real.isoformat()
                if tintura.fecha_corte_real
                else None
            ),
            "fecha_estabilizacion_fin": (
                tintura.fecha_estabilizacion_fin.isoformat()
                if tintura.fecha_estabilizacion_fin
                else None
            ),
            "estado": tintura.estado.value if tintura.estado else None,
            "volumen_disponible_ml": tintura.volumen_disponible_ml,
            "ubicacion_almacen": tintura.ubicacion_almacen,
            "observaciones": tintura.observaciones_iniciales,
            "ph_medido": (
                tintura.control_calidad.ph if tintura.control_calidad else None
            ),
            "alcohol_medido": (
                tintura.control_calidad.alcohol_medido
                if tintura.control_calidad
                else None
            ),
        }

        # Usar INSERT OR REPLACE para upsert
        query = """
        INSERT OR REPLACE INTO tinturas 
        (id, nombre, grupo_funcional, version, peso_materia_seca_g, volumen_alcohol_ml,
         fecha_inicio, fecha_corte_estimada, fecha_corte_real, fecha_estabilizacion_fin,
         estado, volumen_disponible_ml, ubicacion_almacen, observaciones, ph_medido, alcohol_medido)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.ejecutar(query, tuple(tintura_data.values()))

        # Guardar composición botánica
        self.db.ejecutar(
            "DELETE FROM composicion_botanica WHERE tintura_id = ?", (tintura.id,)
        )
        for comp in tintura.composicion:
            comp_data = {
                "tintura_id": tintura.id,
                "especie": comp.especie,
                "porcentaje": comp.porcentaje,
                "parte_utilizada": comp.parte_utilizada,
                "lote_origen": comp.lote_origen,
            }
            query = """
            INSERT INTO composicion_botanica 
            (tintura_id, especie, porcentaje, parte_utilizada, lote_origen)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.ejecutar(query, tuple(comp_data.values()))

        # Guardar parámetros de extracción
        if tintura.parametros:
            self.db.ejecutar(
                "DELETE FROM parametros_extraccion WHERE tintura_id = ?", (tintura.id,)
            )
            params_data = {
                "tintura_id": tintura.id,
                "abv_objetivo": tintura.parametros.abv_objetivo,
                "ratio_planta_alcohol": tintura.parametros.ratio_planta_alcohol,
                "temperatura_maceracion": tintura.parametros.temperatura_maceracion,
                "agitacion_diaria": 1 if tintura.parametros.agitacion_diaria else 0,
                "tiempo_estimado_dias": tintura.parametros.tiempo_estimado_dias,
                "proteccion_luz": 1 if tintura.parametros.proteccion_luz else 0,
                "recipiente_material": tintura.parametros.recipiente_material,
            }
            query = """
            INSERT INTO parametros_extraccion 
            (tintura_id, abv_objetivo, ratio_planta_alcohol, temperatura_maceracion,
             agitacion_diaria, tiempo_estimado_dias, proteccion_luz, recipiente_material)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.ejecutar(query, tuple(params_data.values()))

        # Guardar registros de curva
        self.db.ejecutar(
            "DELETE FROM registros_curva WHERE tintura_id = ?", (tintura.id,)
        )
        for registro in tintura.registros_extraccion:
            reg_data = {
                "tintura_id": tintura.id,
                "dia": registro.dia,
                "fecha": registro.fecha.isoformat() if registro.fecha else None,
                "intensidad": registro.intensidad_estimada,
                "notas_sensoriales": registro.notas_sensoriales,
                "color": registro.color,
                "turbidez": registro.turbidez,
                "aroma_descripcion": registro.aroma_descripcion,
                "momento_optimo": 1 if registro.momento_optimo_candidato else 0,
            }
            # insertar() ejecuta el INSERT y devuelve cursor.lastrowid dentro de la
            # misma conexión: last_insert_rowid() es por-conexión, así que pedirlo
            # en una conexión nueva (como se hacía antes) siempre daba 0.
            registro_id = self.db.insertar("registros_curva", reg_data)

            if registro_id:
                # Guardar compuestos detectados
                for compuesto in registro.compuestos_detectados:
                    self.db.ejecutar(
                        "INSERT INTO compuestos_detectados (registro_id, compuesto) VALUES (?, ?)",
                        (registro_id, compuesto),
                    )

        return tintura.id

    def get_by_id(self, tintura_id: str) -> Optional[Tintura]:
        """
        Obtiene una tintura por su ID.

        Args:
            tintura_id: ID de la tintura

        Returns:
            Optional[Tintura]: Tintura encontrada o None
        """
        # Obtener datos básicos
        query = "SELECT * FROM tinturas WHERE id = ?"
        result = self.db.ejecutar_una_fila(query, (tintura_id,))

        if not result:
            return None

        # Crear tintura con valores por defecto
        tintura = Tintura(
            nombre=result["nombre"] or "",
            peso_total_materia_seca_g=result["peso_materia_seca_g"] or 0,
            volumen_alcohol_ml=result["volumen_alcohol_ml"] or 0,
        )

        # Asignar grupo funcional
        if result["grupo_funcional"]:
            try:
                tintura.grupo_funcional = GrupoFuncional(result["grupo_funcional"])
            except ValueError:
                tintura.grupo_funcional = None

        # Asignar ID y otros campos
        tintura.id = result["id"]
        tintura.version = result["version"] or "1.0.0"

        # Fechas
        if result["fecha_inicio"]:
            try:
                tintura.fecha_inicio = datetime.fromisoformat(result["fecha_inicio"])
            except ValueError:
                tintura.fecha_inicio = None

        if result["fecha_corte_estimada"]:
            try:
                tintura.fecha_corte_estimada = datetime.fromisoformat(
                    result["fecha_corte_estimada"]
                )
            except ValueError:
                tintura.fecha_corte_estimada = None

        if result["fecha_corte_real"]:
            try:
                tintura.fecha_corte_real = datetime.fromisoformat(
                    result["fecha_corte_real"]
                )
            except ValueError:
                tintura.fecha_corte_real = None

        if result["fecha_estabilizacion_fin"]:
            try:
                tintura.fecha_estabilizacion_fin = datetime.fromisoformat(
                    result["fecha_estabilizacion_fin"]
                )
            except ValueError:
                tintura.fecha_estabilizacion_fin = None

        if result["estado"]:
            try:
                tintura.estado = EstadoTintura(result["estado"])
            except ValueError:
                tintura.estado = EstadoTintura.EN_MACERACION

        tintura.volumen_disponible_ml = result["volumen_disponible_ml"] or 0
        tintura.ubicacion_almacen = result["ubicacion_almacen"] or ""
        tintura.observaciones_iniciales = result["observaciones"] or ""

        # Control de calidad
        if result["ph_medido"] is not None or result["alcohol_medido"] is not None:
            tintura.control_calidad = ControlCalidad(
                ph=result["ph_medido"], alcohol_medido=result["alcohol_medido"]
            )

        # Cargar parámetros de extracción
        query = "SELECT * FROM parametros_extraccion WHERE tintura_id = ?"
        params_row = self.db.ejecutar_una_fila(query, (tintura_id,))

        if params_row:
            tintura.parametros = ParametrosExtraccion(
                abv_objetivo=params_row["abv_objetivo"] or 70.0,
                ratio_planta_alcohol=params_row["ratio_planta_alcohol"] or 0.2,
                temperatura_maceracion=params_row["temperatura_maceracion"] or 20.0,
                agitacion_diaria=bool(params_row["agitacion_diaria"]),
                tiempo_estimado_dias=params_row["tiempo_estimado_dias"] or 21,
                proteccion_luz=bool(params_row["proteccion_luz"]),
                recipiente_material=params_row["recipiente_material"] or "vidrio",
            )

        # Cargar composición botánica
        query = "SELECT * FROM composicion_botanica WHERE tintura_id = ?"
        comp_rows = self.db.ejecutar(query, (tintura_id,))

        for row in comp_rows:
            comp = ComposicionBotanica(
                especie=row["especie"],
                porcentaje=row["porcentaje"],
                parte_utilizada=row["parte_utilizada"],
                lote_origen=row["lote_origen"],
            )
            tintura.composicion.append(comp)

        # Cargar registros de curva
        query = """
        SELECT r.*, GROUP_CONCAT(c.compuesto) as compuestos
        FROM registros_curva r
        LEFT JOIN compuestos_detectados c ON r.id = c.registro_id
        WHERE r.tintura_id = ?
        GROUP BY r.id
        ORDER BY r.dia
        """
        reg_rows = self.db.ejecutar(query, (tintura_id,))

        for row in reg_rows:
            compuestos = row["compuestos"].split(",") if row["compuestos"] else []

            try:
                fecha_registro = (
                    datetime.fromisoformat(row["fecha"])
                    if row["fecha"]
                    else datetime.now()
                )
            except ValueError:
                fecha_registro = datetime.now()

            registro = RegistroExtraccion(
                dia=row["dia"],
                fecha=fecha_registro,
                intensidad_estimada=row["intensidad"],
                notas_sensoriales=row["notas_sensoriales"] or "",
                compuestos_detectados=compuestos,
                color=row["color"] or "",
                turbidez=row["turbidez"] or "",
                aroma_descripcion=row["aroma_descripcion"] or "",
                momento_optimo_candidato=bool(row["momento_optimo"]),
            )
            tintura.registros_extraccion.append(registro)

        return tintura

    def listar(
        self, estado: Optional[str] = None, grupo: Optional[str] = None
    ) -> List[Tintura]:
        """
        Lista tinturas con filtros opcionales.

        Args:
            estado: Filtrar por estado
            grupo: Filtrar por grupo funcional

        Returns:
            List[Tintura]: Lista de tinturas
        """
        query = "SELECT id FROM tinturas WHERE 1=1"
        params = []

        if estado:
            query += " AND estado = ?"
            params.append(estado)

        if grupo:
            query += " AND grupo_funcional = ?"
            params.append(grupo)

        rows = self.db.ejecutar(query, tuple(params))

        tinturas = []
        for row in rows:
            tintura = self.get_by_id(row["id"])
            if tintura:
                tinturas.append(tintura)

        return tinturas

    def eliminar(self, tintura_id: str) -> bool:
        """
        Elimina una tintura (borrado físico).

        Args:
            tintura_id: ID de la tintura

        Returns:
            bool: True si se eliminó
        """
        # Las foreign keys con ON DELETE CASCADE se encargan del resto
        filas_eliminadas = self.db.eliminar_filas("tinturas", "id = ?", (tintura_id,))
        return filas_eliminadas > 0
