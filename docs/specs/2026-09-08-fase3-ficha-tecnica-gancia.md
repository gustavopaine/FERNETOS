Status: Implementado, verificado en el navegador, /code-review high aplicado (2 pasadas)

# Fase 3 (4/N): ficha tecnica de Gancia + fix de un bug real en Fernet

## Que agrega

- `core/receta_reportes.py`: `_filas_composicion_gancia(resultado,
  tinturas)` y `generar_ficha_tecnica_blend_gancia(resultado,
  tinturas) -> bytes`, mismo patron que la version Fernet de (3/N)
  pero sobre `GanciaBlendResult`/`ComposicionBlendGancia` (vino +
  alcohol de fortificacion + agua en vez de alcohol base + agua; mas
  una seccion "Aditivos" para azucar/acido citrico/caramelo, que no
  son volumen de la base).
- `app.py` (Ensamblaje Gancia): boton nuevo
  "📄 Descargar ficha técnica (PDF)" - a diferencia de Fernet, Gancia
  no tenia ningun boton de guardado (ni siquiera un stub), asi que
  esto es una adicion, no un reemplazo.

## Hallazgos de /code-review high sobre (3/N) aplicados

Lanzado sobre el commit `aafca5c` (Fernet), 3 hallazgos reales:

- **Bug real: el boton de descarga se comia el panel de resultados.**
  `st.download_button` estaba anidado dentro de
  `if st.button("Calcular Blend"):`. Un click en "Descargar ficha
  técnica" dispara un rerun de todo el script; en ese rerun
  `st.button("Calcular Blend")` vuelve a evaluar `False` (los botones
  de Streamlit solo devuelven `True` en el render exacto del click),
  asi que TODO el bloque de resultados (metricas, tablas, y el propio
  boton de descarga) desaparecia de la pantalla. Fix: el `resultado`
  calculado se guarda en `st.session_state` dentro del bloque del
  boton, y todo el panel de resultados (incluido el boton de
  descarga) se movio a un bloque separado que lee de `session_state`
  - sobrevive a cualquier rerun, incluido el que dispara la propia
  descarga. Aplique el mismo patron preventivamente en Gancia al
  agregar su boton en este slice, para no reintroducir el mismo bug.
- **Bug de test: `tinturas_ml or {...}` descarta un `{}` valido**
  (`{}` es falsy en Python). Los tests de "sin tinturas" pasaban por
  la razon equivocada (el diccionario de *nombres* estaba vacio, no
  la composicion real). Fix: `tinturas_ml if tinturas_ml is not None
  else {...}` en los helpers de test, mas un test que efectivamente
  ejercita `resultado.composicion.tinturas == {}`.
- **`ZeroDivisionError` sin guardia** en `_filas_composicion_fernet`
  si `volumen_total_ml` es 0 (ej. un `BlendResult()` por defecto). La
  UI de `app.py` lo evita indirectamente (el `number_input` de volumen
  tiene `min_value=0.5`), pero la funcion es publica y reutilizable
  sin esa proteccion. Fix: guardia explicita que lanza `ValueError`
  con mensaje claro - agregada tambien a `_filas_composicion_gancia`
  por el mismo motivo, ya que se escribio con el mismo patron.

## Decisiones tomadas por mi cuenta

- Mismo criterio de scope que (3/N): PDF, sin persistencia del blend
  (sigue sin existir "Historial de Blends" real).
- El fix de "resultado en session_state" para Gancia se aplico desde
  el principio (nunca tuvo el bug, porque nunca tuvo boton de
  descarga) - se agrega directamente bien hecho en vez de agregarlo
  mal y corregirlo despues.

## Segunda pasada de /code-review high (sobre este mismo diff)

5 hallazgos, todos aplicados:

- **Bug real: `azucar_efectiva_g_l` nunca se seteaba en Gancia**
  (quedaba en el default `0.0`), asi que la ficha tecnica de Gancia
  siempre mostraba "Azúcar efectiva: 0.0 g/L" sin importar la receta
  real. Fix: `azucar_pct_gancia * 10` (de % p/v a g/L) al construir
  `GanciaBlendResult` - mismo criterio que Fernet (se ecoa el target
  dosificado, no se recalcula contra el volumen real).
- **El try/except dejo de cubrir el render + la generacion del PDF**
  al mover ese bloque fuera de `if st.button(...)` (fix del hallazgo
  anterior). Un error ahi (ej. el `ValueError` de volumen 0 agregado
  en (3/N)) tumbaba el script sin capturar, y como el `resultado`
  invalido quedaba en `session_state`, volvia a fallar en cada rerun
  siguiente. Fix: `try/except` alrededor de la generacion del PDF +
  el boton de descarga (la parte que realmente puede lanzar), que
  ademas limpia el `session_state` en el except para no repetir el
  crash.
- **Resultado en `session_state` no se invalida si el usuario cambia
  parametros sin volver a calcular** - la ficha tecnica podria
  reflejar una receta vieja mientras el formulario ya muestra otros
  valores. Decision consciente: en vez de trackear cada input para
  invalidar el cache automaticamente (mucho mas codigo), se agrego un
  `st.caption` explicito abajo del mensaje de exito indicando que hay
  que volver a calcular si se cambio algo - mitigacion proporcional
  al riesgo real, documentada, no un fix silencioso.
- **Duplicacion real entre `_filas_composicion_fernet`/`_gancia` y
  sus `generar_ficha_tecnica_blend_*`** (~65 lineas de boilerplate de
  reportlab repetidas), que ya habia causado el bug de arriba (la
  version Gancia se armo por copy-paste y se olvido un campo). Fix:
  extraido `_generar_pdf_ficha_tecnica()` compartido que arma el PDF
  a partir de listas de tuplas ya resueltas a texto; las funciones
  publicas por familia arman esas listas desde su `resultado` tipado
  y llaman al renderer comun. Los tests existentes no cambiaron (la
  API publica es identica), confirmando que el refactor no cambio
  comportamiento.
- **El PDF se reconstruia en cada rerun ajeno** de Streamlit mientras
  el resultado siguiera en `session_state` (mismo patron ya visto y
  arreglado en el modulo de Torneo). Fix:
  `_pdf_ficha_tecnica_fernet`/`_pdf_ficha_tecnica_gancia`, wrappers
  locales con `@st.cache_data`, en ambos Ensamblajes.

## Que NO hace (deferred)

- Americano/Campari: sus calculators (`AmericanoCalculator`/
  `CampariCalculator`) ni siquiera estan conectados a `app.py` todavia
  (ver memoria del proyecto) - no hay UI de Ensamblaje ahi para
  agregarle un boton.
- Persistir el blend calculado (mismo deferred que (3/N)).

## Verificacion

- `python -m pytest -q`: 225 passed (216 previos + 9 nuevos en
  `tests/test_receta_reportes.py`: 6 de Gancia, 2 de la guardia de
  volumen 0 - Fernet y Gancia -, 1 de que el bug del helper de test
  quedo corregido).
- Verificacion manual en navegador (DB aislada, no la real -
  verificado por mtime): recreado el flujo de Fernet completo y
  **confirmado que el panel de resultados ya NO desaparece** al
  clickear "Descargar ficha técnica" (el bug del hallazgo 1); blend
  de Gancia calculado con una tintura real filtrada por
  `producto=GANCIA`, descarga de su ficha tecnica
  (`ficha_tecnica_G-20260908-A83A.pdf`, 2744 bytes, `%PDF-`) y panel
  de resultados tambien persistente tras el click. Sin errores de
  consola ni tracebacks en ninguna de las dos familias.
