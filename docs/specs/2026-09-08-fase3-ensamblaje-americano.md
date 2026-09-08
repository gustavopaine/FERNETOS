Status: Implementado, verificado en el navegador, pendiente /code-review high

# Fase 3 (6/N): UI de Ensamblaje Americano (variantes experimentales) + 2 hallazgos de (5/N)

## Que agrega

- `app.py`: nuevo menu "🌿 Ensamblaje Americano". A diferencia de
  Campari (receta fija con gramos exactos), Americano no tiene
  cantidades reales documentadas por botanico (`ComposicionBotanica.
  gramos` queda sin usar en este modelo, ver spec original) - solo
  trackea que ingredientes estan presentes. La UI refleja eso:
  - Batch ID (texto libre, ej. "AMERICANO_CLAVO_v1").
  - Alcohol/agua/azucar (numericos, precargados con la receta real:
    500ml alcohol 96°, 3-5L agua, 900g azucar).
  - **Ingredientes base** (9, checklist, todos tildados por defecto -
    sacar uno "define una receta distinta", segun la spec original).
  - **Variante** (4 opcionales del banco: clavo de olor, galanga,
    paico, romero - checklist, todos destildados por defecto).
  - Notas vs. referencia comercial (texto libre, opcional).
  - Calcula (`AmericanoCalculator.calcular_abv` vía
    `VarianteExperimental.__post_init__`) y genera ficha tecnica PDF.
- `core/receta_reportes.py`: `_filas_ingredientes_americano()` +
  `generar_ficha_tecnica_variante_americano()`. Sin cantidades (a
  diferencia de `_filas_botanicos` de Campari) - lista ingrediente ->
  parte utilizada, no ingrediente -> gramos, porque esa cantidad no
  existe en el modelo de Americano.

## Hallazgos de /code-review high sobre (5/N) aplicados

- **`_filas_botanicos` (Campari) mostraba "1 g" para las cascaras de
  citricos** (naranja/pomelo/limon), que la receta real cuenta como
  "1 unidad" entera - contradecia la propia decision documentada en
  el spec de (5/N). Fix: `parte_utilizada == "cascara"` ahora muestra
  "unidad" en vez de "g".
- **"Densidad registrada" en pantalla (Campari) usaba un chequeo
  truthy** (`if control_calidad and control_calidad.densidad:`) en vez
  de `is not None`, a diferencia del PDF (que si usaba `is not None`).
  Una densidad de `0.0` se guardaria y apareceria en la ficha tecnica
  pero nunca en pantalla - UI y PDF en desacuerdo sobre si hay un dato
  registrado. Fix: mismo chequeo `is not None` en ambos lados.

## Decisiones tomadas por mi cuenta

- `parte_utilizada` de cada ingrediente de Americano (ej. "corteza"
  para canela, "fruto" para anis estrellado/enebro, "flor" para clavo
  de olor) no estaba fijado por ningun test existente (el test suite
  solo usa "cascara" como default generico) - eleji valores mas
  representativos botanicamente ya que no hay ningun caso existente
  que dependa del valor exacto.
- Los 9 ingredientes base son checkboxes (presente/ausente), no
  campos de cantidad - el modelo de Americano no tiene gramos reales
  por ingrediente para pedirlos.
- Menu llamado "🌿 Ensamblaje Americano" (no "Variantes Americano")
  para mantener la convencion ya establecida ("Ensamblaje X") aunque
  funcionalmente el corazon de la pantalla es `VarianteExperimental`.

## Que NO hace (deferred)

- Persistir las variantes calculadas (mismo deferred que las demas
  familias - los blends no se guardan en ningun lado todavia).
- Pruebas A/B/triangulares contra Gancia comercial usando
  `VarianteExperimental` (la spec original ya dejaba esto abierto,
  `ABTesting` acepta `Any` pero no hay UI para armar esa prueba).
- `AmericanoCalculator.escalar_blend()` (no existe, no se construyo -
  mismo deferred de la spec original).

## Verificacion

- `python -m pytest -q`: 236 passed (230 previos + 1 de regresion de
  `_filas_botanicos` + 5 de
  `_filas_ingredientes_americano`/`generar_ficha_tecnica_variante_americano`).
- Verificacion manual en navegador (DB aislada, no la real - verificado
  por mtime): Americano con la receta base por defecto dio **ABV
  13.71%, exactamente el valor esperado** de
  `tests/test_calculator_americano.py`; agregada la variante "Clavo de
  olor" + notas comerciales, recalculado, "Variante agregada: Clavo De
  Olor (flor)" y las notas se mostraron correctamente; ficha tecnica
  PDF descargada (`ficha_tecnica_AMERICANO_CLAVO_v1.pdf`, 2825 bytes,
  `%PDF-`). Fixes de Campari confirmados: con densidad en `0`, "Densidad
  registrada: 0" ahora se muestra (antes del fix quedaba oculto por el
  chequeo truthy). Sin errores de consola ni tracebacks en ningun paso.
