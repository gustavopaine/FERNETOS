Status: Implementado, verificado en el navegador, /code-review high aplicado. Incluye tambien la ficha tecnica retroactiva desde el historial (originalmente planeada como slice siguiente, terminó entrando en el mismo commit - ver seccion abajo).

# Fase 4 (1/N): persistir blends reales de Fernet (Historial de Blends)

## Review summary

Reemplaza el placeholder de "Historial de Blends" (datos hardcodeados
de ejemplo, descubierto durante Fase 3/3N) por persistencia real: el
usuario puede guardar un blend de Fernet ya calculado, y despues verlo
listado con sus datos reales. Primer slice de una serie (Gancia/
Campari/Americano quedan para slices siguientes, cada uno con su
propia forma de composicion).

Elementos que van mas alla de lo pedido explicitamente:
- **[added] Tabla nueva `blends_guardados`, no reuso de `core.
  receta_models.Receta`.** Costo: una tabla + repositorio nuevos en
  vez de cero. Investigado antes de proponer: `Receta` no guarda
  resultado calculado (solo `abv_objetivo`, un target, no lo que
  realmente dio la mezcla) y su `ingredientes: List[IngredienteReceta]`
  asume `tintura_id` de stock - no sirve para Campari/Americano (que
  no usan tinturas de stock). Una tabla nueva evita forzar cuatro
  formas de composicion distintas dentro de un modelo pensado para
  una sola.
- **[added] Snapshot de nombres de tintura al momento de guardar**, no
  solo sus ids. Costo: unas líneas mas al serializar. Sin esto, si una
  tintura se borra o se renombra despues, un blend guardado hace
  meses quedaria mostrando ids sueltos en vez de nombres - rompe el
  proposito mismo de un historial (trazabilidad).

Lo que este slice deliberadamente NO hace: Gancia/Campari/Americano
(slices separados); regenerar la ficha tecnica PDF desde un blend
guardado (el dato ya queda disponible para eso, pero cablear la
reconstruccion es un paso mas, ver Deferred); editar/versionar un
blend ya guardado (solo alta + lectura + borrado); cualquier limite de
cantidad de blends guardados.

## Contexto

Fase 3 (3/N) encontro que "Historial de Blends" en Ensamblaje Fernet
es un placeholder (`data_historial` con filas `B-001/B-002/B-003`
hardcodeadas) - nunca hubo persistencia real. El boton original
"💾 Guardar Receta" tambien era un stub (reemplazado en (3/N) por la
descarga de ficha tecnica, que no requeria guardar nada). El usuario
ahora pide resolver esto de raiz.

## Arquitectura

### Schema (`modules/core/db_manager.py`)

Nueva tabla, agregada tanto a `_crear_bd_desde_esquema` (instalacion
nueva) como a un nuevo `_migrar_tabla_blends_guardados` (BD existente),
mismo patron que las tablas ya existentes (`recetas`,
`compatibilidad_familias`):

```sql
CREATE TABLE IF NOT EXISTS blends_guardados (
    id TEXT PRIMARY KEY,
    familia TEXT NOT NULL,
    nombre TEXT,
    fecha_guardado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datos_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_blends_guardados_familia ON blends_guardados(familia);
```

`datos_json` guarda todo lo necesario para volver a mostrar el blend
(params, composicion con tinturas ya resueltas a nombre, resultado
calculado) - una tabla generica con un blob JSON, no una tabla por
familia, porque la forma de la composicion difiere demasiado entre
las 4 familias (mismo criterio que ya se uso para `ingredientes_json`
en `recetas`).

### `core/blend_repository.py` (nuevo)

```python
@dataclass
class BlendGuardado:
    id: str
    familia: str  # "fernet" | "gancia" | "campari" | "americano"
    nombre: Optional[str]
    fecha_guardado: datetime
    datos: dict  # forma libre, especifica de la familia

class BlendRepository:
    def guardar(self, blend: BlendGuardado) -> str: ...
    def get_by_id(self, blend_id: str) -> Optional[BlendGuardado]: ...
    def listar(self, familia: Optional[str] = None) -> List[BlendGuardado]: ...
    def eliminar(self, blend_id: str) -> bool: ...
```

### `core/receta_reportes.py` (o un modulo nuevo `core/blend_snapshot.py`)

`_snapshot_fernet(resultado: BlendResult, tinturas: Dict[str, Tintura]) -> dict`:
arma el dict que va a `datos_json` para un blend de Fernet -
composicion con tinturas ya resueltas a `{nombre, ml}` (no `tintura_id`,
por la razon de trazabilidad de arriba), params, resultado calculado.
TDD, testeado sin DB (funcion pura, igual patron que `_filas_*`).

### `app.py` (Ensamblaje Fernet)

- El boton "📄 Descargar ficha técnica (PDF)" pasa a estar acompañado
  de un boton "💾 Guardar en el historial" (explicito - guardar cada
  calculo automaticamente ensuciaria el historial con cada ajuste
  exploratorio antes de llegar a la receta final).
- Tab "📋 Historial" dentro de "🧮 Ensamblaje": reemplaza el
  `data_historial` hardcodeado por `blend_repo.listar(familia="fernet")`
  real - tabla con fecha, nombre (o id si no se puso), ABV, volumen;
  un selector para ver el detalle completo de un blend guardado
  (misma info que el panel de resultados que ya existe); boton
  eliminar.

## Decisiones tomadas por mi cuenta

- Guardado explicito (boton), no automatico - decision de disenio
  clara dado el proposito ("historial" implica curaduria, no un log
  de cada tecleo).
- `nombre` opcional en el guardado (text_input, ej. "Fernet
  competencia 2026") - si se deja vacio, se muestra el `id` en el
  listado.
- No hay limite de cantidad ni "solo el mas reciente por nombre" - un
  historial de verdad no descarta datos, es al usuario decidir si
  borra algo.

## Que NO hace (deferred)

- Gancia/Campari/Americano: mismo patron, slices separados (cada uno
  necesita su propio `_snapshot_X`).
- Regenerar la ficha tecnica PDF desde un blend guardado del
  historial: el `datos_json` ya tiene todo lo necesario, pero cablear
  "reconstruir un `BlendResult` desde el dict guardado y llamar a
  `generar_ficha_tecnica_blend_fernet`" es un paso aparte, natural
  candidato a ser el slice inmediato siguiente.
- Comparar blends entre si (side-by-side).
- Cualquier limite/paginacion en el listado (asumido: escala de un
  historial personal, no miles de filas).

## Hallazgo de /code-review high aplicado + bug propio encontrado en la verificacion

- **`next()` sin default sobre `blends_guardados_fernet`** en la tab
  de Historial: si se borraba un blend que no era el ultimo, el
  selectbox (keyed, opciones recalculadas en cada rerun) podia quedar
  con un id que ya no esta en la lista, y `next()` sin default hubiera
  lanzado `StopIteration` crudo. La version instalada de Streamlit lo
  amortigua hoy (cae a la primera opcion sola), pero `requirements.txt`
  solo fija `>=1.28.0` - no hay garantia de que esa resolucion se
  mantenga en otra version. Fix: `next(..., None)` + guardia explicita
  (`if blend_detalle is None: st.info(...)`).
- **Bug propio, encontrado al agregar la ficha retroactiva (no del
  review)**: al reordenar el bloque para agregar el boton de descarga
  entre el detalle y "Eliminar del historial", `st.rerun()` quedo
  dedentado fuera del `if st.button("🗑️ Eliminar...")` - hubiera
  ejecutado un rerun incondicional en cada render de la tab
  (potencial loop). Encontrado por lectura del diff antes de
  verificar en el navegador, no por el review (que ya habia
  terminado sobre la version anterior). Corregido antes de comitear.

## Ficha tecnica retroactiva desde el historial (roadmap Fase 4, item ya documentado como "siguiente slice natural")

- `core/receta_reportes.py`: `_filas_composicion_desde_snapshot_fernet`
  + `generar_ficha_tecnica_desde_historial_fernet(blend: BlendGuardado)`
  - misma estructura que `generar_ficha_tecnica_blend_fernet`, pero
    leyendo del dict guardado (`blend.datos`) en vez de un
    `BlendResult` en vivo. Funcion separada, no un branch: las fuentes
    de datos son de tipo distinto (dict vs. dataclass) y unificarlas
    hubiera significado ramificar cada acceso a campo. Alguna
    duplicacion con la version "en vivo" es un tradeoff deliberado -
    si aparece una tercera familia con el mismo patron, unificar via
    `snapshot_X()` como fuente unica (tanto para el PDF en vivo como
    para el guardado) pasa a valer la pena (regla de tres).
  - Sin `tinturas: Dict[str, Tintura]`: el snapshot ya tiene los
    nombres resueltos, no hace falta resolver nada de nuevo.
- `app.py`: boton "📄 Descargar ficha técnica (PDF)" en el detalle del
  historial, cacheado con `st.cache_data` (mismo patron ya establecido
  para las demas fichas tecnicas).

## Verificacion

- `python -m pytest -q`: 256 passed (239 previos + 8 de
  `BlendRepository` + 4 de `snapshot_fernet` + 5 de
  `generar_ficha_tecnica_desde_historial_fernet`).
- Verificacion manual en navegador (DB aislada, no la real - verificado
  por mtime): blend de Fernet calculado -> guardado con nombre "Fernet
  Historial Test" (`BG-38053CF0`) -> tab Historial muestra la fila
  real -> detalle correcto -> **ficha tecnica retroactiva descargada
  desde el historial** (`ficha_tecnica_BG-38053CF0.pdf`, 2542 bytes,
  `%PDF-`) -> eliminado, el historial vuelve al estado vacio sin loop
  infinito (confirmado esperando y re-chequeando el estado). Sin
  errores de consola ni tracebacks en ningun paso.

## Testing

- TDD para `_snapshot_fernet` (pura, sin DB) y `BlendRepository`
  (integracion con SQLite real, mismo patron que
  `test_evaluation_repository.py`).
- `app.py`: sin tests automatizados (mismo criterio ya acordado para
  todo el trabajo de UI de esta fase) - verificacion manual en el
  navegador contra una DB aislada.

## Deferred aspects
- Ficha tecnica retroactiva desde el historial: vuelve a estar en
  alcance como siguiente slice inmediato una vez que este ya este
  aprobado y andando.
- Gancia/Campari/Americano: un slice cada uno, mismo patron.
- Migrar el `Receta`/`RecetaRepository` existente (sigue sin uso,
  sin tocar - no es parte de este trabajo).

## Implementation guidance
- TDD: si, para `_snapshot_fernet` y `BlendRepository`. Sin tests para
  la UI de `app.py` (verificacion manual en navegador, DB aislada).
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; recorrido manual en el
  navegador (guardar un blend, verlo en el historial, ver su detalle,
  borrarlo).
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo Fernet en este slice - Gancia/Campari/Americano quedan
  fuera, proponer no construir.
- Deferred aspects: ver ledger arriba.
- Build order: schema + `BlendRepository` + `_snapshot_fernet` (con
  tests) primero, aislado de la UI; despues el boton "Guardar" y la
  tab de Historial real en `app.py`, verificados a mano en cada paso.
- Routing: todo en el orquestador (cambio concentrado en `app.py`,
  requiere el contexto ya acumulado de convenciones de esta sesion).
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
