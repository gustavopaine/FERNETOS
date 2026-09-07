
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
