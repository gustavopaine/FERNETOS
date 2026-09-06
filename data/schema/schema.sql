
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
        
        -- Índices
        CREATE INDEX IF NOT EXISTS idx_tinturas_estado ON tinturas(estado);
        CREATE INDEX IF NOT EXISTS idx_tinturas_grupo ON tinturas(grupo_funcional);
        CREATE INDEX IF NOT EXISTS idx_registros_tintura ON registros_curva(tintura_id);
        