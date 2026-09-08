Status: Implementado, verificado en el navegador (DB aislada), `/code-review high` aplicado (0 findings).

# Fase 4 (4/N): persistir blends reales de Americano (Historial de Blends)

## Review summary

Extiende a Americano el mismo patron de persistencia de blends ya
implementado para Fernet (1/N), Gancia (2/N) y Campari (3/N): guardado
explicito, historial real, ficha tecnica retroactiva desde el
historial. Sin tabla ni repositorio nuevos - reusa
`blends_guardados`/`BlendRepository`. Igual que Campari, sin tinturas
de stock ni "params" separados de la composicion - pero a diferencia
de las tres familias anteriores, `VarianteExperimental` ya trae su
propio identificador legible (`batch_id`) y notas de cata
(`referencia_comercial`), que el snapshot preserva.

Elementos que van mas alla de lo pedido explicitamente:
- **[added] Historial en un `st.expander`, no una tab** - mismo motivo
  ya documentado en las specs de Gancia (2/N) y Campari (3/N):
  Ensamblaje Americano tampoco usa `st.tabs()`.
- **[added] El listado/detalle usa `batch_id` como fallback del
  nombre** (`b.nombre or b.datos["batch_id"]`) en vez de `b.id`
  (`BG-XXXX`) como las otras tres familias. Costo: una pequeña
  inconsistencia de criterio entre familias. Motivo: `batch_id` ya es
  un identificador legible que el usuario elige al calcular
  (ej. "AMERICANO_CLAVO_v1") - usar el `BG-XXXX` generico en su lugar
  seria estrictamente peor para este caso particular.

Lo que este slice deliberadamente NO hace: unificar
`_filas_composicion_desde_snapshot_*` entre familias (misma "regla de
tres" ya aplicada); editar/versionar un blend ya guardado; limite de
cantidad; comparar variantes entre si (esto ya es parcialmente el
proposito de `referencia_comercial`, pero comparar dos variantes
guardadas entre si en la UI queda fuera).

## Contexto

Fase 4 (1/N, 2/N, 3/N) resolvieron el mismo problema para Fernet,
Gancia y Campari. Ensamblaje Americano (agregado en Fase 3) tampoco
tenia guardado ni historial real. El usuario pidio extender el mismo
patron ("segui con Americano igual").

## Arquitectura

Nada de schema nuevo - se reusa `blends_guardados`/`BlendRepository`
pasando `familia="americano"`.

### `core/blend_snapshot.py::snapshot_americano`

`snapshot_americano(variante: VarianteExperimental) -> dict` - sin
`tinturas` (mismo motivo que Campari) ni `params`. Incluye `batch_id`
y `referencia_comercial` (propios de `VarianteExperimental`, sin
equivalente en las otras tres familias). La azucar efectiva se
recalcula con `AmericanoCalculator.calcular_azucar_efectiva_gpl` (la
misma fuente unica que ya usan la ficha tecnica en vivo y la UI desde
Fase 3 6/N, evitando la duplicacion de formula que ya habia causado un
bug real en esa fase) en vez de guardar un campo que
`VarianteExperimental` no tiene.

### `core/receta_reportes.py`

`_filas_composicion_desde_snapshot_americano` +
`_filas_ingredientes_desde_snapshot_americano` +
`generar_ficha_tecnica_desde_historial_americano(blend: BlendGuardado) -> bytes`:
mismo patron que las tres familias anteriores. El titulo de la ficha
usa `blend.nombre or datos["batch_id"]` (no `blend.id`) - mismo
criterio que el listado/detalle de la UI.

### `app.py` (Ensamblaje Americano)

- Debajo del boton "📄 Descargar ficha técnica (PDF)" ya existente:
  `text_input` de nombre (opcional) + boton "💾 Guardar en el
  historial".
- `st.expander("📋 Historial de Blends de Americano")` al final del
  bloque (sibling del `if "ensamblaje_americano_variante" in
  st.session_state:`): listado real (columna extra "Batch ID"),
  detalle via selectbox keyed + guardia `next(..., None)`, descarga de
  ficha retroactiva, boton eliminar con `st.rerun()` correctamente
  anidado.

## Decisiones tomadas por mi cuenta

- Expander en vez de tab (ver Review summary) - mismo criterio que
  Gancia/Campari.
- `batch_id` como fallback de nombre en vez de `b.id` (ver Review
  summary) - unico desvio de criterio respecto a las otras familias,
  justificado por que Americano ya trae su propio identificador.

## Que NO hace (deferred)

- Unificar el layout de Ensamblaje Americano a tabs.
- Comparar variantes guardadas entre si en la UI.
- Todo lo ya diferido en las specs de 1/N, 2/N y 3/N que aplica igual
  aca.

## Verificacion

- `python -m pytest -q`: 288 passed (276 previos + 6 de
  `snapshot_americano` + 6 de `generar_ficha_tecnica_desde_historial_
  americano`/`_filas_composicion_desde_snapshot_americano`/
  `_filas_ingredientes_desde_snapshot_americano`).
- Verificacion manual en navegador (DB aislada, `streamlit run app.py`
  con cwd en un scratch dir, mtime de la DB real confirmado sin
  cambios antes/despues): variante de Americano calculada con la
  receta base -> guardada con nombre "Americano Historial Test"
  (`BG-AE4D2461`) -> expander de Historial muestra la fila real
  (con Batch ID "AMERICANO_BASE_v1") -> detalle correcto (incluye
  todos los ingredientes base) -> ficha tecnica retroactiva descargada
  (`ficha_tecnica_BG-AE4D2461.pdf`, 2555 bytes, `%PDF-`) -> eliminada,
  el historial vuelve al estado vacio sin loop infinito. Sin errores
  de consola ni tracebacks en ningun paso.

## Hallazgo de /code-review high

Ninguno. Revisado en una pasada combinada junto con Campari (3/N)
- este slice se comiteo junto con el anterior (ver nota en el
commit sobre por que) -, con trazado linea por linea del diff,
chequeo cruzado de firmas (`ComposicionAmericano.volumen_total_ml`,
`AmericanoCalculator.calcular_azucar_efectiva_gpl`), y verificacion
de round-trip de serializacion JSON vía `BlendRepository`. 0 findings.

## Testing

- TDD para `snapshot_americano` y las funciones de
  `core/receta_reportes.py` (mismo patron que las specs anteriores).
- `app.py`: sin tests automatizados, verificacion manual en navegador.

## Deferred aspects
- Unificar el layout de Ensamblaje Americano a tabs.
- Comparar variantes guardadas entre si.
- Con esto se completan las 4 familias del roadmap de Fase 4
  (Fernet/Gancia/Campari/Americano) - cualquier trabajo siguiente en
  el modulo de blends es una iteracion sobre el patron ya establecido,
  no un slice nuevo de "conectar una familia mas".

## Implementation guidance
- TDD: si, para `snapshot_americano` y las funciones de
  `core/receta_reportes.py`. Sin tests para la UI de `app.py`.
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; recorrido manual en el
  navegador con DB aislada.
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo Americano en este slice.
- Deferred aspects: ver ledger arriba.
- Build order: `snapshot_americano` (TDD) -> funciones de
  `receta_reportes.py` (TDD) -> wiring de `app.py`, verificado a mano
  al final.
- Routing: todo en el orquestador.
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
