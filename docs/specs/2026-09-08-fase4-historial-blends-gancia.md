Status: Implementado, verificado en el navegador (DB aislada), `/code-review high` aplicado (0 findings tras busqueda en 8 angulos - ver seccion abajo).

# Fase 4 (2/N): persistir blends reales de Gancia (Historial de Blends)

## Review summary

Extiende a Gancia el mismo patron de persistencia de blends ya
implementado para Fernet (Fase 4, 1/N): guardado explicito, historial
real, ficha tecnica retroactiva desde el historial. Sin tabla ni
repositorio nuevos - reusa `blends_guardados`/`BlendRepository` (ya
son genericos por diseño, discriminados por `familia`).

Elementos que van mas alla de lo pedido explicitamente:
- **[added] Historial en un `st.expander`, no una tab**, a diferencia
  de Fernet (que usa `st.tabs`). Costo: inconsistencia visual menor
  entre Ensamblaje Fernet y Ensamblaje Gancia. Motivo: el bloque de
  Ensamblaje Gancia (~300 lineas) no usa `st.tabs()` -
  restructurarlo entero para agregar tabs hubiera sido una edicion
  mecanica grande sobre codigo ya existente, el mismo tipo de cirugia
  donde aparecio el bug de indentacion de `st.rerun()` en el slice de
  Fernet (ver spec 1/N). Un expander logra el mismo objetivo (sacar el
  historial del flujo principal) sin re-indentar nada existente.

Lo que este slice deliberadamente NO hace: Campari/Americano (slices
separados, forma de composicion distinta); unificar
`_filas_composicion_desde_snapshot_fernet`/`_gancia` (misma razón que
la spec de 1/N - "regla de tres", con 4 call sites en total todavia no
justifica una abstraccion compartida); editar/versionar un blend ya
guardado; cualquier limite de cantidad.

## Contexto

Fase 4 (1/N) resolvio el mismo problema para Fernet: el "Historial de
Blends" de Gancia nunca existio como tal (Ensamblaje Gancia no tenia
ni boton de guardado ni tab/seccion de historial - es una pantalla mas
nueva que la de Fernet, agregada en Fase 3 "Conectar Americano/
Campari a la UI"). El usuario pidio extender el mismo patron
("segui con Gancia igual").

## Arquitectura

Nada de schema nuevo - `blends_guardados`/`BlendRepository` de 1/N se
reusan tal cual, pasando `familia="gancia"`.

### `core/blend_snapshot.py::snapshot_gancia`

`snapshot_gancia(resultado: GanciaBlendResult, tinturas: Dict[str, Tintura]) -> dict`:
mismo criterio que `snapshot_fernet` (tinturas resueltas a nombre, se
omite un `tintura_id` sin `Tintura` correspondiente). Incluye
azucar/acido citrico/caramelo en `composicion` (son parte de la
receta, mismo criterio que `_filas_composicion_gancia` los separa en
su propia seccion "Aditivos" en la ficha tecnica). Sin `ph_estimado`
ni `margen_error_ml` - Gancia no tiene esos conceptos.

### `core/receta_reportes.py`

`_filas_composicion_desde_snapshot_gancia(composicion: dict)` +
`generar_ficha_tecnica_desde_historial_gancia(blend: BlendGuardado) -> bytes`:
mismo patron que la version Fernet (funcion separada de la version
"en vivo", no un branch - fuentes de datos de tipo distinto). Incluye
la seccion "Aditivos" como `secciones_extra`, igual que
`generar_ficha_tecnica_blend_gancia`.

### `app.py` (Ensamblaje Gancia)

- Debajo del boton "📄 Descargar ficha técnica (PDF)" ya existente
  (dentro del bloque `if "ensamblaje_gancia_resultado" in
  st.session_state:`): un `text_input` para el nombre (opcional) +
  boton "💾 Guardar en el historial", mismo patron que Fernet.
- Despues de ese bloque (sibling, no nested - visible aunque no haya
  un calculo reciente en session_state): `st.expander("📋 Historial de
  Blends de Gancia")` con el listado real
  (`blend_repo_gancia.listar(familia="gancia")`), detalle via
  selectbox keyed + guardia `next(..., None)` (mismo hallazgo de
  review que en 1/N, aplicado preventivamente aca), descarga de ficha
  retroactiva, y boton eliminar con `st.rerun()` correctamente anidado
  dentro de su propio `if st.button(...)`.

## Decisiones tomadas por mi cuenta

- Expander en vez de tab (ver Review summary arriba) - la decision de
  UI mas visible de este slice.
- Mismo criterio que Fernet en todo lo demas (guardado explicito,
  nombre opcional, sin limite de historial).

## Que NO hace (deferred)

- Campari/Americano: mismo patron, slices separados (Campari no usa
  tinturas de stock; Americano tampoco - la forma del snapshot va a
  ser bastante distinta).
- Unificar Ensamblaje Gancia a `st.tabs()` para que quede visualmente
  consistente con Fernet - posible mejora futura, no forzada en este
  slice por el motivo ya explicado.
- Todo lo ya diferido en la spec de 1/N que aplica igual aca
  (comparar blends entre si, paginacion, edicion).

## Verificacion

- `python -m pytest -q`: 265 passed (260 previos + esta suma incluye
  ya los 8 tests de `snapshot_gancia` de un slice anterior + 5 nuevos
  de `generar_ficha_tecnica_desde_historial_gancia`/
  `_filas_composicion_desde_snapshot_gancia`).
- Verificacion manual en navegador (DB aislada, `streamlit run app.py`
  con cwd en un scratch dir, mtime de la DB real confirmado sin
  cambios antes/despues): blend de Gancia calculado (sin tinturas, ya
  que la DB aislada no tiene stock - el flujo no depende de tener
  tinturas) -> guardado con nombre "Gancia Historial Test"
  (`BG-9D4250D0`) -> expander de Historial muestra la fila real ->
  detalle correcto -> ficha tecnica retroactiva descargada
  (`ficha_tecnica_BG-9D4250D0.pdf`, 2705 bytes, `%PDF-`) -> eliminado,
  el historial vuelve al estado vacio ("Todavía no guardaste ningún
  blend...") sin loop infinito. Sin errores de consola ni tracebacks
  en ningun paso.

## Hallazgo de /code-review high

Ninguno - 0 findings tras busqueda en 8 angulos (diff, comportamiento
removido, trazado cross-file, reuso, simplificacion, eficiencia,
altitud, convenciones de CLAUDE.md). Confirmo especificamente que el
`st.rerun()` del boton "Eliminar del historial" quedo bien anidado
dentro de su `if` (el mismo tipo de bug que aparecio en el slice de
Fernet), y que el guard `next(..., None)` del selectbox de detalle se
aplico preventivamente igual que en Fernet.

## Testing

- TDD para `snapshot_gancia` (pura, sin DB) y las funciones de
  `receta_reportes.py` (mismo patron que 1/N).
- `app.py`: sin tests automatizados, verificacion manual en navegador
  (mismo criterio ya acordado).

## Deferred aspects
- Campari/Americano: un slice cada uno, mismo patron general (forma
  de composicion todavia por definir para cada uno).
- Unificar el layout de Ensamblaje Gancia a tabs (consistencia visual
  con Fernet) - vuelve a estar en alcance si se hace una pasada de UI
  general sobre esa pantalla por otro motivo.

## Implementation guidance
- TDD: si, para `snapshot_gancia` y las funciones de
  `core/receta_reportes.py`. Sin tests para la UI de `app.py`.
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; recorrido manual en el
  navegador con DB aislada (guardar, ver detalle, descargar ficha
  retroactiva, borrar).
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo Gancia en este slice - Campari/Americano quedan fuera.
- Deferred aspects: ver ledger arriba.
- Build order: `snapshot_gancia` (TDD) -> funciones de
  `receta_reportes.py` (TDD) -> wiring de `app.py` (boton guardar +
  expander de historial), verificado a mano al final.
- Routing: todo en el orquestador (cambio concentrado en `app.py`,
  requiere el contexto ya acumulado de convenciones de esta sesion).
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
