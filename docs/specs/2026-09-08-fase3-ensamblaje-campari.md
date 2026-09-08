Status: Implementado, verificado en el navegador, /code-review high aplicado (2 hallazgos - ver docs/specs/2026-09-08-fase3-ensamblaje-americano.md)

# Fase 3 (5/N): UI de Ensamblaje Campari + fix de un hallazgo de (4/N)

## Que agrega

- `app.py`: nuevo menu "🍸 Ensamblaje Campari" (infusion directa, sin
  tinturas de stock). Formulario con **campos fijos por ingrediente**
  (no un editor de lista dinamica) precargados con la receta real de
  referencia (`docs/specs/2026-09-06-campari-cuarto-producto.md`,
  nunca conectada a UI hasta ahora): alcohol/agua/azucar, 9 botanicos
  de maceracion (ajenjo, quina, genciana, angelica, ruibarbo, chips de
  roble, naranja, pomelo, limon) e incorporacion tardia (hibiscus),
  mas densidad opcional (control de calidad, dato de densimetro).
  Calcula ABV y azucar efectiva (`CampariCalculator.calcular_blend`)
  y genera una ficha tecnica PDF descargable.
- `core/receta_reportes.py`: `generar_ficha_tecnica_blend_campari()` +
  `_filas_composicion_campari()` + `_filas_botanicos()` (helper
  compartible a futuro). Se generalizo el renderer compartido
  (`_generar_pdf_ficha_tecnica`) para que `version`/`parametros`
  sean opcionales (Campari no versiona blends ni tiene "objetivo"
  separado de la composicion en si) y para reemplazar el parametro
  fijo `aditivos` (solo usado por Gancia) por `secciones_extra`, una
  lista de (encabezado, filas) arbitraria - Campari la usa para
  "Botánicos (maceración)" e "Incorporación tardía" como bloques
  separados.

## Por que no es una copia de Fernet/Gancia

Investigado antes de implementar (ver memoria del proyecto): Campari
es infusion directa de lote fijo (alcohol + agua + botanicos en un
solo batch), no un blend de tinturas de stock escalado a un volumen
objetivo. No hay paso de "elegir tinturas del inventario" ni un
metodo que escale la receta - `CampariCalculator.calcular_blend()`
solo arma el resultado a partir de una composicion ya especificada
con cantidades absolutas. Por eso el formulario es de campos fijos
(los 9 ingredientes de la receta real, editables) en vez de un
selector de stock.

## Hallazgo de /code-review high sobre (4/N) aplicado

- **El fix del bug de (4/N) en Fernet quedo un nivel de indentacion
  corto**: el panel de resultados (con el `resultado` en
  `session_state`) seguia anidado dentro de `if
  tinturas_seleccionadas:`. Si el usuario calculaba un blend y despues
  vaciaba la seleccion de tinturas (ej. poniendo el ml de vuelta en 0),
  el panel entero desaparecia otra vez - mismo bug, un nivel mas
  arriba. Fix: el bloque `if "ensamblaje_fernet_resultado" in
  st.session_state:` se movio a nivel de la tab (sibling de `if
  tinturas_seleccionadas:`/`else:`), igual que ya estaba correctamente
  Gancia (el review lo uso como referencia de como SI debia quedar).

## Decisiones tomadas por mi cuenta

- Sin editor de lista dinamica de botanicos: son 9 ingredientes
  conocidos y fijos de una receta real, no un banco abierto - un
  campo numerico por ingrediente (con `min_value=0.0` para poder
  "sacarlo" poniendolo en 0, mismo criterio que "ml > 0" en
  Fernet/Gancia) es mas simple y mas fiel a lo que el producto
  realmente es.
- Cascaras (naranja/pomelo/limon) se etiquetan "(unidad)" en vez de
  "(g)" - la receta real las cuenta como "1 unidad" entera, no peso
  (ver `ComposicionBotanica.gramos` docstring y
  `tests/test_calculator_campari.py`).
- `CampariBlendResult` no tiene `id` ni `version` (a diferencia de
  Fernet/Gancia) - el nombre de archivo de la ficha usa un timestamp
  (`ficha_tecnica_campari_{YYYYMMDD_HHMMSS}.pdf`) en vez de un id de
  blend, y la ficha misma omite la seccion "Parámetros objetivo"
  (no aplica: la composicion ingresada ES la receta, no un target).
- `parte_utilizada` de cada botanico no es editable en la UI (esta
  fijo por ingrediente, ej. ajenjo siempre "hoja") - es intrinseco a
  la identidad del ingrediente, no algo que varie independientemente
  en esta receta.

## Que NO hace (deferred)

- Americano: sigue pendiente (mas complejo, tiene sistema de
  variantes experimentales).
- Logica de timing para la incorporacion tardia del hibiscus (sigue
  siendo, como ya documentaba la spec original de Campari, una lista
  aparte sin automatizar "agregar el dia 35").
- Persistir el blend calculado (mismo deferred que Fernet/Gancia).

## Verificacion

- `python -m pytest -q`: 230 passed (225 previos + 5 de
  `_filas_composicion_campari`/`generar_ficha_tecnica_blend_campari`).
- Verificacion manual en navegador (DB aislada, no la real -
  verificado por mtime): (1) confirmado el fix del hallazgo de (4/N)
  en Fernet - calcule un blend, vacie la seleccion de tinturas a 0 ml,
  el panel de resultados y el boton de descarga siguieron visibles
  (antes del fix, desaparecian). (2) Ensamblaje Campari: formulario
  precargado con la receta real, calculo con los valores por defecto
  dio **ABV 26.67% y azucar efectiva 150 g/L, exactamente los valores
  esperados** de `tests/test_calculator_campari.py`; activado el
  checkbox de densidad, recalculado, "Densidad registrada: 1060"
  mostrado correctamente; ficha tecnica PDF descargada
  (`ficha_tecnica_campari_20260908_101410.pdf`, 2675 bytes, `%PDF-`).
  Sin errores de consola ni tracebacks en ningun paso.
