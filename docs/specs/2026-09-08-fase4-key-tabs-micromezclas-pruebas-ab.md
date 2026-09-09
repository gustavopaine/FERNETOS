Status: Implementado, verificado en el navegador (DB aislada, mtime de la DB real sin cambios).

# Fase 4 (6/N): `key=` explicito en tabs de Micromezclas y Pruebas A/B

## Review summary

Agrega `key=` explicito a los 4 `st.tabs()` que quedaron pendientes del
hallazgo de `/code-review high` sobre la Fase 4 (5/N) (ver
`2026-09-08-fase4-unificar-ensamblaje-tabs.md`, seccion "Marcado como
fuera de alcance"): Micromezclas Fernet/Gancia
(`["⚙️ Configuración", "📊 Iteraciones", "📈 Resultados"]`) y Pruebas
A/B Fernet/Gancia (`["🎯 Nueva Prueba", "📊 Resultados",
"📈 Análisis Competitivo", "📋 Historial"]`). Mismo bug, mismo fix, ya
aplicado y verificado antes para Ensamblaje: sin `key`, Streamlit
deriva el id del widget de la lista de labels, así que las dos
pantallas de cada par (Fernet/Gancia) comparten el mismo estado de
"tab seleccionado" - cambiar de tab en una y navegar a la otra abre
directo en esa misma tab en vez de resetear a la primera.

No hay elementos que vayan mas alla de lo pedido: es exactamente el
work item que quedó documentado como deferred en el slice anterior.

## Contexto

Ver `2026-09-08-fase4-unificar-ensamblaje-tabs.md` para el hallazgo
original (encontrado al verificar Ensamblaje Gancia/Campari/Americano
en el navegador). El review de ese slice detectó el mismo defecto en
Micromezclas y Pruebas A/B pero lo marcó fuera de alcance por ser
pantallas distintas. Este slice cierra ese deferred.

## Arquitectura

Cambio mecanico de una linea por `st.tabs()`: se agrega
`key="<pantalla>_tabs"` a cada llamada, sin tocar contenido ni logica
interna de las tabs. `requirements.txt` ya declaraba
`streamlit>=1.36.0` (piso subido en el slice anterior por el mismo
motivo - `st.tabs(key=...)` requiere esa version minima), asi que no
hizo falta tocarlo de nuevo.

Keys asignadas:
- `micromezclas_fernet_tabs` (linea ~2586)
- `micromezclas_gancia_tabs` (linea ~3071)
- `pruebas_ab_fernet_tabs` (linea ~3603)
- `pruebas_ab_gancia_tabs` (linea ~4170)

## Verificacion

- `python -m pytest -q`: 288 passed (sin cambios de logica, solo UI -
  mismo conteo que el slice anterior).
- Verificacion manual en navegador headless (Playwright, DB aislada -
  copia de la DB real en un directorio temporal separado, mtime de la
  DB real confirmado sin cambios antes/despues):
  - Micromezclas Fernet: cambiar a tab "📈 Resultados" -> navegar a
    Micromezclas Gancia -> abre en "⚙️ Configuración" (no en
    "📈 Resultados"). Confirmado por screenshot y `aria-selected`.
  - Pruebas A/B Fernet: cambiar a tab "📋 Historial" -> navegar a
    Pruebas A/B Gancia -> abre en "🎯 Nueva Prueba" (no en
    "📋 Historial"). Confirmado por screenshot y `aria-selected`.
  - Sin errores de consola del navegador en el flujo.

## Testing

- Sin tests automatizados nuevos (mismo criterio que el resto de la
  Fase 4: cambio puro de UI, verificacion manual en navegador contra
  DB aislada).

## Deferred aspects

Ninguno - este slice cierra el ultimo deferred conocido de la familia
de bugs de `st.tabs()` sin `key` en el archivo.

## Implementation guidance

- TDD: no aplica (cambio puro de estructura de UI, sin logica nueva).
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; verificacion en navegador
  headless (Playwright) contra DB aislada para los 2 pares de
  pantallas.
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo `key=` en los 4 `st.tabs()` pendientes.
- Routing: orquestador (cambio concentrado en `app.py`).
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
