Status: Implementado, verificado en el navegador (DB aislada), `/code-review high` aplicado (0 findings - primero en una pasada aislada sobre este slice solo, despues re-confirmado en la pasada combinada junto con Americano 4/N, ver seccion abajo).

# Fase 4 (3/N): persistir blends reales de Campari (Historial de Blends)

## Review summary

Extiende a Campari el mismo patron de persistencia de blends ya
implementado para Fernet (1/N) y Gancia (2/N): guardado explicito,
historial real, ficha tecnica retroactiva desde el historial. Sin
tabla ni repositorio nuevos - reusa `blends_guardados`/
`BlendRepository`. A diferencia de Fernet/Gancia, Campari no usa
tinturas de stock (botanicos por nombre directo) ni tiene un target
("params") separado de la composicion en si - la forma del snapshot
es mas simple, sin seccion de parametros ni tinturas a resolver.

Elementos que van mas alla de lo pedido explicitamente:
- **[added] Historial en un `st.expander`, no una tab** - mismo
  motivo y mismo costo ya documentado en la spec de Gancia (2/N):
  Ensamblaje Campari tampoco usa `st.tabs()`, restructurarlo entero
  para agregar tabs es una edicion grande e innecesaria para este
  slice.

Lo que este slice deliberadamente NO hace: Americano (slice separado
- tiene su propio concepto de "variantes experimentales" que todavia
hay que decidir como mapea a un blend guardado); unificar
`_filas_composicion_desde_snapshot_*`/`_filas_botanicos_desde_snapshot`
entre familias (misma "regla de tres" que las specs anteriores);
editar/versionar un blend ya guardado; limite de cantidad.

## Contexto

Fase 4 (1/N) y (2/N) resolvieron el mismo problema para Fernet y
Gancia. Ensamblaje Campari (agregado en Fase 3 al conectar Campari/
Americano a la UI) tampoco tenia ni guardado ni historial. El usuario
pidio extender el mismo patron ("segui con Campari igual").

## Arquitectura

Nada de schema nuevo - se reusa `blends_guardados`/`BlendRepository`
pasando `familia="campari"`.

### `core/blend_snapshot.py::snapshot_campari`

`snapshot_campari(resultado: CampariBlendResult) -> dict` - sin el
parametro `tinturas` que llevan `snapshot_fernet`/`snapshot_gancia`:
Campari no tiene tinturas de stock que resolver, los botanicos ya son
nombres directos. Serializa los botanicos via el `to_dict()` que ya
existe en `ComposicionBotanica` (core/tintura_models.py), no
reconstruye los campos a mano. Sin `params` (Campari no resuelve
contra un target - la composicion ingresada ES la receta, mismo
criterio ya documentado en `generar_ficha_tecnica_blend_campari`) ni
`version` (`CampariBlendResult` no tiene ese campo, a diferencia de
`BlendResult`/`GanciaBlendResult`). Incluye `densidad` en
`resultado_calculado` (`None` si no se registro control de calidad).

### `core/receta_reportes.py`

`_filas_composicion_desde_snapshot_campari` +
`_filas_botanicos_desde_snapshot` (nombre distinto de
`_filas_botanicos` porque opera sobre dicts ya serializados, no
`ComposicionBotanica` en vivo) + `generar_ficha_tecnica_desde_
historial_campari(blend: BlendGuardado) -> bytes`: mismo patron que
las versiones Fernet/Gancia (funcion separada de la version "en vivo").

### `app.py` (Ensamblaje Campari)

- Debajo del boton "📄 Descargar ficha técnica (PDF)" ya existente:
  `text_input` de nombre (opcional) + boton "💾 Guardar en el
  historial", mismo patron que Fernet/Gancia.
- `st.expander("📋 Historial de Blends de Campari")` al final del
  bloque (sibling del `if "ensamblaje_campari_resultado" in
  st.session_state:`, no nested): listado real, detalle via selectbox
  keyed + guardia `next(..., None)`, descarga de ficha retroactiva,
  boton eliminar con `st.rerun()` correctamente anidado.

## Decisiones tomadas por mi cuenta

- Expander en vez de tab (ver Review summary) - mismo criterio que
  Gancia (2/N).
- Mismo criterio que Fernet/Gancia en todo lo demas.

## Que NO hace (deferred)

- Americano: slice separado - su modelo de "variantes experimentales"
  necesita su propia decision de diseño antes de mapear a un blend
  guardado (no es un simple mirror de Campari).
- Unificar el layout de Ensamblaje Campari a tabs.
- Todo lo ya diferido en las specs de 1/N y 2/N que aplica igual aca.

## Verificacion

- `python -m pytest -q`: 276 passed (265 previos + 4 de
  `snapshot_campari` + 7 de `generar_ficha_tecnica_desde_historial_
  campari`/`_filas_composicion_desde_snapshot_campari`/
  `_filas_botanicos_desde_snapshot`).
- Verificacion manual en navegador (DB aislada, `streamlit run app.py`
  con cwd en un scratch dir, mtime de la DB real confirmado sin
  cambios antes/despues): blend de Campari calculado con la receta de
  referencia -> guardado con nombre "Campari Historial Test"
  (`BG-D4294803`) -> expander de Historial muestra la fila real ->
  detalle correcto (incluye botanicos de maceracion e incorporacion
  tardia) -> ficha tecnica retroactiva descargada
  (`ficha_tecnica_BG-D4294803.pdf`, 2703 bytes, `%PDF-`) ->
  eliminado, el historial vuelve al estado vacio sin loop infinito.
  Sin errores de consola ni tracebacks en ningun paso.

## Hallazgo de /code-review high

Ninguno. Se corrio dos veces: una pasada aislada apenas terminado
este slice (0 findings, verifico especificamente el manejo de
densidad=0.0 vs. None y el guard de `next(..., None)`), y una
pasada combinada junto con Americano (4/N) porque este commit termino
incluyendo ambos slices (ver nota en el commit) - la segunda pasada
re-confirmo 0 findings sobre el diff conjunto.

## Testing

- TDD para `snapshot_campari` y las funciones de
  `core/receta_reportes.py` (mismo patron que 1/N y 2/N).
- `app.py`: sin tests automatizados, verificacion manual en navegador.

## Deferred aspects
- Americano: slice separado, pendiente de decision de diseño sobre
  como mapea "variante experimental" a un blend guardado.
- Unificar el layout de Ensamblaje Campari a tabs.

## Implementation guidance
- TDD: si, para `snapshot_campari` y las funciones de
  `core/receta_reportes.py`. Sin tests para la UI de `app.py`.
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; recorrido manual en el
  navegador con DB aislada.
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo Campari en este slice - Americano queda fuera.
- Deferred aspects: ver ledger arriba.
- Build order: `snapshot_campari` (TDD) -> funciones de
  `receta_reportes.py` (TDD) -> wiring de `app.py`, verificado a mano
  al final.
- Routing: todo en el orquestador.
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
