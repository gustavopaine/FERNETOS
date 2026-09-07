"""
Gestor de base de datos SQLite para FernetOS.
Ubicado en modules/core/ para mantener modularidad.
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Generator


class DatabaseManager:
    """Gestor de conexiones a base de datos SQLite"""

    def __init__(
        self,
        db_path: str = "data/fernetos.db",
        schema_path: str = "data/schema/schema.sql",
    ):
        """
        Inicializa el gestor de base de datos.

        Args:
            db_path: Ruta al archivo de base de datos (dentro de data/)
            schema_path: Ruta al archivo de esquema SQL (dentro de data/schema/)
        """
        self.db_path = db_path
        self.schema_path = schema_path

        # Asegurar que existe el directorio
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)

        self._inicializar_bd()

    def _inicializar_bd(self):
        """Inicializa la base de datos con el esquema si no existe"""
        # Si no existe la BD, crearla con el esquema
        if not os.path.exists(self.db_path):
            self._crear_bd_desde_esquema()
        else:
            # Verificar que las tablas existen
            self._verificar_esquema()

        # Migraciones de columna/tabla: corren siempre, son idempotentes
        # (chequean antes de alterar/crear) y cubren tanto instalaciones
        # nuevas como una BD real creada antes de que existiera el
        # producto Gancia, la tabla compatibilidad_familias o recetas.
        self._migrar_columna_producto()
        self._migrar_tabla_compatibilidad_familias()
        self._migrar_tabla_recetas()
        self._migrar_tablas_evaluacion()

    def _migrar_columna_producto(self):
        """Agrega la columna 'producto' a tinturas si todavía no existe."""
        with self.get_connection() as conn:
            columnas = [
                row[1] for row in conn.execute("PRAGMA table_info(tinturas)").fetchall()
            ]
            if "producto" not in columnas:
                conn.execute(
                    "ALTER TABLE tinturas ADD COLUMN producto TEXT NOT NULL DEFAULT 'fernet'"
                )
                conn.commit()

    def _migrar_tabla_compatibilidad_familias(self):
        """Crea la tabla 'compatibilidad_familias' si todavía no existe."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS compatibilidad_familias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tintura_id TEXT NOT NULL,
                    familia TEXT NOT NULL,
                    dosis_min_ml_l REAL,
                    dosis_max_ml_l REAL,
                    notas TEXT,
                    UNIQUE(tintura_id, familia),
                    FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_compat_familias_tintura "
                "ON compatibilidad_familias(tintura_id)"
            )
            conn.commit()

    def _migrar_tabla_recetas(self):
        """Crea la tabla 'recetas' si todavía no existe."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recetas (
                    id TEXT PRIMARY KEY,
                    familia TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    estado TEXT NOT NULL DEFAULT 'borrador',
                    ingredientes_json TEXT NOT NULL DEFAULT '[]',
                    abv_objetivo REAL,
                    tiempo_maceracion_dias INTEGER,
                    perfil_sensorial_json TEXT DEFAULT '{}',
                    notas_batch TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_recetas_familia ON recetas(familia)"
            )
            conn.commit()

    def _migrar_tablas_evaluacion(self):
        """Crea las tablas del modulo de evaluacion/torneo si no existen."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS eventos (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    sede TEXT,
                    edicion_numero INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categorias (
                    id TEXT PRIMARY KEY,
                    evento_id TEXT NOT NULL,
                    familia TEXT NOT NULL,
                    submodalidad TEXT NOT NULL,
                    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS muestras (
                    id TEXT PRIMARY KEY,
                    categoria_id TEXT NOT NULL,
                    codigo_ciego TEXT NOT NULL,
                    receta_id_interna TEXT,
                    productor_id TEXT,
                    UNIQUE(categoria_id, codigo_ciego),
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jurados (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    peso_voto REAL NOT NULL DEFAULT 1.0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS puntajes (
                    id TEXT PRIMARY KEY,
                    muestra_id TEXT NOT NULL,
                    jurado_id TEXT NOT NULL,
                    visual REAL NOT NULL,
                    aroma REAL NOT NULL,
                    sabor_boca REAL NOT NULL,
                    comentario_libre TEXT,
                    timestamp TEXT NOT NULL,
                    UNIQUE(muestra_id, jurado_id),
                    FOREIGN KEY (muestra_id) REFERENCES muestras(id) ON DELETE CASCADE,
                    FOREIGN KEY (jurado_id) REFERENCES jurados(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rankings (
                    categoria_id TEXT NOT NULL,
                    muestra_id TEXT NOT NULL,
                    puntaje_final REAL NOT NULL,
                    posicion INTEGER NOT NULL,
                    PRIMARY KEY (categoria_id, muestra_id),
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
                    FOREIGN KEY (muestra_id) REFERENCES muestras(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_categorias_evento ON categorias(evento_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_muestras_categoria ON muestras(categoria_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_puntajes_muestra ON puntajes(muestra_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_puntajes_jurado ON puntajes(jurado_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rankings_categoria ON rankings(categoria_id)"
            )
            conn.commit()

    def _crear_bd_desde_esquema(self):
        """Crea la BD desde el archivo de esquema"""
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema = f.read()

            with self.get_connection() as conn:
                conn.executescript(schema)
                conn.commit()
            print(f"✅ Base de datos creada: {self.db_path}")
        else:
            # Esquema por defecto si no existe archivo
            self._crear_esquema_por_defecto()

    def _crear_esquema_por_defecto(self):
        """Crea esquema por defecto si no hay archivo"""
        schema = """
        -- Base de datos FernetOS - Esquema por defecto
        -- Versión 1.0
        
        CREATE TABLE IF NOT EXISTS tinturas (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            producto TEXT NOT NULL DEFAULT 'fernet',
            grupo_funcional TEXT NOT NULL,
            version TEXT DEFAULT '1.0.0',
            peso_materia_seca_g REAL NOT NULL,
            volumen_alcohol_ml REAL NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_corte_estimada TEXT,
            fecha_corte_real TEXT,
            fecha_estabilizacion_fin TEXT,
            estado TEXT DEFAULT 'en_maceracion',
            volumen_disponible_ml REAL DEFAULT 0,
            ubicacion_almacen TEXT,
            observaciones TEXT,
            ph_medido REAL,
            alcohol_medido REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS composicion_botanica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tintura_id TEXT NOT NULL,
            especie TEXT NOT NULL,
            porcentaje REAL NOT NULL,
            parte_utilizada TEXT NOT NULL,
            lote_origen TEXT,
            FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS parametros_extraccion (
            tintura_id TEXT PRIMARY KEY,
            abv_objetivo REAL NOT NULL,
            ratio_planta_alcohol REAL NOT NULL,
            temperatura_maceracion REAL DEFAULT 20,
            agitacion_diaria INTEGER DEFAULT 1,
            tiempo_estimado_dias INTEGER NOT NULL,
            proteccion_luz INTEGER DEFAULT 1,
            recipiente_material TEXT DEFAULT 'vidrio',
            FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS registros_curva (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tintura_id TEXT NOT NULL,
            dia INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            intensidad INTEGER NOT NULL,
            notas_sensoriales TEXT,
            color TEXT,
            turbidez TEXT,
            aroma_descripcion TEXT,
            momento_optimo INTEGER DEFAULT 0,
            FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS compuestos_detectados (
            registro_id INTEGER NOT NULL,
            compuesto TEXT NOT NULL,
            PRIMARY KEY (registro_id, compuesto),
            FOREIGN KEY (registro_id) REFERENCES registros_curva(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS compatibilidad_familias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tintura_id TEXT NOT NULL,
            familia TEXT NOT NULL,
            dosis_min_ml_l REAL,
            dosis_max_ml_l REAL,
            notas TEXT,
            UNIQUE(tintura_id, familia),
            FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS recetas (
            id TEXT PRIMARY KEY,
            familia TEXT NOT NULL,
            nombre TEXT NOT NULL,
            version TEXT DEFAULT '1.0.0',
            estado TEXT NOT NULL DEFAULT 'borrador',
            ingredientes_json TEXT NOT NULL DEFAULT '[]',
            abv_objetivo REAL,
            tiempo_maceracion_dias INTEGER,
            perfil_sensorial_json TEXT DEFAULT '{}',
            notas_batch TEXT,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS eventos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            fecha TEXT NOT NULL,
            sede TEXT,
            edicion_numero INTEGER
        );

        CREATE TABLE IF NOT EXISTS categorias (
            id TEXT PRIMARY KEY,
            evento_id TEXT NOT NULL,
            familia TEXT NOT NULL,
            submodalidad TEXT NOT NULL,
            FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS muestras (
            id TEXT PRIMARY KEY,
            categoria_id TEXT NOT NULL,
            codigo_ciego TEXT NOT NULL,
            receta_id_interna TEXT,
            productor_id TEXT,
            UNIQUE(categoria_id, codigo_ciego),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS jurados (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            peso_voto REAL NOT NULL DEFAULT 1.0
        );

        CREATE TABLE IF NOT EXISTS puntajes (
            id TEXT PRIMARY KEY,
            muestra_id TEXT NOT NULL,
            jurado_id TEXT NOT NULL,
            visual REAL NOT NULL,
            aroma REAL NOT NULL,
            sabor_boca REAL NOT NULL,
            comentario_libre TEXT,
            timestamp TEXT NOT NULL,
            UNIQUE(muestra_id, jurado_id),
            FOREIGN KEY (muestra_id) REFERENCES muestras(id) ON DELETE CASCADE,
            FOREIGN KEY (jurado_id) REFERENCES jurados(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS rankings (
            categoria_id TEXT NOT NULL,
            muestra_id TEXT NOT NULL,
            puntaje_final REAL NOT NULL,
            posicion INTEGER NOT NULL,
            PRIMARY KEY (categoria_id, muestra_id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
            FOREIGN KEY (muestra_id) REFERENCES muestras(id) ON DELETE CASCADE
        );

        -- Índices
        CREATE INDEX IF NOT EXISTS idx_tinturas_estado ON tinturas(estado);
        CREATE INDEX IF NOT EXISTS idx_tinturas_grupo ON tinturas(grupo_funcional);
        CREATE INDEX IF NOT EXISTS idx_registros_tintura ON registros_curva(tintura_id);
        CREATE INDEX IF NOT EXISTS idx_compat_familias_tintura ON compatibilidad_familias(tintura_id);
        CREATE INDEX IF NOT EXISTS idx_recetas_familia ON recetas(familia);
        CREATE INDEX IF NOT EXISTS idx_categorias_evento ON categorias(evento_id);
        CREATE INDEX IF NOT EXISTS idx_muestras_categoria ON muestras(categoria_id);
        CREATE INDEX IF NOT EXISTS idx_puntajes_muestra ON puntajes(muestra_id);
        CREATE INDEX IF NOT EXISTS idx_puntajes_jurado ON puntajes(jurado_id);
        CREATE INDEX IF NOT EXISTS idx_rankings_categoria ON rankings(categoria_id);
        """

        with self.get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

        # Guardar esquema para referencia futura
        os.makedirs(os.path.dirname(self.schema_path), exist_ok=True)
        with open(self.schema_path, "w", encoding="utf-8") as f:
            f.write(schema)

    def _verificar_esquema(self):
        """Verifica que las tablas necesarias existen"""
        tablas_requeridas = [
            "tinturas",
            "composicion_botanica",
            "parametros_extraccion",
            "registros_curva",
        ]

        with self.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]

        faltantes = [t for t in tablas_requeridas if t not in tablas_existentes]

        if faltantes:
            print(f"⚠️ Tablas faltantes: {faltantes}. Recreando esquema...")
            self._crear_bd_desde_esquema()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager para conexiones a base de datos.

        Yields:
            sqlite3.Connection: Conexión a la base de datos
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        conn.execute("PRAGMA foreign_keys = ON")  # SQLite no lo activa por defecto
        try:
            yield conn
        finally:
            conn.close()

    def ejecutar(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        Ejecuta una consulta SQL y retorna resultados como diccionarios.

        Args:
            query: Consulta SQL
            params: Parámetros para la consulta

        Returns:
            List[Dict]: Resultados como lista de diccionarios
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            resultados = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return resultados

    def ejecutar_una_fila(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """
        Ejecuta una consulta y retorna una sola fila.

        Returns:
            Optional[Dict]: Una fila como diccionario o None
        """
        resultados = self.ejecutar(query, params)
        return resultados[0] if resultados else None

    def insertar(self, tabla: str, datos: Dict) -> int:
        """
        Inserta un registro en una tabla.

        Args:
            tabla: Nombre de la tabla
            datos: Diccionario con columnas y valores

        Returns:
            int: ID del último registro insertado
        """
        columnas = ", ".join(datos.keys())
        placeholders = ", ".join(["?" for _ in datos])
        query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.execute(query, tuple(datos.values()))
            conn.commit()
            return cursor.lastrowid

    def actualizar(
        self, tabla: str, datos: Dict, where: str, where_params: tuple = ()
    ) -> int:
        """
        Actualiza registros en una tabla.

        Args:
            tabla: Nombre de la tabla
            datos: Diccionario con columnas y valores a actualizar
            where: Condición WHERE
            where_params: Parámetros para la condición WHERE

        Returns:
            int: Número de filas afectadas
        """
        set_clause = ", ".join([f"{k} = ?" for k in datos.keys()])
        query = f"UPDATE {tabla} SET {set_clause} WHERE {where}"

        params = tuple(datos.values()) + where_params

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def eliminar_filas(self, tabla: str, where: str, where_params: tuple = ()) -> int:
        """
        Elimina registros de una tabla.

        Args:
            tabla: Nombre de la tabla
            where: Condición WHERE
            where_params: Parámetros para la condición WHERE

        Returns:
            int: Número de filas eliminadas
        """
        query = f"DELETE FROM {tabla} WHERE {where}"

        with self.get_connection() as conn:
            cursor = conn.execute(query, where_params)
            conn.commit()
            return cursor.rowcount
