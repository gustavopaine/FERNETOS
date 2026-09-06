Status: Approved (2026-09-05)

# Fase 2: Gancia como segundo producto (MVP)

## Review summary

Agrega Gancia como segundo producto formulable en FernetOS, con un motor de
cálculo propio basado en su receta real (vino blanco 75-80% del volumen,
fortificado con alcohol neutro hasta 15-18% ABV, azúcar 8-12% p/v, ácido
cítrico y caramelo como variables de ajuste) — no reutiliza el motor de
dilución alcohol+agua de Fernet. Reutiliza toda la infraestructura de
tinturas (modelos, base de datos, curvas de extracción) generalizando
`GrupoFuncional`/`Tintura` para ser genéricos por producto, y agrega un
calculador de blend paralelo (`GanciaCalculator`) para la base vínica.

**Agregado más allá de lo pedido literalmente:**
- **[added] Migración de columna en `tinturas`** (`ALTER TABLE ... ADD COLUMN
  producto`). Costo: bajo, una función en `db_manager.py`. Por qué: sin esto
  la base real del usuario (7 tinturas ya creadas) no puede distinguir
  fernet de gancia sin perder o recrear datos.
- **[added] `modules/ensamblaje/common.py`** con la única pieza de cálculo que
  Fernet y Gancia genuinamente comparten (alcohol puro ponderado). Costo:
  bajo, un archivo de ~15 líneas + refactor de
  `FernetCalculator.calcular_abv_blend` para usarlo. Por qué: es la respuesta
  concreta a "herencia o composición" — composición vía una función pura
  compartida, sin forzar una clase base artificial entre dos calculadoras
  cuyos parámetros no comparten forma.
- **[added] Filtro por Producto en Listado de Tinturas y Stock.** Costo:
  bajo. Por qué: sin esto, agregar los 4 grupos de Gancia al mismo
  `GrupoFuncional` mezclaría sus opciones con las de Fernet en los tres
  dropdowns existentes (`app.py:303, 431, 2423`), rompiendo la usabilidad
  actual de esas pantallas.
- **[added] `Tintura.to_dict()` incluye `producto`.** Costo: trivial.
  Consistencia con el resto de los campos serializados.

**Esto NO hace** (ver Deferred aspects): no da soporte a Gancia en
microblending (`PilotBatch`) ni en pruebas A/B (`ABTesting`) — ambos están
atados directamente a `FernetCalculator`/`BlendResult` y a referencias de
mercado de fernet; no genera manual PDF de Gancia; no agrega heurísticas de
día de corte específicas para los grupos de Gancia en `CurveAnalyzer` (queda
el fallback genérico, a pedido explícito del usuario, hasta tener datos
reales de maceración); no toca la CLI de `main.py` (sigue sirviendo solo
fernet, sin romperse).

## Contexto y decisiones de dominio (del usuario)

- Base: vino blanco, 75-80% del volumen total (no alcohol+agua puro).
- Fortificación con alcohol neutro (96° por defecto) hasta ABV objetivo
  15-18% (parametrizable).
- Azúcar: 8-12% p/v, **seca** (no almíbar) — misma aproximación de volumen
  que Fernet (~0.6ml/g), para mantener el balance de volumen simple y
  consistente entre productos.
- Ácido cítrico: variable de ajuste de acidez, input directo (g/L), sin
  modelo químico de pH (igual de descriptivo que `ph_estimado` en
  `BlendResult` de Fernet hoy).
- Color vía caramelo (E150): input directo (ml), no depende de las tinturas.
- `GrupoFuncional` genérico por producto:
  - FERNET (sin cambios): amargos_estructurales, aromatica_alta,
    especias_calidas, citricos, correctivos, experimental.
  - GANCIA (nuevo): quinados, botanicos_aromaticos, citricos_dulces,
    especiado_suave, experimental (compartido).
- Heurística de día de corte en `CurveAnalyzer.sugerir_dia_corte()`: se deja
  el fallback genérico (`return ultimo_registro.dia`) para los grupos de
  Gancia — el usuario no quiere rangos inventados sin datos reales de
  maceración propios; se ajustará cuando los tenga.

## Arquitectura y cambios

### 1. `modules/tinturas/models.py`
- Nuevo `class Producto(Enum): FERNET = "fernet"; GANCIA = "gancia"`.
- `GrupoFuncional` gana 4 miembros nuevos (`QUINADOS`,
  `BOTANICOS_AROMATICOS`, `CITRICOS_DULCES`, `ESPECIADO_SUAVE`) — los de
  Fernet no se tocan.
- Nuevo `GRUPOS_POR_PRODUCTO: Dict[Producto, List[GrupoFuncional]]`,
  `EXPERIMENTAL` presente en ambas listas.
- `Tintura` gana `producto: Producto = Producto.FERNET` (default preserva
  las 7 tinturas existentes sin migración de datos de aplicación).
- `Tintura.to_dict()` incluye `"producto": self.producto.value if
  self.producto else None`.
- `Tintura.__post_init__` llama a la nueva
  `validar_grupo_funcional_para_producto` (ver #2) junto a las validaciones
  de la Fase 1.

### 2. `utils/validators.py`
- Nueva `validar_grupo_funcional_para_producto(producto, grupo) -> None`:
  no valida si `grupo` es `None` (mismo criterio que las validaciones de
  Fase 1); lanza `ValueError` si `grupo not in GRUPOS_POR_PRODUCTO[producto]`.

### 3. `modules/core/db_manager.py`
- `_verificar_esquema()` hoy solo compara nombres de tabla. Se extiende (o
  se agrega un paso posterior en `_inicializar_bd()`) para leer `PRAGMA
  table_info(tinturas)` y, si falta la columna `producto`, ejecutar
  `ALTER TABLE tinturas ADD COLUMN producto TEXT NOT NULL DEFAULT 'fernet'`.
  Esto migra la base real del usuario (7 tinturas) sin pérdida de datos.
- Esquema embebido en `_crear_esquema_por_defecto()` y el archivo
  `data/schema/schema.sql` en disco se actualizan para incluir la columna
  `producto` en instalaciones nuevas.

### 4. `modules/tinturas/repository_sql.py`
- `guardar()`: agrega `producto` al diccionario/INSERT de la tabla
  `tinturas`.
- `get_by_id()`: lee `result["producto"]` y reconstruye
  `Producto(result["producto"])` (con `try/except ValueError` -> default
  `Producto.FERNET`, mismo patrón que `grupo_funcional`/`estado`).
- `listar()`: nuevo parámetro opcional `producto: Optional[str] = None` que
  extiende el `WHERE` existente (mismo patrón que `estado`/`grupo`).

### 5. `modules/ensamblaje/common.py` (nuevo)
```python
def alcohol_puro_total(componentes: List[Tuple[float, float]]) -> float:
    """componentes: [(volumen_ml, abv_pct), ...]. Devuelve ml de alcohol puro."""

def abv_resultante(componentes: List[Tuple[float, float]], volumen_total_ml: float) -> float:
    """0.0 si volumen_total_ml == 0, para evitar división por cero."""
```
`FernetCalculator.calcular_abv_blend` se refactoriza para construir su lista
de componentes (alcohol base a 96%, cada tintura a su `abv_objetivo` o 70%
por defecto) y delegar en `abv_resultante` — comportamiento idéntico,
verificado por los tests ya existentes de la Fase 1 (no se modifican).

### 6. `modules/ensamblaje/calculator_gancia.py` (nuevo)
Estructura paralela a `calculator.py`, sin heredar de `FernetCalculator`:
- `GanciaBlendParams`: `volumen_objetivo_litros`, `abv_objetivo=17.0`,
  `vino_pct=0.78`, `vino_abv=12.0`, `alcohol_fortificacion_abv=96.0`,
  `azucar_pct_wv=10.0`, `acido_citrico_g_l=0.0`, `caramelo_ml=0.0`.
- `ComposicionBlendGancia`: `vino_ml`, `alcohol_fortificacion_ml`,
  `tinturas: Dict[str, float]`, `agua_ml` (remanente, puede dar negativo si
  vino+tinturas ya exceden el volumen — se muestra tal cual, mismo criterio
  que Fernet: no hay validación dura, el usuario ve el número y ajusta
  `vino_pct`), `azucar_g`, `acido_citrico_g`, `caramelo_ml`;
  `volumen_total_ml` como property (suma de todo).
- `GanciaBlendResult`: espejo de `BlendResult` con estos campos.
- `GanciaCalculator.calcular_base_vino_alcohol(params, tinturas_ml_total=0.0)
  -> Tuple[float, float, float]`: `vino_ml = volumen_total * vino_pct`;
  `alcohol_fortificacion_ml` resuelve el ABV objetivo descontando lo que ya
  aporta el vino; `agua_ml` es el remanente.
- `GanciaCalculator.calcular_abv_blend(composicion, tinturas_data, vino_abv,
  alcohol_fortificacion_abv) -> float`: usa `abv_resultante` de `common.py`.
- `GanciaCalculator.calcular_azucar(azucar_pct_wv, volumen_lote_ml) ->
  float`: `(azucar_pct_wv / 100) * volumen_lote_ml` (p/v = gramos por 100ml).
- Volumen con azúcar: reutiliza la misma aproximación de Fernet
  (`+ azucar_g * 0.6`) — según lo acordado, sin modelo de almíbar.

### 7. `config/settings.py`
- Nueva `GanciaParameterRanges` (mismos campos que `GanciaBlendParams`,
  como valores por defecto configurables: `vino_pct_min/max/default`,
  `vino_abv_default`, `alcohol_fortificacion_abv_default`,
  `abv_min/max/default`, `azucar_pct_min/max/default`,
  `acido_citrico_default_g_l`, `caramelo_default_ml`).
- Campo `gancia: GanciaParameterRanges` en `FernetOSConfig`.
- `from_yaml()` ya es genérico desde la Fase 1 (itera `fields(config)`) —
  no requiere cambios para cargar la sección nueva.
- `save_settings()` NO es genérico (arma el dict a mano) — se agrega el
  bloque `"gancia": {...}` explícito, siguiendo el mismo patrón que
  `"backup"`.

### 8. `app.py` (UI)
- **Nueva Tintura**: selector "Producto" (Fernet/Gancia) antes del
  selector de Grupo; el dropdown de Grupo se filtra con
  `GRUPOS_POR_PRODUCTO[producto_elegido]`; se pasa `producto=` al
  constructor de `Tintura`.
- **Listado de Tinturas** (`app.py:303`) y **Stock** (`app.py:2423`): se
  agrega un filtro "Producto" (Todos/Fernet/Gancia) junto al filtro de
  Grupo existente, y se filtran los resultados de `repo.listar(...)` en
  consecuencia.
- **Nueva sección de menú "🍷 Ensamblaje Gancia"**, paralela a
  "🧮 Ensamblaje": formulario con volumen objetivo, ABV objetivo (15-18%),
  % vino (75-80%), ABV del vino, ABV de fortificación, % azúcar (8-12%),
  ácido cítrico (g/L), caramelo (ml), selección de tinturas **filtradas a
  `producto=gancia`**, y botón "Calcular Blend" que usa `GanciaCalculator`
  y muestra la receta resultante (mismo estilo que la sección de Fernet).

## Testing (TDD)
Mismo criterio que la Fase 1: TDD para lógica de negocio, verificación
manual para wiring de UI en `app.py`.
- `tests/test_ensamblaje_common.py`: `alcohol_puro_total`, `abv_resultante`
  (incluyendo volumen 0).
- `tests/test_calculator.py`: se agrega un test de que
  `calcular_abv_blend` sigue dando los mismos resultados tras el refactor
  (regresión del comportamiento, no un test nuevo de funcionalidad).
- `tests/test_calculator_gancia.py`: `calcular_base_vino_alcohol` con caso
  conocido (10L, 78% vino, vino 12°, objetivo 17% ABV -> valores exactos
  verificables a mano); `calcular_abv_blend` con y sin tinturas;
  `calcular_azucar` (% p/v).
- `tests/test_db_manager.py`: la migración de columna agrega `producto` a
  una BD creada con el esquema viejo (sin la columna) sin perder filas
  existentes.
- `tests/test_repository_sql.py`: guardar/recuperar una tintura Gancia
  conserva `producto`; `listar(producto="gancia")` filtra correctamente.
- `tests/test_validators.py`: grupo válido/inválido por producto.
- `tests/test_config_settings.py`: round-trip de la sección `gancia`.
- `tests/test_models.py`: `Tintura` con grupo de Gancia no lanza; con grupo
  de Fernet + `producto=GANCIA` sí lanza.

## No-goals / alternativas rechazadas
- **Heredar `GanciaCalculator` de `FernetCalculator`**: rechazado porque
  `BlendParams`/`GanciaBlendParams` no comparten forma (vino+fortificación
  vs alcohol+agua) — forzar una base común hubiera sido una abstracción
  artificial. Se usa composición vía `common.py` en su lugar.
- **Enums separados por producto** (`GrupoFuncionalFernet`/
  `GrupoFuncionalGancia`) en vez de uno solo extendido: más "puro" pero
  obliga a tipar `Tintura.grupo_funcional` como Union y a saber qué Enum
  reconstruir en `repository_sql.py` según `producto` — más invasivo para
  un beneficio marginal dado que solo hay 2 productos hoy.
- **Modelar almíbar en vez de azúcar seca**: rechazado explícitamente por
  el usuario para mantener el balance de volumen simple.
- **Inventar heurísticas de día de corte** para los grupos de Gancia:
  rechazado explícitamente por el usuario sin datos reales propios.

## Deferred aspects
- **Microblending para Gancia** (`PilotBatch`): atado directamente a
  `FernetCalculator`/`BlendResult` (`modules/microblending/pilot_batch.py:19-21,91`).
  Requiere generalizar `PilotBatch` para aceptar cualquier calculador/
  resultado, o crear un `GanciaPilotBatch` paralelo. Vuelve a estar en
  alcance cuando el usuario quiera iterar recetas de Gancia con ajustes
  finos, igual que ya hace con fernet.
- **Pruebas A/B para Gancia** (`ABTesting`): tiene referencias de mercado
  hardcodeadas a fernet (Branca, Vittone, 1882,
  `modules/microblending/ab_testing.py:350-364`). Necesitaría su propia
  lista de referencias (Cinzano, Martini, Gancia, etc.) y desacoplarse de
  `BlendResult` de fernet. Vuelve a estar en alcance junto con
  microblending.
- **Manual PDF de Gancia** (`scripts/generar_manual_pdf.py`): genera el
  manual de fernet únicamente. Se retoma si el usuario quiere documentación
  formal de Gancia antes de la competencia.
- **Heurística de día de corte por grupo de Gancia** en `CurveAnalyzer`:
  fallback genérico por ahora. Vuelve a estar en alcance cuando el usuario
  tenga datos reales de maceración de sus tinturas de Gancia.
- **CLI (`main.py`) sin soporte para Gancia**: sigue sirviendo solo fernet
  (`grupo_map` hardcodeado). No se toca porque no se pidió y no se usa
  documentadamente (ver spec de Fase 1). Se retoma si el usuario empieza a
  usar la CLI para Gancia.
- **Escalado industrial de Gancia** (`modules/ensamblaje/scaling.py`): no
  auditado ni extendido en este slice.

## Implementation guidance
- TDD: activado para `models.py` (validación), `db_manager.py` (migración),
  `repository_sql.py`, `calculator_gancia.py`, `common.py`, `validators.py`,
  `config/settings.py`. Sin TDD para el wiring de `app.py` — verificación
  manual (pytest + smoke test de la app real, mismo criterio que Fase 1).
- Isolation: checkout actual (`main`), sin worktree.
- Verify: `pytest` (suite completa, exit 0) antes de dar cualquier tarea
  por terminada; además, la suite de la Fase 1 (40 tests) debe seguir en
  verde sin cambios — es la garantía de "no romper el modelo de Fernet
  existente".
- Review: `/code-review high` sobre el diff completo de la fase, una sola
  vez, al terminar todas las tareas y con la suite en verde (mismo
  mecanismo que la Fase 1).
- Scope: construir solo lo que este spec especifica; los ítems de Deferred
  aspects se proponen, no se construyen.
- Deferred aspects: ver ledger arriba. Sin sistema de tracking externo —
  este spec es el registro canónico.
- Build order (de menor a mayor dependencia, aislando el riesgo de migrar
  datos reales primero):
  1. `modules/tinturas/models.py` (Producto, GrupoFuncional extendido,
     GRUPOS_POR_PRODUCTO, campo producto en Tintura) + `validators.py`
  2. `db_manager.py` (migración de columna) + `repository_sql.py`
     (persistir/filtrar producto) — con tests contra una copia temporal de
     la BD real para confirmar que la migración no pierde las 7 tinturas
  3. `modules/ensamblaje/common.py` + refactor de
     `FernetCalculator.calcular_abv_blend` (con la suite de Fase 1 en
     verde como guardrail)
  4. `modules/ensamblaje/calculator_gancia.py`
  5. `config/settings.py` (GanciaParameterRanges)
  6. UI en `app.py`: Nueva Tintura producto-aware, filtros de
     Listado/Stock, sección Ensamblaje Gancia
  7. `/code-review high` sobre el diff completo de la fase
- Routing: secuencial, ejecutado por el orquestador — mismo razonamiento
  que la Fase 1 (volumen chico por tarea, no ahorra tokens delegar).
- Orchestrator: modelo/effort actual de esta sesión (Opus, alto esfuerzo).
